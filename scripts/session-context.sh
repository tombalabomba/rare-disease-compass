#!/usr/bin/env bash
set -euo pipefail
#
# session-context.sh — Sitzungs-Kontext für RareDiseaseCompass (EXP-03)
#
# Gibt zu Sitzungsbeginn einen ruhigen Lagebericht zu EINEM Fall aus: Fallstand
# (pseudonymisierte Stammdaten + kodierte Symptome + jüngster Zeitleisten-Eintrag)
# und die offenen Fragen/Hypothesen aus der Akte. Optional ein einzeiliger
# Literatur-Hinweis aus der rdc-History — nur ein Hinweis, keine Aktion.
#
# Bewusst opt-in und nicht-drängend: ein Lagebericht, kein Alarm. RDC bleibt auch
# ohne dieses Skript nutzbar — Claude Code liest die Fallakte ohnehin direkt.
#
# Datenschutz: gibt NUR die Zusammenfassung aus (pseudonymisierte Stammdaten,
# Symptom-Anzahl, offene Fragen). NIEMALS Rohbefunde, Genom-/Variantenzeilen oder
# den Inhalt der Genetik-Sektion. Defense-in-Depth: das Skript wählt aktiv aus,
# was es ausgibt, statt die Akte ungefiltert durchzureichen.
#
# Als Claude-Code-SessionStart-Hook (optional) in .claude/settings.json einbinden:
#
#   {
#     "hooks": {
#       "SessionStart": [
#         { "hooks": [
#             { "type": "command",
#               "command": "scripts/session-context.sh /pfad/zum/fall-ordner" }
#         ] }
#       ]
#     }
#   }
#
# Der Block ist auch jederzeit manuell aufrufbar — der Hook ist Komfort, keine
# Voraussetzung.
#
# Testbarkeit: main() läuft nur bei direktem Aufruf (Source-Guard am Dateiende),
# damit die Hilfsfunktionen per `source` isoliert prüfbar sind.

# Ausgabe-Helfer ----------------------------------------------------------------

# err <msg...> — Hinweise/Fehler nach stderr.
err() {
  printf '%s\n' "$*" >&2
}

usage() {
  cat <<'EOF'
session-context.sh — Sitzungs-Kontext für einen RareDiseaseCompass-Fall

Verwendung:
  ./scripts/session-context.sh <fall-ordner> [Optionen]

Argumente:
  <fall-ordner>   Pfad zum Fall-Ordner (Konvention KB-03/SET-01): enthält eine
                  oder mehrere case-file*.md. Liegt außerhalb des Repos.

Optionen:
  --db <pfad>     rdc-History-DB für den Literatur-Hinweis (Default: $RCA_HISTORY_DB
                  oder ~/.rdc/history.db). Fehlt sie, wird der Hinweis übersprungen.
  -h, --help      Diese Hilfe.

Gibt einen ruhigen Lagebericht aus: Fallstand + offene Fragen, optional ein
einzeiliger Literatur-Hinweis. Nur Zusammenfassung, niemals Rohdaten. Fehlt der
Ordner oder die History, erscheint ein freundlicher Hinweis (Exit 0).
EOF
}

# Datei-Auswertung --------------------------------------------------------------

# extract_section <datei> <header> — gibt die Zeilen zwischen einer exakten
# "## …"-Überschrift und der nächsten "## "-Überschrift aus (ohne die Überschrift).
extract_section() {
  local file="$1" header="$2"
  awk -v hdr="$header" '
    $0 == hdr { inside = 1; next }
    inside && /^## / { inside = 0 }
    inside { print }
  ' "$file"
}

# print_bullets <datei> <header> <fallback> — gibt die nicht-leeren Zeilen einer
# Sektion eingerückt aus; ist die Sektion leer/fehlt, den Fallback-Text.
print_bullets() {
  local file="$1" header="$2" fallback="$3" line found=0
  while IFS= read -r line; do
    [[ -z "${line//[[:space:]]/}" ]] && continue
    printf '  %s\n' "${line}"
    found=1
  done < <(extract_section "${file}" "${header}")
  if [[ "${found}" -eq 0 ]]; then
    printf '  %s\n' "${fallback}"
  fi
}

# count_symptoms <datei> — Anzahl korrekt kodierter HPO-IDs in der Symptom-Sektion.
count_symptoms() {
  local file="$1"
  extract_section "${file}" "## Symptome" | { grep -cE 'HP:[0-9]{7}' || true; }
}

# last_timeline <datei> — jüngster (letzter) Listeneintrag der Zeitleiste.
last_timeline() {
  local file="$1"
  extract_section "${file}" "## Zeitleiste" \
    | { grep -E '^[[:space:]]*-' || true; } \
    | tail -n 1 \
    | sed -E 's/^[[:space:]]*-[[:space:]]*//'
}

# Literatur-Hinweis aus der History --------------------------------------------

