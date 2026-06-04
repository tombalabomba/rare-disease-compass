---
id: CLI-05
title: Differentialdiagnose-Quelle (PubCaseFinder + Phen2Gene)
status: done
depends_on: [CLI-01]
stop_after: false
epic: cli
commit_type: feat(cli)
---

# CLI-05 — Differentialdiagnose-Quelle (PubCaseFinder + Phen2Gene)

## Why
Das Herz eines Recherche-Assistenten für seltene Fälle ist die
Phänotyp-getriebene Differentialdiagnose: aus einer Liste beobachteter HPO-Symptome
eine gerankte Liste seltener Krankheiten (PubCaseFinder) und Kandidatengene
(Phen2Gene) ableiten. Beide Tools nehmen genau HPO-IDs als Eingabe. Claude Code
braucht dafür knappe Befehle mit sauberer HPO-Validierung, damit Tippfehler/Müll
nicht stillschweigend zu falschen API-Calls führen. Ohne dieses Ticket fehlt dem
System der DDx-Kern; mit ihm wird das Ranking in der History gespeichert.

## Scope
**`cli/rdc/sources/ddx.py`** — Typer-Subkommando-Gruppe, registriert über die
CLI-01-Registry. Befehle:

- **`rdc pubcasefinder rank <HPO...>`** — sendet die HPO-Liste an die
  PubCaseFinder-REST-API und liefert eine **gerankte Liste seltener Krankheiten**
  (Krankheit + ID wie OMIM/ORPHA + Score/Rang). Optionen: `--limit`, `--json`.
- **`rdc phen2gene genes <HPO...>`** — sendet die HPO-Liste an die Phen2Gene-API und
  liefert **gerankte Kandidatengene** (Gen-Symbol + Score/Rang). Optionen:
  `--limit`, `--json`.

Eigenschaften:
- **HPO-Validierung** in einer reinen Funktion: akzeptiert nur das Format
  `HP:nnnnnnn` (Präfix `HP:` + sieben Ziffern; großzügig genug für die offizielle
  HPO-ID-Form). Ungültige Eingaben (z. B. `HP:123`, `foo`, leer) werden **abgelehnt**
  mit klarer Fehlermeldung und Exit-Code ≠ 0 — **kein** API-Call mit Müll.
- Nutzt den **zentralen httpx-Client** aus CLI-01.
- **Request-Bildung** (HPO-Liste → API-Payload/Params) und **Ranking-Parsing**
  (Response → gerankte Records) in reinen, ohne HTTP testbaren Funktionen.
- Jede Abfrage schreibt einen **History-Eintrag** (source `pubcasefinder`/
  `phen2gene`), inklusive der eingegebenen HPO-Liste.
- Ausgabe über `output.py` (Tabelle/JSONL) mit Quellen-IDs (OMIM/ORPHA bzw.
  Gen-Symbol) und Rang/Score.

## Files
```
cli/rdc/sources/__init__.py    (NEU, falls noch nicht vorhanden)
cli/rdc/sources/ddx.py         (NEU)
cli/rdc/main.py                (erweitert: Registrierung der ddx-Gruppen)
cli/tests/test_ddx.py          (NEU)
```

## Reality Check (Pflicht — vor Promotion nach `2.ready/`)
- [x] **Files in `Scope`/`Files`**: `ddx.py` und der Test sind NEU.
      `cli/rdc/sources/__init__.py` ggf. aus CLI-02/03/04 schon vorhanden — defensiv
      mit aufgeführt. `main.py` existiert nach CLI-01 und wird erweitert.
- [x] **`depends_on`-IDs**: CLI-01 liefert Client, History, Output, Registry. Nutzbar
      sobald CLI-01 in `dev/backlog/3.done/`. Unabhängig von CLI-02/03/04.
- [x] **Externe Voraussetzungen**: PubCaseFinder und Phen2Gene sind ohne Auth über
      REST nutzbar (`docs/architektur.md`, Schnittstellen-Tabelle: „keine").
      Kein Pflicht-Secret → kein `stop_after`.
- [x] **Tooling**: `ruff`/`pytest`; Tests injizieren `httpx.MockTransport` — keine
      echten PubCaseFinder-/Phen2Gene-Calls.

## Acceptance
- [ ] `ruff check cli/` ohne Findings.
- [ ] `python -m py_compile cli/rdc/sources/ddx.py cli/tests/test_ddx.py`
      ohne Fehler.
- [ ] `pytest cli/tests/test_ddx.py` grün — alle HTTP-Calls über
      `httpx.MockTransport` (kein echter Netzwerk-Call).
- [ ] CLI startbar: `rdc pubcasefinder --help` (listet `rank`) und
      `rdc phen2gene --help` (listet `genes`).
- [ ] **HPO-Validierung lehnt Müll ab (Test):** gültige IDs (`HP:0001250`) werden
      akzeptiert; ungültige (`HP:123`, `0001250`, `foo`, `""`) werfen einen Fehler /
      führen zu Exit ≠ 0 und **keinem** HTTP-Call (MockTransport-Trefferzähler bleibt
      0).
- [ ] **Ranking-Parsing getestet:** aus einer gemockten PubCaseFinder-Response wird
      die gerankte Krankheitsliste extrahiert; aus einer gemockten
      Phen2Gene-Response die gerankte Genliste (jeweils mit Score/Rang).
- [ ] **History-Eintrag getestet:** nach einem (gemockten) `rank` existiert ein
      History-Eintrag mit `source` `pubcasefinder` und der HPO-Liste in den Params.
- [ ] **Negativ-Check:** keine eigene HTTP-Implementierung —
      `! grep -nE 'httpx\.(get|post|Client\()' cli/rdc/sources/ddx.py`.

## Out of scope
- **HPO-Term-Auflösung/-Vorschläge** (Symptomtext → HPO-ID): hier wird nur die
  ID-Form validiert, kein Term-Mapping. Ein Text→HPO-Lookup wäre ein eigenes Ticket.
- **Andere Quellen** (Literatur, Variant, Graph): CLI-02/03/04.
- **Compound-Verknüpfung** (DDx + Graph + Literatur kombiniert, Dedup, Re-Rank):
  CLI-06 — die nutzt diese Befehle, baut sie aber nicht neu.

## Notes
- **HPO-Validierung als gemeinsamer Helper.** Die `HP:nnnnnnn`-Validierung ist eine
  reine Funktion in `ddx.py`. Falls CLI-04 (Graph) sie ebenfalls braucht, lebt sie
  an **einer** Stelle (Single source of truth, `CLAUDE.md`) — beim Bauen prüfen, ob
  CLI-04 bereits eine Validierung anbietet; nicht doppelt implementieren.
- **Score vs. Rang.** Beide APIs liefern Reihenfolge; Score nur durchreichen, wenn
  vorhanden. Die Ausgabe behält die API-Reihenfolge bei (gerankt), `--limit`
  schneidet ab.
- **Kein Diagnose-Anspruch.** Die Ausgabe ist eine **Recherche-Hilfe**, keine
  Diagnose (`config/assistant-instructions.md` aus KB-04). Nur Daten + Quellen-IDs
  ausgeben, keine wertende Sprache.
