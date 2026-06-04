# CLAUDE.md — rare-case-assistant

Projekt-Konventionen, die **immer** gelten. Vor jeder Ticket-Bearbeitung lesen.

## Was dieses Projekt ist

Ein selbst-gehosteter KI-Recherche-Assistent für einen pädiatrischen Krankheitsfall.
Private Fallakte (RAG) + öffentliche Medizin-Datenbanken (MCP) + Chat (LibreChat),
auf einem Hetzner-Server (EU). Siehe [README.md](README.md) und
[docs/architektur.md](docs/architektur.md).

## Unverhandelbare Regeln

### Datenschutz (höchste Priorität)
- **Niemals** echte Patientendaten, Namen, Geburtsdaten, VCF-/Genom-Dateien oder
  Befund-PDFs ins Repo committen. Nur Software, Templates und **synthetische** Fixtures.
- Test-Fixtures sind **erfundene** Menschen. Keine realen Initialen, keine realen Daten.
- Beim Bau von Pseudonymisierungs-/Ingestion-Code: defensiv. Lieber zu viel als zu
  wenig blocken. PII-Leck = kritischer Bug, sofort `status: blocked`.
- Secrets gehören in `.env` (gitignored) und auf dem Server in den Secret-Store,
  nie in den Code, nie in ein Ticket.

### Code-Disziplin (aus AGENT-LOOP.md)
- Keine Stubs, keine Placeholders, keine `TODO`-Marker im Production-Code.
- Single source of truth. Keine Adapter-/Wrapper-Schichten, die ein Konzept doppeln.
- Defense-in-Depth-Schichten nie wegoptimieren (z. B. App-Auth UND Firewall).
- Scope = nur die Pfade aus `Files` im Ticket. Erweiterung = neues Ticket.

## Tech-Stack & Konventionen

| Bereich | Wahl | Hinweis |
|---|---|---|
| Chat-App | LibreChat (Docker) | bringt Auth, Verlauf, RAG, MCP-Support mit |
| Vektor-DB / RAG | Postgres + pgvector (LibreChat RAG-API) | Teil des Compose-Stacks |
| Reverse Proxy | Caddy | automatisches Let's-Encrypt-TLS |
| LLM | Anthropic Claude (`claude-opus-4-8`) | über LibreChat-Endpoint |
| Fertige Daten-Tools | BioMCP | PubMed, ClinVar, dbSNP, MyVariant/gnomAD, ClinicalTrials |
| Eigene Daten-Tools | Python 3.11 + FastMCP | Monarch, Orphanet, Europe PMC, PubCaseFinder, Phen2Gene |
| Genetik | Exomiser (Docker, **lokal**) | läuft gegen VCF, nicht auf dem Server |
| Python-Tooling | `ruff` (lint+format), `pytest`, `mypy` | |
| Shell | `bash`, `shellcheck`-clean, `set -euo pipefail` | |

## Sprache
- Doku, Tickets, Commit-Bodies, Nutzer-sichtbare Texte: **Deutsch**.
- Code, Variablennamen, Tool-Namen: Englisch.

## Commits
- Ein Commit pro Ticket. Prefix aus dem Frontmatter (`commit_type`).
- Footer: `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`
- **Niemals** zu remote pushen — der Mensch pusht nach Review.

## Lessons learned
Tool-Quirks, wiederholte Befehle, Repo-Eigenheiten gehören nach
[AGENTS.md](AGENTS.md) (`## Notes`), Format `- YYYY-MM-DD · <terse, specific>`.
Niemals Status-Reports dort ablegen.
