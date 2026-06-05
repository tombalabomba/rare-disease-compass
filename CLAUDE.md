# CLAUDE.md — RareDiseaseCompass

Projekt-Konventionen, die **immer** gelten. Vor jeder Ticket-Bearbeitung lesen.

## Was dieses Projekt ist

Ein lokaler KI-Recherche-Assistent für seltene Krankheitsfälle, wie ein
persönliches Wissenssystem für genau einen Krankheitsfall.
**Kein Server, keine Web-App, keine Cloud-Infrastruktur.** Die
Architektur ist bewusst minimal:

1. **Claude Code** als Oberfläche (läuft lokal, in VS Code/Codium oder Terminal).
2. **Agenten-native CLIs** über öffentliche Medizin-APIs.
3. **Ein lokaler Ordner** mit der HPO-codierten, pseudonymisierten Fallakte.
4. **Exomiser lokal** für die Genetik (VCF bleibt auf der Maschine).

Siehe [README.md](README.md) und [docs/architektur.md](docs/architektur.md).

## Unverhandelbare Regeln

### Datenschutz (höchste Priorität)
- **Niemals** echte Patientendaten, Namen, Geburtsdaten, VCF-/Genom-Dateien oder
  Befund-PDFs ins Repo committen. Nur Software, Templates und **synthetische** Fixtures.
- Test-Fixtures sind **erfundene** Menschen. Keine realen Daten.
- Die CLI-SQLite-History kann fallbezogene Inhalte ansammeln → liegt außerhalb des
  Repos und ist gitignored (`*.db`, `*.sqlite`, `.cache/`).
- PII-Leck = kritischer Bug, sofort `status: blocked`.

### Open Source
- Das Repo ist (oder wird) öffentlich. Alles muss **generisch** sein, nicht an
  einen bestimmten Fall gebunden. Keine fallspezifischen Inhalte im Code/Doku.
- Lizenz: GPL-3.0-or-later ([LICENSE](LICENSE)). Neue Dateien erben das.

### Code-Disziplin
- Keine Stubs, keine Placeholders, keine `TODO`-Marker im Production-Code.
- Single source of truth. Keine doppelten Abstraktionsschichten.
- Scope = nur die Pfade aus `Files` im Ticket. Erweiterung = neues Ticket.

## Tech-Stack & Konventionen

| Bereich | Wahl | Hinweis |
|---|---|---|
| Oberfläche | Claude Code | nutzt die CLIs via Shell, liest die Fallakte als Dateien |
| Daten-CLIs | Python 3.11 + Typer + httpx + SQLite | agenten-nativ (knappe Befehle, lokale History), OSS-clean ohne proprietäre Abhängigkeit |
| CLI-History | lokale SQLite-DB | akkumulierter Recherche-Speicher, gitignored |
| Genetik | Exomiser (Docker, **lokal**) | läuft gegen VCF auf der Maschine, nie remote |
| Fallakte | Markdown im lokalen/geteilten Ordner (z. B. Dropbox) | HPO-codiert, pseudonymisiert |
| Python-Tooling | `ruff`, `pytest`, `mypy` | |
| Shell | `bash`, `shellcheck`-clean, `set -euo pipefail` | |

> **CLI-Stil:** „Agenten-nativ" heißt: knappe, kombinierbare Befehle mit lokaler
> SQLite-History, für eine KI als Bediener gebaut. Bewusst **framework-frei**
> (Typer + httpx + SQLite), ohne proprietäre Laufzeit-Abhängigkeit — wichtig für
> die OSS-Sauberkeit (GPL-3.0).

## Sprache
- Doku, Tickets, Commit-Bodies, Nutzer-Texte: **Deutsch**.
- Code, Variablennamen, CLI-Befehle, öffentliche README-Teile: Englisch erlaubt/üblich.

## Commits
- Ein Commit pro Ticket. Prefix aus dem Frontmatter (`commit_type`).
- Footer: `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`
- **Niemals** zu remote pushen — der Mensch pusht nach Review.

## Lessons learned
Tool-Quirks, API-Eigenheiten, wiederholte Befehle → [AGENTS.md](AGENTS.md)
(`## Notes`), Format `- YYYY-MM-DD · <terse, specific>`.
