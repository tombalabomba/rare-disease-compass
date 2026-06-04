---
id: MCP-02
title: Eigener FastMCP-Server — Scaffold + HTTP-Basis
status: todo
depends_on: []
stop_after: false
epic: mcp
commit_type: feat(mcp)
---

# MCP-02 — Eigener FastMCP-Server: Scaffold + HTTP-Basis

## Why
Die Quellen, die BioMCP **nicht** abdeckt (Monarch, Orphanet, Europe PMC,
PubCaseFinder, Phen2Gene), brauchen einen eigenen MCP-Server. Dieses Ticket legt
das Fundament: die FastMCP-Instanz mit Tool-Registry und einen zentralen
HTTP-Client, der öffentliche APIs **höflich** abfragt (Cache, Rate-Limit, Timeout,
Retry). Ohne diese Basis kann kein Tool-Ticket (MCP-03..05) gebaut werden — jedes
Tool nutzt diesen einen Client (single source of truth, kein direktes `httpx` in
den Tools).

## Scope
- `mcp-server/pyproject.toml` (NEU): Projekt-Metadaten, Dependencies (`fastmcp`,
  `httpx`, `pydantic`), Dev-Dependencies (`ruff`, `pytest`, `pytest-asyncio`),
  `[tool.ruff]`-Konfiguration. Package `app`.
- `mcp-server/app/__init__.py` (NEU): leer, macht `app` zum Package.
- `mcp-server/app/server.py` (NEU): erzeugt die FastMCP-Instanz (`FastMCP("rare-case")`)
  und eine zentrale `register_all(mcp)`-Funktion, die später die Tool-Module
  registriert. Aktuell registriert sie nichts (leere, aber aufrufbare Registry).
  `main()`-Entrypoint, der den Server im stdio-Modus startet.
- `mcp-server/app/http_client.py` (NEU): async-Client um `httpx.AsyncClient` mit:
  - **Cache:** In-Memory, Key = (Methode, URL, sortierte Query-Params), TTL-basiert.
  - **Rate-Limit:** minimaler Abstand zwischen Requests pro Host (höflich, konfig.).
  - **Retry:** begrenzte Versuche mit exponentiellem Backoff bei 5xx / Timeout;
    4xx (außer 429) wird **nicht** wiederholt.
  - **Timeout:** Default-Timeout pro Request.
  - **User-Agent:** sprechender, projektidentifizierender String.
  - Öffentliche async-Methode `get_json(url, params=None)`.
- `mcp-server/Dockerfile` (NEU): Python-3.11-Slim-Basis, installiert das Package,
  Entrypoint startet `app.server:main`. Non-root-User.
- `mcp-server/README.md` (NEU): kurze deutsche Doku — Zweck, Start lokal
  (`python -m app.server`), Start im Container, wie Tools registriert werden.
- `mcp-server/app/tests/__init__.py` (NEU) + `mcp-server/app/tests/test_http_client.py`
  (NEU): pytest für den HTTP-Client mit **gemocktem** Transport
  (`httpx.MockTransport`) — prüft Cache-Treffer (zweiter Call → kein zweiter
  Netzwerk-Request), Rate-Limit-Abstand, Retry-Verhalten, gesetzten User-Agent.

## Files
```
mcp-server/pyproject.toml                       (NEU)
mcp-server/Dockerfile                           (NEU)
mcp-server/README.md                            (NEU)
mcp-server/app/__init__.py                      (NEU)
mcp-server/app/server.py                        (NEU)
mcp-server/app/http_client.py                   (NEU)
mcp-server/app/tests/__init__.py                (NEU)
mcp-server/app/tests/test_http_client.py        (NEU)
```

## Reality Check (Pflicht — vor Promotion nach `2.ready/`)
- [x] **Files in `Scope`/`Files`**: `mcp-server/` existiert noch nicht
      (`ls mcp-server` → fehlt) → komplett NEU, keine Kollision.
- [x] **`depends_on`-IDs**: keine. MCP-02 ist die Wurzel des eigenen Servers und
      sofort baubar.
- [x] **Externe Voraussetzungen**: keine Secrets, keine Server. Alle Ziel-APIs
      sind öffentlich; in diesem Ticket werden sie **nicht** live aufgerufen
      (HTTP im Test gemockt).
- [x] **Tooling**: `python3.11`, `pip`, `ruff`, `pytest` lokal verfügbar bzw. über
      `pip install -e mcp-server[dev]` herstellbar. `docker` nur für den manuellen
      Image-Build nötig, **nicht** Teil der Acceptance.

## Acceptance
- [ ] Lint grün: `ruff check mcp-server/`
- [ ] Alle Python-Files kompilieren:
      `python -m py_compile $(find mcp-server -name '*.py')`
- [ ] Tests grün (HTTP gemockt): `pytest mcp-server/app/tests/`
      — deckt mindestens ab: Cache-Treffer beim zweiten gleichen Request,
      Rate-Limit-Abstand, Retry bei 5xx, gesetzter `User-Agent`.
- [ ] Server importiert und Registry ist (leer) aufrufbar:
      `python -c "import sys; sys.path.insert(0,'mcp-server'); from app.server import mcp, register_all; register_all(mcp)"`
- [ ] Kein direkter Netzwerk-Aufruf in den Tests (Negativ-Check):
      `! grep -Rnq 'AsyncClient()' mcp-server/app/tests` und Tests nutzen
      `MockTransport` (`grep -Rq 'MockTransport' mcp-server/app/tests`).

## Out of scope
- Konkrete Daten-Tools (Monarch, Orphanet, Europe PMC, PubCaseFinder, Phen2Gene) —
  je eigenes Ticket (MCP-03..05). Hier nur Scaffold + Client + leere Registry.
- Persistenter/Redis-Cache — In-Memory mit TTL reicht für diesen Anwendungsfall.
- Compose-Verdrahtung / `librechat.yaml`-Eintrag — das macht MCP-06.

## Notes
- FastMCP-Tool-Registrierung erfolgt über Decorator `@mcp.tool` bzw.
  `mcp.add_tool`. `register_all(mcp)` soll der einzige Ort sein, an dem die
  Tool-Module ihre Registrierung anstoßen — so bleibt `server.py` die single
  source of truth für die Registry.
- Cache/Rate-Limit/Retry/Timeout sind Konstanten oben in `http_client.py`
  (klar benannt), kein verstreutes Magic-Number-Setup.
- Tests müssen **ohne Netz** laufen (`httpx.MockTransport`), sonst sind sie nicht
  maschinell verlässlich und hängen an der Erreichbarkeit öffentlicher APIs.
