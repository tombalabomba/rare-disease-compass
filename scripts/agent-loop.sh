#!/usr/bin/env bash
# Outer-shell loop for backlog/2.ready/ — single-repo variant.
#
# Spawns a fresh `claude -p` session per ticket, follows backlog/AGENT-LOOP.md.
# Scans backlog/2.ready/ recursively for tickets:
#   - epic ticket:  backlog/2.ready/<epic>/tickets/<id>.md
#   - flat ticket:  backlog/2.ready/<id>.md
# Ticket selection (status, depends_on, sort order) happens INSIDE the Claude
# session per AGENT-LOOP.md §2. The shell only checks if any `status: todo`
# ticket is left and trusts the agent's pick. One commit per iteration.
#
# Stops on: no todo ticket left · .STOP_GATE marker · no new commit (blocker)
#           · non-zero claude exit · MAX_ITERATIONS reached.
#
# Usage:
#   scripts/agent-loop.sh             # run until an exit condition
#   scripts/agent-loop.sh continue    # remove a pending .STOP_GATE, then run
#   scripts/agent-loop.sh status      # print ticket status grouped by epic
#
# Env knobs (defaults):
#   MAX_ITERATIONS=30
#   COOLDOWN_SECONDS=10
#   MAX_BUDGET_USD_PER_ITER=15
#   CLAUDE_MODEL=claude-opus-4-8
#
# Why --dangerously-skip-permissions: unattended runs must not block on prompts.
# Blast radius is bounded by AGENT-LOOP.md "Niemals" rules (no remote push) and
# the per-iteration budget cap. Only run on a machine you trust.

# Needs bash 4+ (macOS ships 3.2 — re-exec under a newer one if available).
if [ "${BASH_VERSINFO[0]:-0}" -lt 4 ] && [ -z "${AGENT_LOOP_REEXEC:-}" ]; then
  for candidate in /opt/homebrew/bin/bash /usr/local/bin/bash; do
    if [ -x "$candidate" ]; then
      AGENT_LOOP_REEXEC=1 exec "$candidate" "$0" "$@"
    fi
  done
  echo "agent-loop.sh requires bash 4+. Install via: brew install bash" >&2
  exit 1
fi

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
READY_DIR="$REPO_ROOT/backlog/2.ready"
LOG_DIR="$REPO_ROOT/.agent-loop-logs"
LOCK_FILE="/tmp/rare-case-assistant-agent-loop.lock"
MARKER="$REPO_ROOT/backlog/.STOP_GATE"

MAX_ITERATIONS="${MAX_ITERATIONS:-30}"
COOLDOWN_SECONDS="${COOLDOWN_SECONDS:-10}"
MAX_BUDGET_USD_PER_ITER="${MAX_BUDGET_USD_PER_ITER:-15}"
CLAUDE_MODEL="${CLAUDE_MODEL:-claude-opus-4-8}"

cmd="${1:-run}"

# List all ticket files in 2.ready/ (flat: one .md per ticket).
list_ticket_files() {
  find "$READY_DIR" -mindepth 1 -maxdepth 1 -type f -name '*.md' 2>/dev/null || true
}

# Read one frontmatter field from a ticket file.
fm_field() {
  awk -v key="$2" '
    /^---$/ {sep++; next}
    sep==1 && $0 ~ "^" key ":" {sub("^" key ": *", ""); gsub(/"/, ""); print; exit}
  ' "$1"
}

count_todo() {
  local count=0
  while IFS= read -r f; do
    [ -f "$f" ] || continue
    if grep -qE '^status: todo$' "$f"; then
      count=$((count + 1))
    fi
  done < <(list_ticket_files)
  echo "$count"
}

print_status() {
  echo "Tickets in backlog/2.ready/ (flach, gruppiert nach epic):"
  echo
  # Discover epic groups from the `epic:` frontmatter, in stable order of appearance.
  local epics=() seen e
  while IFS= read -r f; do
    e="$(fm_field "$f" epic)"; [ -n "$e" ] || e="(ohne)"
    case " ${epics[*]} " in *" $e "*) : ;; *) epics+=("$e") ;; esac
  done < <(list_ticket_files | sort)

  for epic in "${epics[@]}"; do
    echo "=== $epic ==="
    printf "%-8s %-14s %s\n" "ID" "Status" "Titel"
    printf "%-8s %-14s %s\n" "--------" "--------------" "----------------------------------------"
    while IFS= read -r f; do
      e="$(fm_field "$f" epic)"; [ -n "$e" ] || e="(ohne)"
      [ "$e" = "$epic" ] || continue
      printf "%-8s %-14s %s\n" "$(fm_field "$f" id)" "$(fm_field "$f" status)" "$(fm_field "$f" title)"
    done < <(list_ticket_files | sort)
    echo
  done
}

