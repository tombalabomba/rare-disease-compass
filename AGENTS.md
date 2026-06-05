# AGENTS.md

Repo-weite **Lessons learned** und erprobte Tool-Quirks. Dies ist **kein**
Status-Log. Nur dauerhaft nützliche Erkenntnisse, knapp und konkret.

Vor Implementation lesen. Neue Erkenntnis entdeckt (Tool verhält sich anders als
erwartet, Befehl musste zweimal laufen, API-Eigenheit)? → hier ergänzen.

## Notes

Format: `- YYYY-MM-DD · <terse, specific finding inkl. konkretem Fix>`

- 2026-06-04 · Repo-Bootstrap. Backlog-System aus 4matesMiddleware übernommen, aber auf Single-Repo reduziert: kein Supabase-Auto-Deploy, kein Cross-Repo. `dev/agent-loop.sh` macht nur Ticket-Pick → Commit → nächste Iteration.
- 2026-06-04 · Architektur-Pivot: weg von Server/LibreChat/MCP, hin zu lokalem Claude-Code-Setup + agenten-nativen CLIs (agenten-native CLIs) + lokalem Fallakten-Ordner. Open Source (GPL-3.0). Server-Tickets (INF-*, MCP-*, DEP-*) entfernt; neue Epics `setup` + `cli`. CLI-Kern framework-frei (Typer+httpx+SQLite), framework-frei (eine geprüfte Agent-CLI-Bibliothek war unlizenziert und damit für OSS nicht nutzbar).
- 2026-06-06 · COM-01: `api.orphadata.com` hat **keinen** Organisations-Datensatz (nur `rd-associated-genes`, `rd-classification`, `rd-cross-referencing`, `rd-epidemiology`, `rd-medical-specialties`, `rd-natural_history`, `rd-phenotypes`); der frühere Download `en_product8.xml` ist 404. RareConnect ist eine reine React-SPA ohne API/Sitemap (jeder Pfad liefert dieselbe 202600-B-Shell → Slugs serverseitig nicht verifizierbar). Folge: `rdc community` ist als **Wegweiser** gebaut — Disease→ORPHA via `rd-cross-referencing` auflösen, dann klickbare Orphanet-Disease-/RareConnect-Browse-Links statt erfundener Org-Namen. Verifizierte Stabil-URLs: `https://www.orpha.net/en/disease/detail/<orpha>` (200), `https://www.orpha.net/en/disease` (200, Such-Fallback), `https://www.rareconnect.org/en/communities` (200).
- 2026-06-04 · Maschine hat kein `python`/`python3.11` und kein Repo-venv; System-`python3` ist 3.9 (zu alt für `enum.StrEnum`). CLI-Tests laufen über `uv run --python 3.12 --with typer --with httpx --with pytest python -m pytest cli/tests/` (aus `cli/`). `ruff` liegt standalone unter `/opt/homebrew/bin/ruff`. `uv run` legt in `cli/` ein `.venv` (gitignored) + `uv.lock` an — `uv.lock` nach dem Lauf löschen, gehört nicht ins Repo.
