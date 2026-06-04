---
id: CLI-01
title: CLI-Kern (Typer-App, httpx-Client, SQLite-History)
status: todo
depends_on: []
stop_after: false
epic: cli
commit_type: feat(cli)
---

# CLI-01 — CLI-Kern (Typer-App, httpx-Client, SQLite-History)

## Why
Alle Quellen-Subkommandos (CLI-02…05) und die Compound Queries (CLI-06) bauen auf
einem gemeinsamen Fundament auf: einer einzelnen Typer-App mit Subkommando-Registry,
einem zentralen httpx-Client (Cache, höfliches Rate-Limit, Retry, Timeout,
User-Agent) und der lokalen SQLite-History, die jede Abfrage über die Zeit
durchsuchbar macht. Ohne diesen Kern hat keines der Folge-Tickets einen Ort, an dem
es sich registrieren kann, und es gäbe keinen einheitlichen HTTP-Pfad — jede Quelle
würde Cache/Rate-Limit/Retry neu erfinden. Dieses Ticket legt den framework-freien
Kern an (kein proprietäres Printing-Press-Laufzeit-Paket, siehe `CLAUDE.md` und
`dev/backlog/PLAN.md`).

## Scope
Ein installierbares Python-Paket `cli/` mit folgendem Aufbau:

**1. `cli/pyproject.toml`** — Paket-Definition (PEP 621). Name `rdc`, Python `>=3.11`,
Dependencies exakt `typer`, `httpx`, `pydantic`. Console-Script-Entrypoint
`rdc = "rdc.main:app"`, sodass `pipx install ./cli` bzw. `pip install -e ./cli` den
Befehl `rdc` bereitstellt. Optionale Dev-Dependency-Gruppe mit `pytest`, `ruff`,
`mypy`. Build-Backend (z. B. `hatchling` oder `setuptools`) konfiguriert.

**2. `cli/rdc/__init__.py`** — Paket-Init mit `__version__`-String.

**3. `cli/rdc/main.py`** — die Typer-`app` (Top-Level). Eine **Registry**-Funktion,
über die Folge-Tickets ihre Subkommando-Gruppen (`typer.Typer()`-Instanzen)
anhängen: z. B. eine Funktion `register(name: str, sub: typer.Typer, help: str)`
oder eine zentrale Liste, die `main.py` beim Import auflöst. CLI-01 registriert
**noch keine** echten Quellen — die Gruppen sind leer/kommen in CLI-02…06 dazu.
Ein eingebautes `rdc history`-Subkommando (Gruppe) mit `list` und `search` als
sichtbare, sofort nutzbare Funktion auf der History (siehe Punkt 5).

**4. `cli/rdc/http_client.py`** — zentraler HTTP-Zugriff über `httpx`. Eine Klasse
oder Factory, die einen konfigurierten `httpx.Client` kapselt mit:
- **User-Agent** (projektspezifischer String inkl. Kontakt-/Repo-Hinweis).
- **Timeout** (sinnvoller Default, überschreibbar).
- **Retry** mit Backoff für transiente Fehler (5xx, Verbindungsfehler),
  begrenzte Versuche.
- **Höfliches Rate-Limit** (minimaler Abstand zwischen Requests pro Host).
- **Cache** (in-memory Dict nach URL+Params; optional auf Platte erweiterbar, aber
  hier reicht prozesslokaler Cache mit Hit-Erkennung). Cache-Treffer macht **keinen**
  echten Request.
- Der Konstruktor akzeptiert einen injizierbaren `transport`-Parameter
  (`httpx.BaseTransport`), damit Tests `httpx.MockTransport` einspeisen können —
  **keine echten Netzwerk-Calls im Test**.

**5. `cli/rdc/history.py`** — SQLite-History. Funktionen:
- `connect(path)` öffnet/erstellt die DB; akzeptiert `":memory:"` für Tests.
- Schema-Init (Tabelle `queries`: id, timestamp, source, command, params (JSON),
  result_summary, result_count, raw (optional JSON)).
- `save_query(...)` speichert eine Abfrage + Ergebnis.
- `list_queries(limit, source=None)` listet zeitlich absteigend.
- `search_queries(term)` durchsucht über Quelle/Command/Params/Summary (LIKE).
- Default-DB-Pfad liegt **außerhalb** des Repos (z. B. unter `~/.rdc/history.db`
  oder via Env `RCA_HISTORY_DB`), ist also gitignored (`*.db` greift bereits).

**6. `cli/rdc/output.py`** — agenten-freundliche Formatierung: knappe Tabellen und
JSON-Lines. Mindestens `print_table(rows, headers)` und `print_jsonl(records)`.
Jede Ausgabe trägt Quellen-IDs (PMID, RCV, OMIM/ORPHA etc.) mit; ein
`--json`/`--format`-Schalter (global oder pro Befehl) wählt zwischen Tabelle und
JSON-Lines.

**7. `cli/README.md`** — kurze deutsche Doku: Installation (pipx/pip), Aufbau
(Subkommando-Gruppen pro Quelle), wo die History liegt (lokal, gitignored), wie der
HTTP-Client Cache/Rate-Limit/Retry handhabt, Hinweis auf `--help`.

