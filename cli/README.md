# `rdc` — RareDiseaseCompass-CLI-Kern

Framework-freier Kern der agenten-nativen Recherche-CLIs. Stellt das gemeinsame
Fundament bereit, auf dem die Quellen-Subkommandos (PubMed, Variant, Graph, DDx)
und die Compound Queries aufbauen:

- **Eine Typer-App** mit Subkommando-Registry.
- **Ein zentraler httpx-Client** mit Cache, höflichem Rate-Limit, Retry und
  Timeout.
- **Eine lokale SQLite-History**, die jede Abfrage über die Zeit durchsuchbar
  macht.

CLI-01 registriert **noch keine** echten Quellen — die Quellen-Gruppen kommen in
den Folge-Tickets (CLI-02…06) dazu und hängen sich über die Registry an.

## Installation

```bash
pipx install ./cli
# oder für die Entwicklung:
pip install -e "./cli[dev]"
```

Danach steht der Befehl `rdc` bereit:

```bash
rdc --help
rdc history --help
```

Ohne Installation aus dem `cli/`-Verzeichnis heraus:

```bash
python -m rdc.main --help
```

## Aufbau

| Modul | Aufgabe |
|---|---|
| `rdc/main.py` | Top-Level-App, `register(...)`-Registry, `history`-Gruppe, globales `--format`/`--json`. |
| `rdc/http_client.py` | `HttpClient` — User-Agent, Timeout, Retry, Rate-Limit, Cache. |
| `rdc/history.py` | SQLite-History: `connect`, `save_query`, `list_queries`, `search_queries`. |
| `rdc/output.py` | `print_table` und `print_jsonl` — agenten-freundliche Ausgabe. |

Folge-Tickets registrieren ihre Gruppe über **einen** Mechanismus:

```python
import typer
from rdc.main import register

pubmed_app = typer.Typer()
# ... Befehle definieren ...
register("pubmed", pubmed_app, help="PubMed-Recherche.")
```

## HTTP-Client: Cache, Rate-Limit, Retry

`HttpClient` (in `rdc/http_client.py`) kapselt einen `httpx.Client`:

- **User-Agent** mit Projekt- und Repo-Hinweis (überschreibbar).
- **Timeout** mit sinnvollem Default.
- **Retry mit Backoff** für transiente Fehler (5xx, Verbindungsfehler),
  begrenzte Versuche.
- **Höfliches Rate-Limit**: Mindestabstand zwischen Requests **pro Host**.
- **Prozesslokaler Cache** nach URL+Params. Ein Cache-Treffer macht **keinen**
  echten Request (`cache_hits` zählt die Treffer).
- Injizierbarer `transport` (für Tests via `httpx.MockTransport`) sowie
  austauschbare `sleep`/`monotonic`-Funktionen.

## History: wo liegt sie?

Die History-DB liegt bewusst **außerhalb** des Repos und ist gitignored:

- Default: `~/.rdc/history.db`
- Überschreibbar über die Env-Variable `RCA_HISTORY_DB`.

```bash
rdc history list                 # jüngste Abfragen, neueste zuerst
rdc history list --source pubmed # nur eine Quelle
rdc history search BRCA1         # LIKE-Suche über Quelle/Command/Params/Summary
rdc --json history list          # JSON-Lines statt Tabelle
```

Tipp: `rdc --help` und `rdc <gruppe> --help` listen alle Optionen.
