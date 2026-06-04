---
id: GEN-02
title: VCF + HPO → Exomiser Wrapper-Skript
status: done
depends_on: [GEN-01]
stop_after: false
epic: genetics
commit_type: feat(genetics)
---

# GEN-02 — VCF + HPO → Exomiser Wrapper-Skript

## Why
GEN-01 liefert Container und Templates, aber kein Mensch soll von Hand ein
Analysis-YAML basteln, Platzhalter ersetzen und den Container mit den richtigen
Mounts starten — fehleranfällig und leicht datenschutz-gefährdend (Output ins
falsche Verzeichnis). GEN-02 kapselt den Lauf in **ein** Skript: VCF-Pfad +
HPO-Liste rein, gerankte Exomiser-Ergebnisse unter `exomiser-results/` (gitignored)
raus. Mit harter Input-Validierung, damit kein Müll an den Container geht und damit
**nichts** in ein vom Repo getracktes Verzeichnis geschrieben wird.

## Scope
Eine Datei: **`genetics/run_exomiser.sh`** — ein `bash`-Skript mit
`set -euo pipefail`, `shellcheck`-clean. Funktionsumfang:

- **CLI:** `./genetics/run_exomiser.sh <vcf-pfad> <HP:nnnnnnn,HP:nnnnnnn,...>`
  (HPO-Liste komma-separiert) plus optionale Flags (`--assembly hg38|hg19`,
  `--proband <id>`). Usage-/Help-Ausgabe bei fehlenden Argumenten.
- **Input-Validierung (eigene Funktionen, einzeln testbar):**
  - `validate_vcf`: VCF-Pfad existiert und ist eine Datei; Endung `.vcf` oder
    `.vcf.gz`. Fehlt die Datei → Fehlermeldung + Exit ≠ 0.
  - `validate_hpo`: jede HPO-ID matcht exakt `^HP:[0-9]{7}$`. Mindestens eine ID.
    Müll (`HP:123`, `foo`, leer) → Fehlermeldung + Exit ≠ 0, **kein** Lauf.
- **YAML-Generierung:** kopiert `genetics/config/analysis.template.yml`, ersetzt
  `__VCF_PATH__` (Container-interner Pfad des gemounteten VCF) und `__HPO_IDS__`
  (HPO-Liste im YAML-Listen-Format) in eine **temporäre** Analysis-Datei. Die
  generierte YAML-Datei landet **nicht** im Repo (temp-Verzeichnis oder
  `exomiser-results/`), nie in `genetics/config/`.
- **Container-Start:** `docker compose -f genetics/docker-compose.exomiser.yml run`
  mit den passenden Env-Variablen/Mounts (Referenzdaten-Dir, VCF-Dir, Output-Dir),
  sodass Exomiser die generierte Analysis-Datei ausführt.
- **Output:** Ergebnisse ausschließlich nach `exomiser-results/` (gitignored). Das
  Skript legt das Verzeichnis bei Bedarf an und schreibt **nirgendwo sonst** im Repo.
- Sprechende deutsche Fehlermeldungen, Exit-Codes ≠ 0 bei jedem Validierungsfehler.

## Files
```
genetics/run_exomiser.sh   (NEU)
```

## Reality Check (Pflicht — vor Promotion nach `2.ready/`)
- [x] **Files in `Scope`/`Files`**: `genetics/run_exomiser.sh` wird NEU angelegt.
      `genetics/` entsteht in GEN-01.
- [x] **`depends_on`-IDs**: `GEN-01` liefert `analysis.template.yml` (mit den
      Platzhaltern `__VCF_PATH__`/`__HPO_IDS__`, die dieses Skript ersetzt) und das
      Compose-File, das es startet. GEN-02 zieht der Loop erst, wenn GEN-01 in einem
      `done/`-Ordner liegt.
- [x] **Externe Voraussetzungen**: `docker` und die Referenzdaten braucht nur der
      **echte** Lauf (Smoke-Test). Die Acceptance prüft Skript-Syntax, shellcheck und
      die Validierungs-Funktionen **ohne** Container-Start — die Validierung läuft
      vor jedem `docker`-Aufruf und ist isoliert testbar.
