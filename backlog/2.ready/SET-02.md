---
id: SET-02
title: CLI-Installer & API-Key-Konfiguration
status: todo
depends_on: [CLI-01]
stop_after: false
epic: setup
commit_type: feat(setup)
---

# SET-02 — CLI-Installer & API-Key-Konfiguration

## Why
Damit ein Nutzer die `rdc`-CLIs überhaupt nutzen kann, müssen sie einmalig auf
seiner Maschine installiert werden. Ohne ein definiertes Installations-Skript macht
das jeder anders (falsche Python-Version, fehlende `pipx`, Keys im Repo). SET-02
liefert ein idempotentes Shell-Skript, das das `cli/`-Paket installiert, die
Python-Version prüft und eine **Beispiel-Konfig** für optionale API-Keys anlegt
(z. B. NCBI/Entrez) — ohne je echte Keys ins Repo zu schreiben. Plus eine kurze
deutsche Anleitung. Das ist die „letzte Meile" zwischen geklontem Repo und
lauffähigem Assistenten und Voraussetzung für ONB-01 (Runbook).

## Scope
Zwei neue Dateien — Installer-Skript + Anleitung:

**1. `scripts/install.sh`** (`bash`, `set -euo pipefail`, `shellcheck`-clean):
- **Python-Version prüfen:** erkennt `python3` und stellt sicher, dass mindestens
  3.11 vorhanden ist (Stack-Vorgabe aus `CLAUDE.md`). Fehlt es / zu alt → klare
  deutsche Fehlermeldung und Exit ≠ 0.
- **Installations-Backend wählen:** bevorzugt `pipx` (isolierte CLI-Installation);
  fällt auf `pip --user` zurück, wenn `pipx` fehlt. Installiert das `cli/`-Paket aus
  dem Repo (Pfad relativ zum Skript ermittelt, nicht hartkodiert auf das CWD).
- **Idempotenz:** prüft **vor** der Installation, ob das `rdc`-Kommando schon
  verfügbar ist (`command -v rdc`); wenn ja, meldet das und überspringt die
  Neuinstallation (bzw. bietet ein Upgrade an, ohne zu erzwingen). Mehrfaches
  Ausführen darf nichts kaputt machen und keinen Fehler werfen.
- **Beispiel-Konfig anlegen:** legt — falls noch nicht vorhanden — eine
  **Beispiel**-Konfig für optionale API-Keys im User-Konfig-Verzeichnis an
  (z. B. `~/.config/rdc/config.toml.example` oder `~/.config/rdc/env.example`),
  mit auskommentierten Platzhaltern (`NCBI_API_KEY=__HIER_DEINEN_KEY__`) und einem
  deutschen Kommentar, dass die Keys **optional** sind und niemals ins Repo gehören.
  Überschreibt eine bestehende echte Konfig **nie**.
- Verständliche deutsche Fortschritts-/Abschluss-Ausgaben (was installiert wurde,
  wo die Beispiel-Konfig liegt, nächster Schritt: Keys eintragen, Verweis auf
  `docs/install.md`).

**2. `docs/install.md`** (deutsch): kurze Anleitung — Voraussetzungen (Python ≥ 3.11,
optional `pipx`), Aufruf `bash scripts/install.sh`, was das Skript tut, wie man die
optionalen API-Keys (NCBI/Entrez) einträgt und warum sie optional sind, Hinweis auf
SET-01 (`docs/project-layout.md`) für den nächsten Schritt (Fall-Ordner + Claude
Code). Klarer Datenschutz-Hinweis: echte Keys nur lokal, nie committen.

## Files
```
scripts/install.sh   (NEU)
docs/install.md      (NEU)
```

## Reality Check (Pflicht — vor Promotion nach `2.ready/`)
- [x] **Files in `Scope`/`Files`**: beide NEU. `scripts/` existiert (`ls scripts/`
      → `agent-loop.sh`); `docs/` existiert. `scripts/install.sh` existiert noch
      nicht.
- [x] **`depends_on`-IDs**: `CLI-01` muss `done` sein — es liefert das
      installierbare `cli/`-Paket (Typer-App, Befehl `rdc`). Ohne dieses Paket hat
      `install.sh` nichts zu installieren. Der Loop zieht SET-02 erst, wenn `CLI-01`
      in `backlog/3.done/` liegt. **Annahme an CLI-01:** das `cli/`-Paket ist als
      installierbares Python-Paket strukturiert (mit `pyproject.toml`/Entry-Point
      `rdc`). Der Installer ermittelt den Paketpfad relativ zum Skript und übergibt
      ihn an `pipx install`/`pip install`; der exakte Paket-Root wird bei der
      Implementierung gegen das dann existierende `cli/` verifiziert (siehe Notes).
