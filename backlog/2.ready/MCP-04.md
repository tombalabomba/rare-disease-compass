---
id: MCP-04
title: Tool — Europe PMC
status: todo
depends_on: [MCP-02]
stop_after: false
epic: mcp
commit_type: feat(mcp)
---

# MCP-04 — Tool: Europe PMC

## Why
Europe PMC ist eine offene Literatur-Datenbank (Volltext-Links, Zitationen,
breitere Abdeckung als PubMed allein, inkl. Preprints und europäischer Quellen)
und braucht keine Auth. BioMCP deckt PubMed, aber nicht Europe PMC ab. Für eine
gründliche Literatur-Recherche zu einem seltenen Fall ist die ergänzende Quelle
wertvoll. Ohne dieses Tool fehlt Claude der Europe-PMC-Zugang.

## Scope
- `mcp-server/app/tools/europepmc.py` (NEU) — Tools gegen die Europe-PMC-REST-API,
  über den zentralen HTTP-Client aus MCP-02:
  - `search(query: str, filters: ... = None) -> ...`: Volltextsuche mit optionalen
    Filtern (z. B. Quelle, Jahr, nur Open-Access). Liefert Treffer mit Titel,
    Autoren, Jahr, IDs (PMID/PMCID/DOI).
  - `get_fulltext_links(article_id: str) -> ...`: Volltext-/PDF-Links zu einem
    Artikel.
  - `citations(article_id: str) -> ...`: zitierende Arbeiten zu einem Artikel.
- `mcp-server/app/server.py` (erweitert): `register_all` registriert die neuen Tools.
- `mcp-server/app/tests/test_europepmc.py` (NEU): pytest mit **gemockten**
  Antworten — Schwerpunkt **korrekte Query-Param-Bildung** (Such-Query, `format`,
  `resultType`, Filter werden richtig in die Query gemappt) und Response-Parsing.
- Pydantic-Modelle + **deutsche Docstrings** je Tool (Eingabe/Ausgabe/Quelle).

## Files
```
mcp-server/app/tools/europepmc.py           (NEU)
mcp-server/app/server.py                    (erweitert: register_all)
mcp-server/app/tests/test_europepmc.py      (NEU)
```

## Reality Check (Pflicht — vor Promotion nach `2.ready/`)
- [x] **Files in `Scope`/`Files`**: `europepmc.py` und der Test sind NEU.
      `server.py` und `app/tests/` stammen aus MCP-02 → erweitert. `tools/`-Package
      ggf. aus MCP-03 schon vorhanden; falls dieses Ticket zuerst läuft, legt es
      `tools/__init__.py` mit an.
- [x] **`depends_on`-IDs**: `MCP-02` liefert Instanz, Registry und HTTP-Client.
- [x] **Externe Voraussetzungen**: Europe PMC REST ist **ohne Auth** öffentlich.
      Kein Secret. In den Tests kein Live-Call (gemockt).
- [x] **Tooling**: `ruff`, `pytest`, `pytest-asyncio` aus MCP-02.

## Acceptance
- [ ] Lint grün: `ruff check mcp-server/`
- [ ] Kompiliert: `python -m py_compile mcp-server/app/tools/europepmc.py mcp-server/app/server.py`
- [ ] Tests grün (gemockt): `pytest mcp-server/app/tests/test_europepmc.py`
      — prüft explizit die **Query-Param-Bildung** (Query, Filter, `format=json`,
      `resultType`) gegen die erwartete Request-URL **und** das Response-Parsing.
- [ ] Tool registriert, Docstrings vorhanden:
      `python -c "import sys; sys.path.insert(0,'mcp-server'); from app.server import mcp, register_all; register_all(mcp)"`
- [ ] Negativ-Check: kein direkter `httpx`-Aufruf im Tool-Modul:
      `! grep -Eq 'httpx\.(get|post|AsyncClient)' mcp-server/app/tools/europepmc.py`

## Out of scope
- PubMed (deckt BioMCP ab — nicht doppeln).
- Monarch/Orphanet (MCP-03), PubCaseFinder/Phen2Gene (MCP-05).
- Compose / `librechat.yaml` — MCP-06.

## Notes
- Europe-PMC-Such-Endpunkt: `https://www.ebi.ac.uk/europepmc/webservices/rest/search`
  mit `query`, `format=json`, `resultType` (`lite`/`core`), `pageSize`. Exakte
  Param-Namen gegen die aktuelle Europe-PMC-REST-Doku verifizieren.
- Volltext-Links/Zitationen laufen über eigene REST-Pfade
  (`.../{source}/{id}/fullTextUrlList`, `.../{source}/{id}/citations`) — pro Tool
  korrekt zusammensetzen.
