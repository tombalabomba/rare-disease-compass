# Agent-Loop — universell für alle Epics

Operating-Anweisung für die **autonome** Abarbeitung von Tickets aus
`backlog/2.ready/`. Jede Iteration läuft in einer **frischen** Claude-Session.

Epic-spezifisches lebt im Frontmatter des Tickets (`epic`, `commit_type`,
`stop_after`) und in der Projekt-Übersicht `backlog/PLAN.md` (Ziele, Modul-Karte,
Abhängigkeitsgraph aller Epics).

## Trigger

- **Shell-Loop**: `bash scripts/agent-loop.sh` startet eine `claude -p`-Session pro
  Iteration. Cooldown 10 s, Logs pro Iteration in `.agent-loop-logs/`.
- **In Claude Code direkt**: `/loop Bitte arbeite eine Iteration aus backlog/AGENT-LOOP.md ab.`

## Iteration — Schritt für Schritt

### 1. Setup-Refresher
Lies in dieser Reihenfolge:
1. **diese Datei** komplett.
2. **`AGENTS.md`** (Repo-Root) — `Notes`-Sektion, erprobte Tool-Quirks.
3. **`CLAUDE.md`** (Repo-Root) — Projekt-Konventionen, gelten immer.
4. **`docs/`** — überfliegen, nur lesen was zum Ticket-Scope passt
   (`architektur.md`, `security.md`).

### 2. Nächstes Ticket finden
Tickets liegen **flach** als `backlog/2.ready/<ID>.md` (ein File pro Ticket, kein
Epic-Unterordner). Die Epic-Zugehörigkeit steht im Frontmatter (`epic:`). Suche
nach `.md`-Files mit `status: todo`.

**Auswahlregeln (in Reihenfolge):**
1. `status: todo` (nicht `in_progress`, `done`, `blocked`)
2. Alle `depends_on`-IDs liegen in `backlog/3.done/` (per ID, nicht per Pfad)
3. Bei mehreren Kandidaten: kleinste ID zuerst (`CLI-01` vor `CLI-02`)

**Kein Kandidat passt** (alles done/blocked oder Dependencies offen): exit clean,
kein Commit. Shell-Loop interpretiert das als „nichts zu tun" und stoppt.

### 3. Status auf `in_progress`
Direkt im Frontmatter. **Nicht** committen — lokales Tracking während der Iteration.

### 4. Scope ausführen
Lies `Scope`, `Files`, `Out of scope`, `Notes`.

**Vor der ersten Codezeile:** mit einem Explore-Subagent prüfen, ob etwas
Ähnliches im Repo schon existiert. Doppel-Implementierungen sind teuer.

**Implementations-Disziplin (nicht verhandelbar):**
- **Keine Stubs, keine Placeholders, keine `TODO`-Marker im Production-Code.**
- **Single source of truth.** Keine Adapter-/Wrapper-Layer, die ein Konzept doppeln.
- **Defense-in-Depth nie rausoptimieren** (App-Auth UND Firewall bleiben beide).
- **Datenschutz:** niemals echte Patientendaten/PII in Code, Test, Log oder Commit.
  Fixtures sind synthetisch. Im Zweifel defensiv blocken. (Siehe `docs/security.md`.)
- **Modul-Separation:** nur die Pfade aus `Files`. Scope erweitern = **neues Ticket**.
- **Drive-by Fix** nur ≤ 10 Zeilen UND klar verstanden, in der Commit-Message als
  zweite Zeile vermerken. Größere Fixes → neues Ticket in `backlog/1.planning/`.

### 5. Bug- & Lern-Disziplin (kontinuierlich)
- **Tool-Quirk / unerwartetes Verhalten / Befehl zweimal nötig?** → mit Datum in
  `AGENTS.md` unter `## Notes` ergänzen. Format strikt:
  `- YYYY-MM-DD · <terse, specific finding inkl. Fix>`
- **Fremder Bug bemerkt?** ≤ 30 Min und klar → jetzt mit-fixen (Drive-by-Vermerk).
  Größer → **neues Ticket** in `backlog/1.planning/`, aktuelles Ticket nicht blockieren.
- **Doku-Inkonsistenz** in `docs/` oder Epic-README? → in derselben Commit-Message
  als zweite Zeile vermerken.
- **Niemals** Status-Reports in `AGENTS.md` parken. Dort nur lessons learned.

### 6. Acceptance verifizieren
Jeden `[ ]`-Punkt explizit prüfen, inklusive der **Negativ-Checks**
(„darf nicht drin sein …"). Acceptance ist **maschinell prüfbar** gehalten
(lint, build, validate, unit-tests, config-validate). Alles ist lokal prüfbar —
es gibt keinen Server und keine Live-Checks, die menschliche Hardware bräuchten.
Echte API-Calls in Tests werden gemockt (öffentliche APIs nicht im Test hämmern).

**Acceptance-Punkt nicht erfüllbar:**
- ≤ 30 Min lösbar → lösen.
- Sonst → `status: blocked`, `## Blocker`-Section ans Ticket-Ende, **kein** Commit
  der Code-Änderungen (Status-Commit ist OK). Exit, melden.

`status: blocked` nur für **echte Blocker**: fehlende Secrets, fehlende externe
Voraussetzung (Server, Account), ungeklärte Architektur-Entscheidung,
Dependency-Ticket nicht done.

### 7. Ticket abschließen — Status + Move
Frontmatter: `status: done`. Datei verschieben mit **`git mv`** (History bleibt):

```
git mv backlog/2.ready/<ID>.md backlog/3.done/<ID>.md
```

### 8. Commit
Eine Commit pro Ticket. Prefix aus `commit_type`. Format:
```
<commit_type>: <ID> <Kurztitel aus Frontmatter `title:`>

<1–3 Zeilen: was geändert wurde + warum>
[Drive-by fix: <falls relevant>]

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
```

### 9. Stop-Gate-Check
Wenn `stop_after: true`:
1. Marker setzen: `touch backlog/.STOP_GATE`
2. Im finalen Output: Ticket-ID + Titel, was gebaut wurde, welcher **manuelle**
   Schritt jetzt ansteht (z. B. API-Key hinterlegen, Referenzdaten herunterladen),
   welches Ticket laut `depends_on` als nächstes käme.

Wenn `stop_after: false`: kein Marker. Commit reicht. Exit. Loop nimmt das nächste.

## Globale Regeln

### Niemals
- Push zu remote — nur lokale Commits, Mensch pusht nach Review.
- Force-Push, `git reset --hard`, Branch löschen.
- Echte Patientendaten/PII in Repo, Test, Log oder Commit.
- Mehrere Tickets in einem Commit.
- `depends_on` ignorieren.
- Scope eigenmächtig erweitern → stattdessen `status: blocked` + Hinweis.
- Status-Reports in `AGENTS.md`.
- Stubs/Placeholders/`TODO` im Production-Code stehenlassen.

### Immer
- `git mv` statt copy+delete.
- Commit-Footer `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`.
- Bei Failure: `status: blocked`, klare `## Blocker`-Section, exit.
- Frontmatter `epic:` und `commit_type:` respektieren.

## Schnell-Referenz: Ticket-Frontmatter
```yaml
---
id: CLI-01
title: CLI-Kern (Typer-App, httpx-Client, SQLite-History)
status: todo                  # todo | in_progress | blocked | done
depends_on: []                # IDs, optional
stop_after: false             # ob Loop nach Commit pausiert
epic: cli                     # Slug, "" = standalone
commit_type: feat(cli)        # Commit-Prefix
---
```
Vollständiges Schema: `backlog/TICKET-TEMPLATE.md`.
