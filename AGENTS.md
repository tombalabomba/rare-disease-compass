# AGENTS.md

Repo-weite **Lessons learned** und erprobte Tool-Quirks. Dies ist **kein**
Status-Log. Nur dauerhaft nützliche Erkenntnisse, knapp und konkret.

Vor Implementation lesen. Neue Erkenntnis entdeckt (Tool verhält sich anders als
erwartet, Befehl musste zweimal laufen, API-Eigenheit)? → hier ergänzen.

## Notes

Format: `- YYYY-MM-DD · <terse, specific finding inkl. konkretem Fix>`

- 2026-06-04 · Repo-Bootstrap. Backlog-System aus 4matesMiddleware übernommen, aber auf Single-Repo reduziert: kein Supabase-Auto-Deploy, kein Cross-Repo. `dev/agent-loop.sh` macht nur Ticket-Pick → Commit → nächste Iteration.
- 2026-06-04 · Architektur-Pivot: weg von Server/LibreChat/MCP, hin zu lokalem Claude-Code-Setup + agenten-nativen CLIs (Printing-Press-Muster) + lokalem Fallakten-Ordner. Open Source (GPL-3.0). Server-Tickets (INF-*, MCP-*, DEP-*) entfernt; neue Epics `setup` + `cli`. CLI-Kern framework-frei (Typer+httpx+SQLite), bis Printing-Press-Lizenz geklärt ist.
- 2026-06-04 · Maschine hat kein `python`/`python3.11` und kein Repo-venv; System-`python3` ist 3.9 (zu alt für `enum.StrEnum`). CLI-Tests laufen über `uv run --python 3.12 --with typer --with httpx --with pytest python -m pytest cli/tests/` (aus `cli/`). `ruff` liegt standalone unter `/opt/homebrew/bin/ruff`. `uv run` legt in `cli/` ein `.venv` (gitignored) + `uv.lock` an — `uv.lock` nach dem Lauf löschen, gehört nicht ins Repo.
