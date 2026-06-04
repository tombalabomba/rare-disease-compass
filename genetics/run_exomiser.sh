#!/usr/bin/env bash
set -euo pipefail
#
# run_exomiser.sh — VCF + HPO → Exomiser (GEN-02)
#
# Kapselt den lokalen Exomiser-Lauf in EIN Skript: VCF-Pfad + HPO-Liste rein,
# gerankte Ergebnisse unter exomiser-results/ (gitignored) raus. Harte
# Input-Validierung vor jedem Container-Start; die aus dem Template gefüllte
# Analysis-YAML (enthält lokalen VCF-Pfad + HPO-Liste des Falls) landet in einem
# temporären Verzeichnis, niemals im Repo. Defense-in-Depth: .gitignore-Sperre
# UND skript-interne Beschränkung des Schreibziels bleiben beide bestehen.
#
# Testbarkeit: main() läuft nur bei direktem Aufruf (Source-Guard am Dateiende),
# damit die Validierungs-Funktionen per `source` isoliert prüfbar sind.

# Fehlerausgabe nach stderr. Eigene Funktion, damit Meldungen, die auf docs/
# verweisen, keine Redirect-Zeichen auf derselben Zeile tragen.
err() {
  printf '%s\n' "$*" >&2
}

usage() {
  cat <<'EOF'
run_exomiser.sh — VCF + HPO → Exomiser (lokaler Batch-Lauf, vollständig offline)

Verwendung:
  ./genetics/run_exomiser.sh <vcf-pfad> <HP:nnnnnnn,HP:nnnnnnn,...> [Optionen]

Argumente:
  <vcf-pfad>     Pfad zur lokalen VCF (.vcf oder .vcf.gz). Bleibt auf der Maschine.
  <HPO-Liste>    Komma-separierte HPO-IDs, je exakt HP: gefolgt von 7 Ziffern.

Optionen:
  --assembly hg38|hg19   Referenz-Assembly (Default: hg38).
  --proband <id>         Proband-/Sample-ID in der VCF (Default: erstes Sample).
  -h, --help             Diese Hilfe.

Ergebnisse landen unter exomiser-results/ (gitignored). Es wird nichts in ein
vom Repo getracktes Verzeichnis geschrieben.
EOF
}

# validate_vcf <pfad> — existiert, ist Datei, Endung .vcf oder .vcf.gz.
validate_vcf() {
  local vcf="${1:-}"
  if [[ -z "${vcf}" ]]; then
    err "Fehler: kein VCF-Pfad angegeben."
    return 1
  fi
  if [[ ! -f "${vcf}" ]]; then
    err "Fehler: VCF-Datei nicht gefunden: '${vcf}'."
    return 1
  fi
  if [[ ! "${vcf}" =~ \.vcf$ && ! "${vcf}" =~ \.vcf\.gz$ ]]; then
    err "Fehler: VCF muss auf .vcf oder .vcf.gz enden: '${vcf}'."
    return 1
  fi
  return 0
}

