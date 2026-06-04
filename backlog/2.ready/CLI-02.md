---
id: CLI-02
title: Literatur-Quelle (PubMed + Europe PMC)
status: todo
depends_on: [CLI-01]
stop_after: false
epic: cli
commit_type: feat(cli)
---

# CLI-02 — Literatur-Quelle (PubMed + Europe PMC)

## Why
Bei seltenen Fällen ist die Fachliteratur die wichtigste Welt-Wissen-Quelle: Case
Reports, Gen-Phänotyp-Assoziationen, Therapieerfahrungen. Claude Code braucht einen
knappen, agenten-freundlichen Weg, PubMed (NCBI E-utilities) und Europe PMC
abzufragen und Treffer mit Quellen-IDs (PMID/PMCID) zu liefern. Ohne dieses Ticket
hat das System keine Literatur-Anbindung; mit ihm landet jede Suche in der
SQLite-History und wird über die Zeit durchsuchbar (`docs/architektur.md`).

## Scope
**`cli/rca/sources/literature.py`** — eine Typer-Subkommando-Gruppe, die sich über
die Registry aus CLI-01 in `rca` einhängt. Befehle:

- **`rca pubmed search <query>`** — sucht via NCBI E-utilities `esearch`
  (db=pubmed), liefert PMIDs; optional direkt `esummary`/`efetch` für Titel, Autoren,
  Jahr, Journal. Optionen: `--retmax` (Trefferzahl), `--json`.
- **`rca pubmed fetch <pmid...>`** — holt Detaildaten (Titel, Abstract sofern
  verfügbar, Autoren, Jahr, DOI) zu einer oder mehreren PMIDs via `efetch`/`esummary`.
- **`rca europepmc search <query>`** — sucht über die Europe-PMC-REST-Suche
  (`/search`), liefert Titel, Autoren, Jahr, Quelle, PMID/PMCID/DOI. Optionen:
  `--page-size`, `--json`.

Eigenschaften:
- Nutzt den **zentralen httpx-Client** aus CLI-01 (Cache/Rate-Limit/Retry/Timeout/
  User-Agent) — keine eigene HTTP-Schicht.
- **Optionaler NCBI-API-Key** aus Env (`NCBI_API_KEY`): wenn gesetzt, als Query-Param
  anhängen (erhöht das erlaubte Rate-Limit); wenn nicht gesetzt, ohne Key arbeiten.
- Query-Param-Bildung in einer **reinen, testbaren Funktion** (URL/Params ohne
  HTTP-Call konstruierbar), damit Tests die Param-Bildung ohne Netzwerk prüfen.
- Response-**Parsing** in reinen Funktionen (E-utilities-JSON/XML-Struktur bzw.
  Europe-PMC-JSON → schlanke Result-Records).
- Jede Suche/jeder Fetch schreibt einen **History-Eintrag** über `history.save_query`
  (source `pubmed`/`europepmc`, command, params, summary, count).
- Ausgabe über `output.py` (Tabelle/JSONL), immer mit Quellen-IDs (PMID/PMCID/DOI).

## Files
```
cli/rca/sources/__init__.py        (NEU, falls noch nicht vorhanden)
cli/rca/sources/literature.py      (NEU)
cli/rca/main.py                    (erweitert: Registrierung der literature-Gruppe)
cli/tests/test_literature.py       (NEU)
```

## Reality Check (Pflicht — vor Promotion nach `2.ready/`)
- [x] **Files in `Scope`/`Files`**: `literature.py` und der Test sind NEU.
      `cli/rca/sources/` wird mit CLI-02 angelegt (CLI-01 legt es nicht zwingend an).
      `cli/rca/main.py` existiert nach CLI-01 (done) und wird um die Registrierung
      erweitert.
- [x] **`depends_on`-IDs**: CLI-01 liefert Registry (`main.register`), httpx-Client
      (mit `transport`-Injection), History (`save_query`) und Output. Erst nutzbar,
      wenn CLI-01 in `backlog/3.done/` liegt.
- [x] **Externe Voraussetzungen**: NCBI-API-Key ist **optional** (Env `NCBI_API_KEY`);
      ohne Key voll funktionsfähig. Kein Pflicht-Secret → kein `stop_after`.
- [x] **Tooling**: `ruff`/`pytest` wie CLI-01. Tests injizieren `httpx.MockTransport`
      in den CLI-01-Client — keine echten E-utilities-/Europe-PMC-Calls.

## Acceptance
- [ ] `ruff check cli/` ohne Findings.
- [ ] `python -m py_compile cli/rca/sources/literature.py cli/tests/test_literature.py`
      ohne Fehler.
- [ ] `pytest cli/tests/test_literature.py` grün — alle HTTP-Interaktionen über
      `httpx.MockTransport` (kein echter Netzwerk-Call).
- [ ] CLI startbar: `rca pubmed --help` und `rca europepmc --help` listen die
      Subkommandos (`search`, `fetch` bzw. `search`).
- [ ] **Query-Param-Bildung getestet:** die reine Param-Funktion erzeugt die
      erwarteten E-utilities-Params (db, term, retmax …); mit gesetztem
      `NCBI_API_KEY` ist der `api_key`-Param enthalten, ohne nicht.
- [ ] **Parsing getestet:** aus einer gemockten E-utilities-/Europe-PMC-Response
      werden die erwarteten Records (PMID/Titel/Jahr) extrahiert.
- [ ] **History-Eintrag getestet:** nach einer (gemockten) Suche enthält die
      in-memory-History einen Eintrag mit `source` `pubmed`/`europepmc`.
- [ ] **Negativ-Check:** keine eigene HTTP-Implementierung —
      `! grep -nE 'httpx\.(get|post|Client\()' cli/rca/sources/literature.py`
      (HTTP läuft über den CLI-01-Client).

## Out of scope
- **Volltext-Download von PDFs** oder Open-Access-Volltext-Mining: nur Metadaten +
  ggf. Abstract.
- **Andere Quellen** (Variant, Graph, DDx): CLI-03…05.
- **Kombinierte Quervergleiche** (z. B. Literatur ∩ Variante): CLI-06 (Compound).

## Notes
- **E-utilities-Etikette.** NCBI erwartet höfliches Verhalten (Rate-Limit, optionaler
  API-Key, `tool`/`email`-Identifikation). Rate-Limit/User-Agent liefert der
  CLI-01-Client; den API-Key nur als Param anhängen, **nie** loggen.
- **XML vs. JSON.** E-utilities können XML liefern; wenn JSON-Modus
  (`retmode=json`) verfügbar ist, diesen bevorzugen, sonst XML robust parsen. Das
  Parsing in eine reine Funktion kapseln (testbar ohne HTTP).
- **History immer schreiben.** Auch leere Treffer protokollieren (count 0) — der
  Recherche-Speicher soll zeigen, was schon gesucht wurde (`docs/architektur.md`).