**8. `cli/tests/`** — pytest-Tests:
- `test_http_client.py`: nutzt `httpx.MockTransport`. Prüft, dass ein zweiter Aufruf
  derselben URL aus dem **Cache** kommt (Transport wird nur einmal getroffen), dass
  bei einem 5xx ein **Retry** erfolgt und danach Erfolg möglich ist, dass der
  **User-Agent**-Header gesetzt ist und das Rate-Limit den Mindestabstand respektiert
  (mit gemockter Zeit/Schlaf, kein echtes Warten im Test).
- `test_history.py`: in-memory SQLite. Speichern → auflisten → durchsuchen; prüft
  Reihenfolge, Filter nach `source`, LIKE-Suche.

## Files
```
cli/pyproject.toml            (NEU)
cli/rdc/__init__.py           (NEU)
cli/rdc/main.py               (NEU)
cli/rdc/http_client.py        (NEU)
cli/rdc/history.py            (NEU)
cli/rdc/output.py             (NEU)
cli/README.md                 (NEU)
cli/tests/__init__.py         (NEU)
cli/tests/test_http_client.py (NEU)
cli/tests/test_history.py     (NEU)
```

## Reality Check (Pflicht — vor Promotion nach `2.ready/`)
- [x] **Files in `Scope`/`Files`**: alle werden bewusst NEU angelegt. `cli/` existiert
      noch nicht (`ls -R cli` im Repo-Root liefert nichts) — wird neu erstellt.
- [x] **`depends_on`-IDs**: keine — CLI-01 ist die Wurzel des `cli`-Epics
      (`dev/backlog/PLAN.md`, Abhängigkeitsgraph: `CLI01 --> CLI02…05`).
- [x] **Externe Voraussetzungen**: keine. Keine API-Keys, keine echten Netzwerk-Calls
      (Tests mocken via `httpx.MockTransport`). DB-Default liegt außerhalb des Repos
      und ist über `*.db`/`*.sqlite` in `.gitignore:36-40` bereits gesperrt.
- [x] **Tooling**: `ruff`, `pytest` sind die in `CLAUDE.md` benannten Python-Tools.
      `python -m py_compile` ist Standard. `typer`, `httpx`, `pydantic` werden über
      `pyproject.toml` installiert (`pip install -e ./cli`).

## Acceptance
- [ ] `ruff check cli/` ohne Findings.
- [ ] `python -m py_compile cli/rdc/*.py cli/tests/*.py` ohne Fehler.
- [ ] `pytest cli/tests/` grün — HTTP-Tests nutzen ausschließlich
      `httpx.MockTransport` (kein echter Netzwerk-Call), History-Tests nutzen
      in-memory SQLite (`":memory:"`).
- [ ] CLI startbar und Hilfe vorhanden: `rdc --help` (bzw.
      `python -m rdc.main --help` aus `cli/`) listet die `history`-Gruppe; die
      Quellen-Gruppen sind noch leer (kommen in CLI-02…06).
- [ ] Cache-Verhalten getestet: zweiter Request derselben URL trifft den
      MockTransport **nicht** erneut (Hit-Zähler im Test).
- [ ] History-Roundtrip getestet: `save_query` → `list_queries`/`search_queries`
      liefern den Eintrag zurück (in-memory).
- [ ] **Negativ-Check (framework-frei):** kein Import eines proprietären
      Printing-Press-/Framework-Pakets im Code —
      `! grep -rniE 'import +printing|from +printing|import +pp_|printing_press' cli/`.
- [ ] **Negativ-Check (Dependencies):** `pyproject.toml` deklariert genau
      `typer`, `httpx`, `pydantic` als Laufzeit-Dependencies (Dev-Tools separat) —
      keine weitere Laufzeit-Abhängigkeit.

## Out of scope
- **Echte Quellen-Anbindungen** (PubMed, Variant, Graph, DDx): CLI-02…05. Hier nur
  die leere Registry und die Hooks, an denen sie hängen.
- **Compound Queries:** CLI-06.
- **CLI-Installer/Setup-Skript** (Installation auf einer Maschine, API-Key-Konfig):
  SET-02 (`dev/backlog/PLAN.md`, Modul-Karte).
- **Persistenter Platten-Cache / TTL-Strategie:** prozesslokaler in-memory Cache
  reicht für CLI-01; eine ausgefeiltere Cache-Schicht wäre ein eigenes Ticket.

## Notes
- **History-DB nie ins Repo.** Default-Pfad außerhalb des Repos (`~/.rdc/` oder
  `RCA_HISTORY_DB`-Env). `.gitignore:36-40` sperrt `*.db`/`*.sqlite`/`.cache/` —
  trotzdem nie eine DB-Datei unter den getrackten Pfaden anlegen.
- **Tests mocken HTTP zwingend.** `httpx.MockTransport` in den Client injizieren;
  öffentliche APIs werden im Test **nie** echt getroffen (`dev/backlog/AGENT-LOOP.md`,
  Schritt 6). Auch das Rate-Limit-Warten im Test mocken (kein echter `sleep`).
- **Registry single source of truth.** Folge-Tickets registrieren ihre Gruppe über
  **einen** definierten Mechanismus in `main.py` — keine zweite Parallel-Registry
  anlegen (Single source of truth, `CLAUDE.md`).
- **Quellen-IDs immer mitführen.** Jede Ergebniszeile/JSONL-Record trägt die
  Quellen-ID (PMID, RCV, ORPHA …), damit Claude Code Quellen referenzieren kann
  (`docs/architektur.md`, CLI-Design-Tabelle).
