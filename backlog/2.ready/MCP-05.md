---
id: MCP-05
title: Tools — PubCaseFinder + Phen2Gene
status: todo
depends_on: [MCP-02]
stop_after: false
epic: mcp
commit_type: feat(mcp)
---

# MCP-05 — Tools: PubCaseFinder + Phen2Gene

## Why
Das sind die beiden Differenzialdiagnose-Motoren: PubCaseFinder nimmt eine Liste
HPO-IDs und gibt **gerankte seltene Krankheiten** zurück, Phen2Gene nimmt eine
Liste HPO-IDs und gibt **Kandidatengene** zurück. Genau der Use-Case dieses
Projekts (Eingabe ist oft eine HPO-Symptom-Liste). Beide fehlen in BioMCP. Ohne
diese Tools kann Claude aus den Symptomen keine priorisierten Hypothesen ziehen.

## Scope
- `mcp-server/app/tools/pubcasefinder.py` (NEU):
  - `ranked_diseases(hpo_ids: list[str]) -> ...`: HPO-Liste rein → nach Ähnlichkeit
    gerankte seltene Krankheiten (mit Score und Krankheits-ID).
- `mcp-server/app/tools/phen2gene.py` (NEU):
  - `candidate_genes(hpo_ids: list[str]) -> ...`: HPO-Liste rein → priorisierte
    Kandidatengene (mit Rang/Score).
- Beide über den zentralen HTTP-Client aus MCP-02.
- `mcp-server/app/server.py` (erweitert): `register_all` registriert die neuen Tools.
- `mcp-server/app/tests/test_pubcasefinder.py` (NEU) und
  `mcp-server/app/tests/test_phen2gene.py` (NEU): pytest mit **gemockten**
  Antworten — Schwerpunkt: **HPO-Listen-Eingabe wird korrekt serialisiert**
  (das jeweils erwartete Format der API: kommagetrennt vs. wiederholte Params vs.
  JSON-Body) **und** Response-Parsing (Ranking-Felder).
- Pydantic-Modelle + **deutsche Docstrings** je Tool (Eingabe/Ausgabe/Quelle).

## Files
```
mcp-server/app/tools/pubcasefinder.py        (NEU)
mcp-server/app/tools/phen2gene.py            (NEU)
mcp-server/app/server.py                     (erweitert: register_all)
mcp-server/app/tests/test_pubcasefinder.py   (NEU)
mcp-server/app/tests/test_phen2gene.py       (NEU)
```

## Reality Check (Pflicht — vor Promotion nach `2.ready/`)
- [x] **Files in `Scope`/`Files`**: beide Tool-Files und Tests sind NEU.
      `server.py` und `app/tests/` aus MCP-02 → erweitert. `tools/`-Package ggf.
      schon aus MCP-03/04; sonst hier mit `tools/__init__.py` anlegen.
- [x] **`depends_on`-IDs**: `MCP-02` liefert Instanz, Registry, HTTP-Client.
- [x] **Externe Voraussetzungen**: PubCaseFinder und Phen2Gene sind öffentliche
      REST-APIs ohne Auth. Kein Secret. Tests gemockt, kein Live-Call.
- [x] **Tooling**: `ruff`, `pytest`, `pytest-asyncio` aus MCP-02.

## Acceptance
- [ ] Lint grün: `ruff check mcp-server/`
- [ ] Kompiliert: `python -m py_compile mcp-server/app/tools/pubcasefinder.py mcp-server/app/tools/phen2gene.py mcp-server/app/server.py`
- [ ] Tests grün (gemockt): `pytest mcp-server/app/tests/test_pubcasefinder.py mcp-server/app/tests/test_phen2gene.py`
      — testen explizit die **korrekte Serialisierung der HPO-Liste** im
      ausgehenden Request (erwartetes API-Format) **und** das Response-Parsing
      (Ranking/Score).
- [ ] Tools registriert, Docstrings vorhanden:
      `python -c "import sys; sys.path.insert(0,'mcp-server'); from app.server import mcp, register_all; register_all(mcp)"`
- [ ] Negativ-Check: kein direkter `httpx`-Aufruf in den Tool-Modulen:
      `! grep -Eq 'httpx\.(get|post|AsyncClient)' mcp-server/app/tools/pubcasefinder.py mcp-server/app/tools/phen2gene.py`

## Out of scope
- Monarch/Orphanet (MCP-03), Europe PMC (MCP-04).
- Quellen aus BioMCP — nicht doppeln.
- Compose / `librechat.yaml` — MCP-06.

## Notes
- **HPO-Format pro API getrennt verifizieren** — PubCaseFinder und Phen2Gene
  erwarten die Symptomliste nicht zwingend identisch (kommagetrennte Liste,
  wiederholte Query-Params oder JSON-Body). Genau dieser Punkt ist die häufigste
  Fehlerquelle und wird im Test fixiert.
- PubCaseFinder-REST: HPO-IDs → gerankte OMIM/Orphanet-Krankheiten. Endpunkt und
  Param-Namen gegen die aktuelle PubCaseFinder-API-Doku prüfen.
- Phen2Gene-REST: HPO-IDs → Kandidatengene mit Rang. Endpunkt/Param gegen die
  aktuelle Phen2Gene-API-Doku prüfen.
