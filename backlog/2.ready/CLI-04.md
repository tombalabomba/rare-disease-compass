---
id: CLI-04
title: Krankheits-Graph-Quelle (Monarch + Orphanet)
status: todo
depends_on: [CLI-01]
stop_after: false
epic: cli
commit_type: feat(cli)
---

# CLI-04 — Krankheits-Graph-Quelle (Monarch + Orphanet)

## Why
Die Monarch Initiative und Orphanet verknüpfen Phänotypen (HPO), Gene und
Krankheiten in einem Graphen. Für seltene Fälle ist genau das die Brücke vom
beobachteten Symptombild zu Kandidaten-Krankheiten und vom Kandidaten-Gen zu
assoziierten Erkrankungen. Claude Code braucht knappe Befehle, die aus einer Liste
von HPO-IDs Krankheiten ableiten und Orphanet-Einträge nachschlagen — mit Quellen-IDs
(MONDO/OMIM/ORPHA). Ohne dieses Ticket fehlt dem System die graph-basierte
Phänotyp→Krankheit-Verbindung.

## Scope
**`cli/rca/sources/graph.py`** — Typer-Subkommando-Gruppe, registriert über die
CLI-01-Registry. Befehle:

- **`rca monarch diseases-by-phenotypes <HPO...>`** — nimmt eine **Liste von
  HPO-IDs** und fragt die Monarch-API ab, welche Krankheiten am besten zum
  Phänotyp-Profil passen. Liefert Krankheit (MONDO/OMIM/ORPHA-ID + Name) und, falls
  die API es gibt, einen Score/Rang. Optionen: `--limit`, `--json`.
- **`rca monarch gene-to-diseases <gene>`** — nimmt ein Gen (Symbol oder ID) und
  liefert die assoziierten Krankheiten (Krankheits-IDs + Namen) aus dem
  Monarch-Graphen.
- **`rca orphanet lookup <term-or-id>`** — schlägt einen Orphanet-Eintrag nach
  (ORPHA-Code oder Suchbegriff) und liefert Name, ORPHA-Code, ggf. assoziierte
  Gene/OMIM-Querverweise.

Eigenschaften:
- Nutzt den **zentralen httpx-Client** aus CLI-01.
- **HPO-Listen-Serialisierung** in einer reinen Funktion: die `<HPO...>`-Argumente
  werden in das von der Monarch-API erwartete Format gebracht (z. B. komma-
  getrennt / wiederholte Query-Params). Diese Funktion ist ohne HTTP testbar.
- **Response-Parsing** in reinen Funktionen (Monarch-JSON → Krankheits-Records;
  Orphanet/Orphadata-Response → Eintrags-Records), defensiv gegen fehlende Felder.
- Jede Abfrage schreibt einen **History-Eintrag** (source `monarch`/`orphanet`).
- Ausgabe über `output.py` (Tabelle/JSONL) mit Quellen-IDs (MONDO/OMIM/ORPHA).

## Files
```
cli/rca/sources/__init__.py    (NEU, falls noch nicht vorhanden)
cli/rca/sources/graph.py       (NEU)
cli/rca/main.py                (erweitert: Registrierung der graph-Gruppe)
cli/tests/test_graph.py        (NEU)
```

## Reality Check (Pflicht — vor Promotion nach `2.ready/`)
- [x] **Files in `Scope`/`Files`**: `graph.py` und der Test sind NEU.
      `cli/rca/sources/__init__.py` ggf. aus CLI-02/03 schon da — defensiv mit
      aufgeführt. `main.py` existiert nach CLI-01 und wird erweitert.
- [x] **`depends_on`-IDs**: CLI-01 liefert Client, History, Output, Registry. Nutzbar
      sobald CLI-01 in `backlog/3.done/`. Unabhängig von CLI-02/03.
- [x] **Externe Voraussetzungen**: Monarch- und Orphanet-/Orphadata-REST sind ohne
      Auth nutzbar (`docs/architektur.md`, Schnittstellen-Tabelle: „keine" /
      „teils Registrierung"). Kein Pflicht-Secret → kein `stop_after`.
- [x] **Tooling**: `ruff`/`pytest`; Tests injizieren `httpx.MockTransport` — keine
      echten Monarch-/Orphanet-Calls.

## Acceptance
- [ ] `ruff check cli/` ohne Findings.
- [ ] `python -m py_compile cli/rca/sources/graph.py cli/tests/test_graph.py`
      ohne Fehler.
- [ ] `pytest cli/tests/test_graph.py` grün — alle HTTP-Calls über
      `httpx.MockTransport` (kein echter Netzwerk-Call).
- [ ] CLI startbar: `rca monarch --help` (listet `diseases-by-phenotypes`,
      `gene-to-diseases`) und `rca orphanet --help` (listet `lookup`).
- [ ] **HPO-Listen-Serialisierung getestet:** mehrere HPO-IDs (`HP:0001250
      HP:0001263`) werden in das erwartete Query-Format überführt (reine Funktion,
      ohne HTTP).
- [ ] **Response-Parsing getestet:** aus einer gemockten Monarch-Response werden
      Krankheits-Records (ID + Name) extrahiert; aus einer gemockten
      Orphanet-Response der Eintrag.
- [ ] **History-Eintrag getestet:** nach einer (gemockten) `diseases-by-phenotypes`-
      Abfrage existiert ein History-Eintrag mit `source` `monarch`.
- [ ] **Negativ-Check:** keine eigene HTTP-Implementierung —
      `! grep -nE 'httpx\.(get|post|Client\()' cli/rca/sources/graph.py`.

## Out of scope
- **HPO-ID-Validierung** (Format `HP:nnnnnnn` ablehnen bei Müll): zentral in CLI-05
  (DDx), wo HPO-Eingaben validiert werden. CLI-04 serialisiert nur. Falls beide eine
  Validierung brauchen, lebt sie an **einer** Stelle (Single source of truth) — bei
  CLI-04-Implementierung prüfen, ob CLI-05 schon eine Helper-Funktion bereitstellt;
  sonst nur serialisieren und Validierung CLI-05 überlassen.
- **DDx-Ranking-Tools** (PubCaseFinder/Phen2Gene): CLI-05.
- **Andere Quellen** (Literatur, Variant): CLI-02/03.
- **Compound-Verknüpfung:** CLI-06.

## Notes
- **Monarch-API-Form prüfen.** Die Monarch-API hat sich über Versionen geändert
  (BioLink vs. neuere Endpunkte). Beim Bauen kurz die aktuelle Response-Form gegen
  ein **Fixture** festziehen; Parsing defensiv halten. Erkenntnis ggf. in
  `AGENTS.md` `## Notes` notieren.
- **Orphanet teils Registrierung.** `docs/architektur.md` markiert Orphanet/Orphadata
  als „teils Registrierung". Den frei zugänglichen REST-Pfad nutzen; falls ein Teil
  einen Key braucht, optional per Env — **nie** ein Pflicht-Secret einführen
  (sonst `stop_after`).
- **HPO-Format.** HPO-IDs haben die Form `HP:0000000`. Die Serialisierung verändert
  die IDs nicht, sie ordnet sie nur in das API-Query-Format.
