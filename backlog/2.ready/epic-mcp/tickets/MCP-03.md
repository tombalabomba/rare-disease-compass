---
id: MCP-03
title: Tools — Monarch + Orphanet
status: todo
depends_on: [MCP-02]
stop_after: false
epic: mcp
commit_type: feat(mcp)
---

# MCP-03 — Tools: Monarch + Orphanet

## Why
Monarch Initiative ist der Phänotyp↔Gen↔Krankheit-Graph und integriert OMIM,
Orphanet, GARD und NORD in einer Schnittstelle — der zentrale Hebel, um von einer
Liste HPO-Symptomen auf seltene Krankheiten und Gene zu kommen. Orphanet ergänzt
detaillierte Daten zu seltenen Krankheiten (Gene, Vererbungsmuster). Beide Quellen
fehlen in BioMCP. Ohne diese Tools kann Claude den Krankheits-Graph nicht live
abfragen.

## Scope
- `mcp-server/app/tools/monarch.py` (NEU) — Tools gegen die Monarch-REST-API,
  jeweils über den zentralen HTTP-Client aus MCP-02:
  - `disease_by_phenotypes(hpo_ids: list[str]) -> ...`: nimmt eine Liste von
    HPO-IDs (z. B. `["HP:0002014", "HP:0001508"]`) und liefert die nach
    Phänotyp-Übereinstimmung gerankten Krankheiten.
  - `gene_to_diseases(gene_id: str) -> ...`: Krankheiten zu einem Gen
    (HGNC-/NCBIGene-ID oder Symbol).
  - `disease_detail(disease_id: str) -> ...`: Detail-Datensatz zu einer
    Krankheits-ID (MONDO/OMIM/Orphanet).
- `mcp-server/app/tools/orphanet.py` (NEU) — Tools gegen Orphanet/Orphadata:
  - rare-disease lookup (Suche / Detail nach ORPHA-Code oder Name).
  - Gene und Vererbungsmuster zu einer seltenen Krankheit.
- `mcp-server/app/server.py` (erweitert): `register_all` registriert die neuen
  Tool-Funktionen.
- `mcp-server/app/tests/test_monarch.py` (NEU) und
  `mcp-server/app/tests/test_orphanet.py` (NEU): pytest mit **gemockten**
  API-Antworten (Fixtures als synthetisches JSON) — prüfen Request-Aufbau
  (richtige URL/Query, HPO-Liste korrekt serialisiert) **und** Response-Parsing
  (erwartete Felder im Ergebnis).
- Pydantic-Eingabe-/Ausgabe-Modelle und **deutsche Docstrings** je Tool (Claude
  liest diese als Tool-Beschreibung — Eingabe, Ausgabe, Quelle benennen).

## Files
```
mcp-server/app/tools/__init__.py            (NEU, falls noch nicht vorhanden)
mcp-server/app/tools/monarch.py             (NEU)
mcp-server/app/tools/orphanet.py            (NEU)
mcp-server/app/server.py                    (erweitert: register_all)
mcp-server/app/tests/test_monarch.py        (NEU)
mcp-server/app/tests/test_orphanet.py       (NEU)
```

## Reality Check (Pflicht — vor Promotion nach `2.ready/`)
- [x] **Files in `Scope`/`Files`**: `mcp-server/app/tools/` und die Tool-Files sind
      NEU. `server.py` und `app/tests/` werden von MCP-02 angelegt → hier
      erweitert. Existenz gilt erst nach MCP-02 `done` (Dependency).
- [x] **`depends_on`-IDs**: `MCP-02` liefert FastMCP-Instanz, `register_all` und den
      HTTP-Client (`get_json`). Erst nach dessen `done` ist die Basis da.
- [x] **Externe Voraussetzungen**: Monarch und Orphanet sind öffentliche REST-APIs
      ohne zwingende Auth (Orphanet teils Registrierung für Bulk-Download, der
      REST-Lookup ist offen). In den Tests **kein** Live-Call — JSON gemockt.
- [x] **Tooling**: `ruff`, `pytest`, `pytest-asyncio` aus MCP-02-`pyproject.toml`
      vorhanden.

## Acceptance
- [ ] Lint grün: `ruff check mcp-server/`
- [ ] Kompiliert: `python -m py_compile mcp-server/app/tools/monarch.py mcp-server/app/tools/orphanet.py mcp-server/app/server.py`
- [ ] Tests grün (gemockt): `pytest mcp-server/app/tests/test_monarch.py mcp-server/app/tests/test_orphanet.py`
      — testen Request-Aufbau (URL/Query, HPO-Liste korrekt serialisiert) **und**
      Response-Parsing gegen synthetische Fixture-Antworten.
- [ ] Tools sind registriert und tragen Docstrings:
      `python -c "import sys; sys.path.insert(0,'mcp-server'); from app.server import mcp, register_all; register_all(mcp)"`
      und je Tool ein nicht-leerer `__doc__` (im Test asserten oder per
      `python`-Einzeiler prüfen).
- [ ] Negativ-Check: kein direkter `httpx`-Aufruf in den Tool-Modulen
      (alles über den zentralen Client):
      `! grep -Eq 'httpx\.(get|post|AsyncClient)' mcp-server/app/tools/monarch.py mcp-server/app/tools/orphanet.py`

## Out of scope
- Europe PMC, PubCaseFinder, Phen2Gene — eigene Tickets (MCP-04, MCP-05).
- Quellen, die BioMCP schon abdeckt — nicht doppeln.
- Compose / `librechat.yaml`-Verdrahtung — MCP-06.

## Notes
- Monarch-API: Endpunkte für Assoziationen (`/association`/Phänotyp-Suche) und
  Entity-Detail; exakte Pfade gegen die aktuelle Monarch-API-Doku verifizieren
  und in einem kurzen Modul-Kommentar festhalten.
- Orphanet/Orphadata: für reine Lookups die offene REST-Schnittstelle nutzen.
  Falls ein Endpunkt Registrierung verlangt → `status: blocked` mit Hinweis, nicht
  raten.
- HPO-Listen-Serialisierung (mehrere `HP:...`-IDs) ist der fehleranfälligste Teil →
  explizit testen (richtiges Query-Format der Monarch-API).