# literature_hint <db-pfad> — gibt, falls möglich, einen einzeiligen Hinweis auf
# neue Recherche-Einträge seit dem letzten Lauf aus und aktualisiert den Marker.
# Fehlt die History oder sqlite3, ein freundlicher Hinweis (kein Fehler).
literature_hint() {
  local db="$1"
  if ! command -v sqlite3 >/dev/null 2>&1; then
    printf '  Literatur-Abgleich übersprungen: sqlite3 nicht verfügbar.\n'
    return 0
  fi
  if [[ ! -f "${db}" ]]; then
    printf '  Noch keine Recherche-History gefunden — Literatur-Abgleich übersprungen.\n'
    return 0
  fi

  local marker last_run now count
  marker="$(dirname "${db}")/.session-context-last-run"
  last_run=""
  if [[ -f "${marker}" ]]; then
    last_run="$(cat "${marker}")"
  fi
  now="$(date -u +"%Y-%m-%dT%H:%M:%S+00:00")"

  # Neue Einträge seit dem letzten Lauf (ISO-8601-Zeitstempel sortieren lexikografisch).
  count="$(sqlite3 "${db}" \
    "SELECT COUNT(*) FROM queries WHERE timestamp > '${last_run//\'/}';" 2>/dev/null || true)"

  printf '%s' "${now}" > "${marker}" 2>/dev/null || true

  if [[ -z "${last_run}" ]]; then
    printf '  Erster Lagebericht — künftige neue Recherchen werden hier gemeldet (rdc history list).\n'
  elif [[ "${count}" =~ ^[1-9][0-9]*$ ]]; then
    printf '  Seit deiner letzten Sitzung: %s neue Recherche-Eintrag/-Einträge (rdc history list).\n' "${count}"
  else
    printf '  Seit deiner letzten Sitzung keine neuen Recherche-Einträge.\n'
  fi
}

# Hauptablauf -------------------------------------------------------------------

main() {
  local folder="" db="${RCA_HISTORY_DB:-${HOME}/.rdc/history.db}"
  local -a positional=()

  while [[ $# -gt 0 ]]; do
    case "$1" in
      -h|--help)
        usage
        return 0
        ;;
      --db)
        if [[ $# -lt 2 ]]; then
          err "Fehler: --db braucht einen Wert."
          return 2
        fi
        db="$2"
        shift 2
        ;;
      --db=*)
        db="${1#*=}"
        shift
        ;;
      --)
        shift
        while [[ $# -gt 0 ]]; do
          positional+=("$1")
          shift
        done
        ;;
      -*)
        err "Fehler: unbekannte Option '$1'."
        usage >&2
        return 2
        ;;
      *)
        positional+=("$1")
        shift
        ;;
    esac
  done

  if [[ ${#positional[@]} -ge 1 ]]; then
    folder="${positional[0]}"
  fi

  # Fehlt der Ordner / existiert er nicht: freundlicher Hinweis statt Fehler.
  if [[ -z "${folder}" || ! -d "${folder}" ]]; then
    echo "RareDiseaseCompass — Sitzungs-Kontext"
    echo
    if [[ -z "${folder}" ]]; then
      echo "Kein Fall-Ordner angegeben. Aufruf: scripts/session-context.sh <fall-ordner>"
    else
      echo "Fall-Ordner nicht gefunden: '${folder}'. Bitte Pfad zur Fallakte prüfen."
    fi
    echo "Sobald ein Fall-Ordner vorliegt, erscheint hier Fallstand + offene Fragen."
    return 0
  fi

  # Primäre Fallakte im Ordner finden (Konvention KB-03: case-file*.md).
  local -a case_files=()
  local f
  while IFS= read -r f; do
    case_files+=("${f}")
  done < <(find "${folder}" -maxdepth 1 -type f -name 'case-file*.md' | sort)

  if [[ ${#case_files[@]} -eq 0 ]]; then
    echo "RareDiseaseCompass — Sitzungs-Kontext"
    echo
    echo "Im Ordner '${folder}' wurde keine Fallakte (case-file*.md) gefunden."
    echo "Lege die Akte nach docs/case-file-TEMPLATE.md an, dann gibt es hier einen Lagebericht."
    return 0
  fi

  local case_file="${case_files[0]}"

  echo "════════════════════════════════════════════"
  echo "  RareDiseaseCompass — Sitzungs-Kontext"
  echo "════════════════════════════════════════════"
  echo

  echo "Fallstand"
  echo "─────────"
  print_bullets "${case_file}" "## Stammdaten" "(keine Stammdaten vermerkt)"
  printf '  Kodierte Symptome: %s\n' "$(count_symptoms "${case_file}")"
  local latest
  latest="$(last_timeline "${case_file}")"
  if [[ -n "${latest}" ]]; then
    printf '  Zuletzt in der Zeitleiste: %s\n' "${latest}"
  fi
  echo

  echo "Offene Fragen"
  echo "─────────────"
  print_bullets "${case_file}" "## Offene Fragen" "(keine offenen Fragen vermerkt)"
  echo

  echo "Literatur"
  echo "─────────"
  literature_hint "${db}"
  echo

  echo "Ruhiger Lagebericht, keine Diagnose. Details: Fallakte direkt lesen, rdc history list."
}

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  main "$@"
fi