- [x] **Externe Voraussetzungen**: keine Secrets, kein Server. `pipx`/`pip` sind
      Standard-Tooling; fehlt `pipx`, fällt das Skript dokumentiert auf `pip --user`
      zurück. API-Keys sind optional und werden nur als **Beispiel** angelegt.
- [x] **Tooling**: `shellcheck` und `bash -n` für die Acceptance. Beide laufen
      statisch ohne echte Installation — die Acceptance führt das Skript NICHT real
      aus (kein Netzwerk, kein Schreiben ins User-Home im Test).

## Acceptance
- [ ] `shellcheck scripts/install.sh` ohne Findings.
- [ ] `bash -n scripts/install.sh` (Syntax-Check) ohne Fehler.
- [ ] Skript setzt strikte Fehlerbehandlung:
      `grep -qE '^\s*set -euo pipefail' scripts/install.sh`
- [ ] Idempotenz-Prüfung vorhanden (prüft vor Installation):
      `grep -q 'command -v rdc' scripts/install.sh`
- [ ] Python-Versions-Prüfung vorhanden (referenziert 3.11):
      `grep -q '3.11' scripts/install.sh`
- [ ] Installations-Backend referenziert (`pipx` mit `pip`-Fallback):
      `grep -q 'pipx' scripts/install.sh && grep -q 'pip' scripts/install.sh`
- [ ] Beispiel-Konfig wird als `.example`-Datei angelegt (nicht als echte Konfig):
      `grep -qE 'config.*\.example|env\.example|\.example' scripts/install.sh`
- [ ] **Negativ-Check (keine echten Keys / kein Secret im Repo):** das Skript
      schreibt keine realen Keys in getrackte Dateien; die Beispiel-Konfig enthält
      nur Platzhalter. Maschinell — kein NCBI-Key-Literal, nur Platzhalter:
      `! grep -qE 'NCBI_API_KEY=[A-Za-z0-9]{8,}' scripts/install.sh`
      und das Skript schreibt seine Beispiel-Konfig ins User-Konfig-Verzeichnis
      (`$HOME`/`~/.config`), nicht ins Repo:
      `grep -qE '\$HOME|~/.config|XDG_CONFIG_HOME' scripts/install.sh`
- [ ] `docs/install.md` benennt Aufruf und optionale Keys:
      `grep -q 'scripts/install.sh' docs/install.md &&
       grep -qiE 'optional' docs/install.md &&
       grep -qiE 'ncbi|api-?key' docs/install.md`

## Out of scope
- **Implementierung der CLIs selbst:** der Befehl `rdc` und seine Subkommandos
  entstehen im `cli`-Epic (CLI-01…06). SET-02 installiert nur das fertige Paket.
- **Echter Installations-Lauf / Netzwerk:** die Acceptance prüft das Skript
  statisch (`shellcheck`, `bash -n`). Ein realer `pipx install`-Lauf ist
  Smoke-Test (Mensch, lokal).
- **Fall-Ordner / Claude-Code-Konfig:** Ablage und Persona sind SET-01 + KB-04.
- **Verwaltung echter API-Keys:** das Skript legt nur eine Beispiel-Konfig an; das
  Eintragen echter Keys ist ein manueller Nutzer-Schritt (in `docs/install.md`
  beschrieben).

## Notes
- **Braucht das `cli/`-Paket aus CLI-01.** Vor der Implementierung das dann
  existierende `cli/` ansehen: Paket-Root, `pyproject.toml`, Entry-Point-Name
  (`rdc`). Den Installpfad daraus ableiten, nicht raten. Liegt der Entry-Point
  anders als `rdc`, das Idempotenz-/`command -v`-Kommando entsprechend anpassen —
  Single source of truth ist das tatsächliche Paket.
- **`set -euo pipefail` als erste echte Zeile** nach der Shebang/Kommentaren.
  `shellcheck` muss clean sein: Variablen quoten, `[[ ]]` statt `[ ]` wo sinnvoll,
  keine unbenutzten Variablen.
- **Pfad relativ zum Skript** ermitteln (z. B. via `$(cd "$(dirname
  "${BASH_SOURCE[0]}")" && pwd)`), damit der Installer unabhängig vom CWD läuft —
  der Agent-Loop und Nutzer rufen aus unterschiedlichen Verzeichnissen auf.
- **Datenschutz:** echte Keys nie ins Repo. Die Beispiel-Konfig gehört ins
  User-Home (`~/.config/rdc/`), nicht in den Repo-Baum. `.env`/`*.key` sind ohnehin
  via `.gitignore` gesperrt — die Beispiel-Datei trotzdem klar als `.example`
  benennen.