case "$cmd" in
  status) print_status; exit 0 ;;
  continue)
    if [ -f "$MARKER" ]; then
      echo "[loop] Removing stop-gate marker: $MARKER"; rm "$MARKER"
    else
      echo "[loop] No stop-gate marker present (nothing to remove)."
    fi
    ;;
  run|"") : ;;
  *) echo "Unknown subcommand: $cmd"; echo "Usage: $0 [run|continue|status]"; exit 2 ;;
esac

# Single loop at a time.
exec 200>"$LOCK_FILE"
if ! flock -n 200; then
  echo "[loop] Another loop is already running (lock: $LOCK_FILE). Exiting."
  exit 1
fi

if ! command -v claude >/dev/null 2>&1; then
  echo "[loop] claude CLI not on PATH. Aborting."; exit 3
fi

mkdir -p "$LOG_DIR"
cd "$REPO_ROOT"

if ! git diff --quiet || ! git diff --cached --quiet; then
  echo "[loop] Working tree is not clean. Commit, stash, or revert before running the loop."
  git status --short; exit 4
fi

current_branch=$(git rev-parse --abbrev-ref HEAD)
echo "[loop] Running on branch: $current_branch"

PROMPT='Read backlog/AGENT-LOOP.md and execute exactly ONE iteration of the loop as described there. Pick the next eligible ticket from backlog/2.ready/ (epic or flat, per AGENT-LOOP.md §2), run its scope, verify all acceptance criteria, commit, and exit. Do not pick a second ticket. If the ticket has stop_after:true and you finished it successfully, touch backlog/.STOP_GATE before exiting. If no eligible ticket exists or you hit a blocker that cannot be resolved in this run, exit cleanly without committing. Do not push to remote.'

iter=0
while [ "$iter" -lt "$MAX_ITERATIONS" ]; do
  iter=$((iter + 1))

  if [ -f "$MARKER" ]; then
    echo "[loop] Stop-gate marker present: $MARKER"
    echo "[loop] Verify the last commit and tickets, then: bash scripts/agent-loop.sh continue"
    break
  fi

  todo_count=$(count_todo)
  if [ "$todo_count" -eq 0 ]; then
    echo "[loop] No 'status: todo' tickets left in $READY_DIR. Nothing to do."
    break
  fi

  log_file="$LOG_DIR/iter-$(printf '%03d' "$iter")-$(date +%Y%m%d-%H%M%S).log"
  echo "[loop] Iteration $iter (todo count: $todo_count) — log: $log_file"

  before=$(git rev-parse HEAD)

  set +e
  claude -p "$PROMPT" \
    --dangerously-skip-permissions \
    --max-budget-usd "$MAX_BUDGET_USD_PER_ITER" \
    --model "$CLAUDE_MODEL" \
    > "$log_file" 2>&1
  rc=$?
  set -e

  if [ "$rc" -ne 0 ]; then
    echo "[loop] claude exited with code $rc. Stopping. Inspect: $log_file"; break
  fi

  after=$(git rev-parse HEAD)
  if [ "$before" = "$after" ]; then
    echo "[loop] No new commit was made. Likely a blocker or no eligible ticket. Inspect: $log_file"; break
  fi

  echo "[loop] Iteration $iter committed: $(git log --oneline -1)"

  if [ "$iter" -lt "$MAX_ITERATIONS" ]; then
    sleep "$COOLDOWN_SECONDS"
  fi
done

echo "[loop] Exited after $iter iteration(s)."