- [x] **Tooling**: `shellcheck` und `bash -n` müssen verfügbar sein; beide sind in
      CLAUDE.md als Projekt-Standard genannt. Falls `shellcheck` lokal fehlt: per
      Paketmanager nachinstallieren (Installationsschritt, kein Blocker).

## Acceptance
- [ ] `shellcheck genetics/run_exomiser.sh` ohne Findings.
- [ ] `bash -n genetics/run_exomiser.sh` ok (Syntax-Check).
- [ ] Skript beginnt mit `set -euo pipefail`:
      `grep -qE '^set -euo pipefail' genetics/run_exomiser.sh`
- [ ] **HPO-Format-Validierung getestet** — die `validate_hpo`-Funktion lehnt Müll
      ab und akzeptiert Gültiges. Prüfbar durch Sourcing in einer Subshell, die nur
      die Funktion lädt (das Skript ruft `main` nur bei direktem Aufruf, nicht beim
      Sourcen — Guard `[[ "${BASH_SOURCE[0]}" == "${0}" ]]`):
      ```
      bash -c 'source genetics/run_exomiser.sh; validate_hpo "HP:0002028,HP:0002910"' && \
      ! bash -c 'source genetics/run_exomiser.sh; validate_hpo "HP:123"' && \
      ! bash -c 'source genetics/run_exomiser.sh; validate_hpo "foo"' && \
      ! bash -c 'source genetics/run_exomiser.sh; validate_hpo ""'
      ```
- [ ] **Negativ-Check (Datenschutz):** das Skript schreibt nur nach
      `exomiser-results/` (gitignored) — kein Schreibziel in einem getrackten
      Verzeichnis. Es gibt **keinen** Write/Redirect/`cp`/`mv`/`tee` nach
      `genetics/config/`, `docs/` oder ins Repo-Root:
      `! grep -nE '(>|>>|tee|cp |mv ).*(genetics/config|docs/)' genetics/run_exomiser.sh`
      und der Output-Pfad referenziert `exomiser-results`:
      `grep -q 'exomiser-results' genetics/run_exomiser.sh`
- [ ] **Negativ-Check (keine echten Daten):** kein eingebetteter Genom-/VCF-Inhalt,
      keine realen Patientendaten im Skript — nur Logik, Pfade, Platzhalter.

## Out of scope
- **Container-Definition & Templates:** kommen aus GEN-01 — hier nur genutzt.
- **Output-Parsing → Akte:** GEN-03.
- **Referenzdaten-Download:** manueller Schritt aus GEN-01 (`docs/genetics-setup.md`).
- **Echter Exomiser-Lauf gegen reale VCF:** Smoke-Test (Mensch, lokal). Die
  Acceptance prüft Validierung + Skript-Hygiene, nicht den Container-Lauf.

## Notes
- **Source-Guard für Testbarkeit.** Damit die Acceptance `validate_hpo` per `source`
  isoliert prüfen kann, darf `main` nur bei direktem Aufruf laufen:
  `if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then main "$@"; fi`. Beim Sourcen werden
  nur die Funktionen definiert, **kein** `docker`-Aufruf ausgelöst.
- **Generiertes YAML nie ins Repo.** Die aus dem Template gefüllte Analysis-Datei
  enthält den (lokalen) VCF-Pfad und die HPO-Liste des Falls — sie gehört in ein
  temp-Verzeichnis oder nach `exomiser-results/` (gitignored), niemals nach
  `genetics/config/` (getracked). Sonst Datenschutz-Bruch.
- **HPO-Regex strikt** `^HP:[0-9]{7}$` — identisch zu KB-01 und `epic-cli`, damit
  der Verbindungsschlüssel über alle Epics konsistent bleibt.
- **Defense-in-Depth:** Die `.gitignore`-Sperre (`exomiser-results/`, `*.vcf`) UND
  die Skript-interne Beschränkung des Schreibziels bleiben **beide** — nicht das
  eine zugunsten des anderen wegoptimieren.