# validate_hpo <csv> — jede ID matcht ^HP:[0-9]{7}$, mindestens eine. Müll/leer → Exit ≠ 0.
validate_hpo() {
  local csv="${1:-}"
  if [[ -z "${csv}" ]]; then
    err "Fehler: keine HPO-IDs angegeben (mindestens eine, Format HP:nnnnnnn)."
    return 1
  fi
  local IFS=','
  local -a ids
  read -r -a ids <<< "${csv}"
  if [[ ${#ids[@]} -eq 0 ]]; then
    err "Fehler: mindestens eine HPO-ID nötig."
    return 1
  fi
  local id
  for id in "${ids[@]}"; do
    if [[ ! "${id}" =~ ^HP:[0-9]{7}$ ]]; then
      err "Fehler: ungültige HPO-ID '${id}' — erwartet HP: gefolgt von genau 7 Ziffern."
      return 1
    fi
  done
  return 0
}

# build_hpo_yaml <csv> — wandelt "HP:1,HP:2" in eine YAML-Liste ["HP:1", "HP:2"] um.
build_hpo_yaml() {
  local csv="${1:-}"
  local IFS=','
  local -a ids
  read -r -a ids <<< "${csv}"
  local out=""
  local id
  for id in "${ids[@]}"; do
    if [[ -n "${out}" ]]; then
      out+=", "
    fi
    out+="\"${id}\""
  done
  printf '[%s]' "${out}"
}

main() {
  local script_dir repo_dir template results_dir app_props
  script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  repo_dir="$(cd "${script_dir}/.." && pwd)"
  template="${script_dir}/config/analysis.template.yml"
  results_dir="${repo_dir}/exomiser-results"
  app_props="${script_dir}/config/application.properties"

  local assembly="hg38"
  local proband=""
  local -a positional=()

  while [[ $# -gt 0 ]]; do
    case "$1" in
      -h|--help)
        usage
        return 0
        ;;
      --assembly)
        if [[ $# -lt 2 ]]; then
          err "Fehler: --assembly braucht einen Wert (hg38 oder hg19)."
          return 2
        fi
        assembly="$2"
        shift 2
        ;;
      --assembly=*)
        assembly="${1#*=}"
        shift
        ;;
      --proband)
        if [[ $# -lt 2 ]]; then
          err "Fehler: --proband braucht einen Wert."
          return 2
        fi
        proband="$2"
        shift 2
        ;;
      --proband=*)
        proband="${1#*=}"
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

  if [[ ${#positional[@]} -lt 2 ]]; then
    usage >&2
    return 2
  fi

  local vcf="${positional[0]}"
  local hpo="${positional[1]}"

  validate_vcf "${vcf}" || return 1
  validate_hpo "${hpo}" || return 1

  if [[ "${assembly}" != "hg38" && "${assembly}" != "hg19" ]]; then
    err "Fehler: --assembly muss hg38 oder hg19 sein (war: '${assembly}')."
    return 2
  fi

  if [[ ! -f "${app_props}" ]]; then
    err "Fehler: ${app_props} fehlt — aus application.properties.template erzeugen und Daten-Release-Versionen setzen (siehe docs/genetics-setup.md)."
    return 1
  fi

  # Container-interne Pfade: das VCF-Verzeichnis wird read-only nach /exomiser/vcf
  # gemountet, die VCF ist dort unter ihrem Basisnamen erreichbar.
  local vcf_dir vcf_base container_vcf hpo_yaml
  vcf_dir="$(cd "$(dirname "${vcf}")" && pwd)"
  vcf_base="$(basename "${vcf}")"
  container_vcf="/exomiser/vcf/${vcf_base}"
  hpo_yaml="$(build_hpo_yaml "${hpo}")"

  # Ergebnis-Verzeichnis (gitignored) anlegen. Einziges Schreibziel im/unter Repo.
  mkdir -p "${results_dir}"

  # Generierte Analysis-YAML in ein temporäres Verzeichnis — niemals ins Repo,
  # da sie den lokalen VCF-Pfad und die HPO-Liste des Falls enthält.
  local tmp_dir analysis_file
  tmp_dir="$(mktemp -d)"
  trap 'rm -rf "${tmp_dir}"' EXIT
  analysis_file="${tmp_dir}/analysis.yml"

  sed \
    -e "s|\"__VCF_PATH__\"|\"${container_vcf}\"|" \
    -e "s|\"__HPO_IDS__\"|${hpo_yaml}|" \
    -e "s|^  genomeAssembly:.*|  genomeAssembly: ${assembly}|" \
    -e "s|^  proband:.*|  proband: \"${proband}\"|" \
    "${template}" > "${analysis_file}"

  err "Starte Exomiser (${assembly}) — Ergebnisse nach ${results_dir}."

  # Container-Start. Mounts/Vars setzen das Referenzdaten-, VCF- und Output-Dir;
  # die temporäre Analysis-YAML wird read-only zusätzlich eingehängt und per
  # --analysis angesprochen, sodass nichts in das getrackte config/ geschrieben wird.
  EXOMISER_VCF_DIR="${vcf_dir}" \
  EXOMISER_RESULTS_DIR="${results_dir}" \
  docker compose -f "${script_dir}/docker-compose.exomiser.yml" run --rm \
    -v "${analysis_file}:/exomiser/analysis.yml:ro" \
    exomiser \
    --analysis /exomiser/analysis.yml \
    --spring.config.location=/exomiser/config/application.properties
}

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  main "$@"
fi
