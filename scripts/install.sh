#!/usr/bin/env bash
set -euo pipefail
#
# install.sh — Installer für die RareDiseaseCompass-CLIs (SET-02)
#
# Installiert das `cli/`-Paket (Entry-Point `rdc`) auf der lokalen Maschine und
# legt eine BEISPIEL-Konfig für optionale API-Keys im User-Konfig-Verzeichnis an.
# Idempotent: mehrfaches Ausführen macht nichts kaputt.
#
# Bewusst lokal: kein Server, kein Deployment. Echte API-Keys gehören NIE ins
# Repo — das Skript schreibt nur eine `.example`-Vorlage mit Platzhaltern.
#
# Aufruf:
#   bash scripts/install.sh
#
# Details: docs/install.md

# Mindest-Python-Version laut Stack-Vorgabe (CLAUDE.md): Python 3.11.
readonly MIN_PYTHON="3.11"

# Pfade relativ zum Skript ermitteln, damit der Installer unabhängig vom CWD
# läuft (Agent-Loop und Nutzer rufen aus unterschiedlichen Verzeichnissen auf).
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly SCRIPT_DIR
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
readonly REPO_ROOT
readonly CLI_DIR="${REPO_ROOT}/cli"

# Ausgabe-Helfer ----------------------------------------------------------------

info() {
  printf '%s\n' "$*"
}

err() {
  printf 'Fehler: %s\n' "$*" >&2
}

# Python-Version prüfen ---------------------------------------------------------

# require_python — stellt sicher, dass `python3` vorhanden und mindestens
# ${MIN_PYTHON} ist. Sonst klare deutsche Meldung und Exit ≠ 0.
require_python() {
  if ! command -v python3 >/dev/null 2>&1; then
    err "python3 wurde nicht gefunden. Bitte Python ${MIN_PYTHON} oder neuer installieren."
    exit 1
  fi

  local major minor
  major="${MIN_PYTHON%%.*}"
  minor="${MIN_PYTHON#*.}"

  if ! python3 -c "import sys; sys.exit(0 if sys.version_info >= (${major}, ${minor}) else 1)"; then
    local have
    have="$(python3 -c 'import sys; print("%d.%d" % sys.version_info[:2])')"
    err "Python ${MIN_PYTHON} oder neuer wird benötigt, gefunden wurde ${have}."
    err "Bitte ein aktuelles Python installieren und erneut ausführen."
    exit 1
  fi

  info "Python-Version ok (≥ ${MIN_PYTHON})."
}

# Installation ------------------------------------------------------------------

# install_cli — installiert das `cli/`-Paket. Bevorzugt `pipx` (isolierte
# CLI-Installation), fällt sonst auf `pip --user` zurück.
install_cli() {
  if [[ ! -f "${CLI_DIR}/pyproject.toml" ]]; then
    err "CLI-Paket nicht gefunden unter '${CLI_DIR}'. Wurde das Repo vollständig geklont?"
    exit 1
  fi

  if command -v pipx >/dev/null 2>&1; then
    info "Installiere das rdc-Paket mit pipx aus '${CLI_DIR}' …"
    pipx install "${CLI_DIR}"
  else
    info "pipx nicht gefunden — nutze 'pip --user' als Fallback."
    info "(Tipp: 'pipx' bietet eine sauberere, isolierte Installation.)"
    python3 -m pip install --user "${CLI_DIR}"
  fi
}

# Beispiel-Konfig ---------------------------------------------------------------

# config_dir — User-Konfig-Verzeichnis nach XDG-Konvention.
config_dir() {
  printf '%s/rdc' "${XDG_CONFIG_HOME:-${HOME}/.config}"
}

# write_example_config — legt eine BEISPIEL-Konfig mit Platzhaltern an, falls
# noch nicht vorhanden. Überschreibt eine bestehende (echte) Konfig NIE.
write_example_config() {
  local dir example
  dir="$(config_dir)"
  example="${dir}/env.example"

  mkdir -p "${dir}"

  if [[ -f "${example}" ]]; then
    info "Beispiel-Konfig existiert bereits: ${example} (unverändert gelassen)."
    return 0
  fi

  cat > "${example}" <<'EOF'
# RareDiseaseCompass — Beispiel-Konfig für optionale API-Keys
#
# Diese Datei ist nur eine VORLAGE. Zum Aktivieren kopieren nach:
#   ~/.config/rdc/env   (bzw. $XDG_CONFIG_HOME/rdc/env)
# und die Platzhalter durch deine echten Keys ersetzen.
#
# WICHTIG:
#   - Alle Keys sind OPTIONAL. Die meisten Quellen funktionieren ohne Key;
#     ein NCBI/Entrez-Key erhöht nur das Rate-Limit. Siehe docs/architektur.md.
#   - Echte Keys gehören NIEMALS ins Repo. Diese Datei liegt im User-Home,
#     nicht im Projektbaum.

# NCBI/Entrez (PubMed) — optional, hebt das Rate-Limit an.
# NCBI_API_KEY=__HIER_DEINEN_KEY__
EOF

  info "Beispiel-Konfig angelegt: ${example}"
}

# Hauptablauf -------------------------------------------------------------------

main() {
  info "RareDiseaseCompass — Installation der rdc-CLIs"
  info "──────────────────────────────────────────────"

  require_python

  # Idempotenz: ist `rdc` schon installiert, nicht erneut installieren.
  if command -v rdc >/dev/null 2>&1; then
    info "Das Kommando 'rdc' ist bereits installiert ($(command -v rdc))."
    info "Überspringe die Neuinstallation. Für ein Upgrade ggf. 'pipx upgrade rdc'"
    info "oder 'pip install --user --upgrade \"${CLI_DIR}\"' ausführen."
  else
    install_cli
  fi

  write_example_config

  info ""
  info "Fertig."
  info "Nächste Schritte:"
  info "  1. Optionale API-Keys eintragen (siehe Beispiel-Konfig oben)."
  info "  2. Fall-Ordner anlegen und Claude Code dort öffnen (docs/project-layout.md)."
  info "  3. Vollständige Anleitung: docs/install.md"
}

main "$@"
