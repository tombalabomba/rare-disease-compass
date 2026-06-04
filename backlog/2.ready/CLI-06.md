---
id: CLI-06
title: Compound Queries + Claude-Nutzungs-Guide
status: todo
depends_on: [CLI-02, CLI-03, CLI-04, CLI-05]
stop_after: false
epic: cli
commit_type: feat(cli)
---

# CLI-06 — Compound Queries + Claude-Nutzungs-Guide

## Why
Der eigentliche Mehrwert gegenüber rohen APIs sind **quellenübergreifende**
Abfragen: aus einem Phänotyp-Profil in einem Schritt DDx (PubCaseFinder/Phen2Gene),
Krankheits-Graph (Monarch/Orphanet) und Literatur (PubMed/Europe PMC) kombinieren,
Duplikate über Quellen hinweg zusammenführen und das Ergebnis ranken
(`docs/architektur.md`: „Compound Queries"). Dazu braucht Claude Code einen Guide,
welcher Befehl für welche Frage gedacht ist. Ohne dieses Ticket bleibt die
Kombinationslogik beim Modell hängen (mehr Token, weniger reproduzierbar) und es gibt
keine Anleitung, wie die CLIs zu nutzen sind.

## Scope
**1. `cli/rca/compound.py`** — Typer-Subkommando-Gruppe `compound`, registriert über
die CLI-01-Registry. Mindestens:

- **`rca compound phenotype-workup <HPO...>`** — orchestriert eine vollständige
  Phänotyp-Abklärung aus einer HPO-Liste:
  1. DDx: ruft die Funktionen hinter `pubcasefinder rank` und `phen2gene genes`
     (CLI-05) auf.
  2. Graph: ruft die Funktion hinter `monarch diseases-by-phenotypes` (CLI-04) auf.
  3. Literatur: optional eine PubMed-/Europe-PMC-Suche (CLI-02) zu den
     Top-Kandidaten-Krankheiten/-Genen.
  Danach: **Dedup** über Quellen hinweg (gleiche Krankheit über OMIM/ORPHA/MONDO-IDs
  zusammenführen, gleiches Gen über Symbol) und ein kombiniertes **Ranking**
  (z. B. Konsens-Score: in wievielen Quellen taucht ein Kandidat auf, plus dessen
  jeweiliger Rang). Optionen: `--limit`, `--with-literature/--no-literature`,
  `--json`.

Eigenschaften:
- **Wiederverwendung, keine Neu-Implementierung:** ruft die bestehenden reinen
  Funktionen aus `sources/ddx.py`, `sources/graph.py`, `sources/literature.py` auf.
  Kein zweiter HTTP-Pfad, keine Parsing-Duplikate (Single source of truth).
- **History-Nutzung:** schreibt einen eigenen Compound-Eintrag (source `compound`)
  **und** nutzt die History als Speicher — die zugrundeliegenden Quellen-Aufrufe
  protokollieren weiterhin ihre Einzel-Einträge. Die Dedup-/Rank-Funktionen sind
  rein und ohne HTTP testbar.
- HPO-Validierung über den CLI-05-Helper (kein Müll-Input).
- Ausgabe über `output.py` (Tabelle/JSONL) mit Quellen-IDs und Konsens-Info
  (welche Quellen einen Kandidaten stützen).

**2. `docs/cli-guide.md`** — deutscher Nutzungs-Guide für Claude Code:
- Tabelle „Frage → Befehl": welcher `rca`-Befehl für welche Recherche-Frage (Literatur,
  Varianten-Bewertung, Phänotyp→Krankheit, DDx, kombinierte Abklärung).
- **Alle Subkommandos** aus CLI-02…06 gelistet, jeweils mit einem **Beispielaufruf**
  und einer knappen Erklärung der Ausgabe.
- Hinweis auf die History (`rca history list/search`) als Recherche-Speicher.
- Hinweis: Ausgabe ist Recherche-Hilfe, **keine Diagnose**; Quellen-IDs immer
  mitführen (verweist auf `config/assistant-instructions.md` aus KB-04, sofern
  vorhanden).

**3. `cli/tests/test_compound.py`** — testet Dedup- und Ranking-Logik mit
**gemockten** Quellen-Funktionen (kein echter HTTP-Call; entweder die reinen
Funktionen mit Fixtures füttern oder die Quellen-Funktionen monkeypatchen). Prüft,
dass dieselbe Krankheit aus zwei Quellen zu **einem** Eintrag zusammengeführt und
nach Konsens/Rang sortiert wird.

## Files
```
cli/rca/compound.py            (NEU)
cli/rca/main.py                (erweitert: Registrierung der compound-Gruppe)
docs/cli-guide.md              (NEU)
cli/tests/test_compound.py     (NEU)
```

## Reality Check (Pflicht — vor Promotion nach `2.ready/`)
- [x] **Files in `Scope`/`Files`**: `compound.py`, `docs/cli-guide.md` und der Test
      sind NEU. `docs/` existiert (`ls docs` zeigt `architektur.md`, `security.md`).
      `main.py` existiert nach CLI-01 und wird erweitert.
- [x] **`depends_on`-IDs**: CLI-02 (literature), CLI-03 (variant), CLI-04 (graph),
      CLI-05 (ddx) müssen in `backlog/3.done/` liegen — Compound ruft deren reine
      Funktionen auf. CLI-01 ist transitiv über diese vorausgesetzt.
- [x] **Externe Voraussetzungen**: keine neuen — Compound nutzt nur bestehende
      Quellen + History. Keine Pflicht-Secrets → kein `stop_after`.
- [x] **Tooling**: `ruff`/`pytest`; Test mockt Quellen-Funktionen bzw. nutzt Fixtures.
      Falls ein End-to-End-Pfad doch HTTP berührt, via `httpx.MockTransport` — nie
      echte Calls.

## Acceptance
- [ ] `ruff check cli/` ohne Findings.
- [ ] `python -m py_compile cli/rca/compound.py cli/tests/test_compound.py`
      ohne Fehler.
- [ ] `pytest cli/tests/test_compound.py` grün — keine echten Netzwerk-Calls
      (Quellen-Funktionen gemockt bzw. `httpx.MockTransport`).
- [ ] CLI startbar: `rca compound --help` listet `phenotype-workup`.
- [ ] **Kombinations-/Dedup-Logik getestet:** zwei Quellen, die dieselbe Krankheit
      (gleiche OMIM/ORPHA-ID) liefern, ergeben **einen** Ergebnis-Eintrag; das Ranking
      ordnet Kandidaten mit Mehrfach-Quellen-Konsens nach oben.
- [ ] **History-Nutzung getestet:** ein `phenotype-workup` schreibt einen
      `compound`-History-Eintrag (in-memory).
- [ ] **`docs/cli-guide.md` listet alle Subkommandos mit Beispiel:** enthält je einen
      Beispielaufruf für `pubmed`, `europepmc`, `variant`, `monarch`, `orphanet`,
      `pubcasefinder`, `phen2gene`, `compound`. Prüfbar z. B.:
      `for c in pubmed europepmc variant monarch orphanet pubcasefinder phen2gene compound; do grep -q "rca $c" docs/cli-guide.md || { echo "fehlt: $c"; exit 1; }; done`
- [ ] **Negativ-Check (keine Parsing-Duplikate):** `compound.py` importiert die
      Quellen-Funktionen statt sie neu zu implementieren —
      `grep -qE 'from +(\.|rca\.)sources' cli/rca/compound.py` und
      `! grep -nE 'httpx\.(get|post|Client\()' cli/rca/compound.py`.

## Out of scope
- **Neue Quellen-Anbindungen:** Compound baut nur auf CLI-02…05 auf, fügt keine
  neue externe API hinzu.
- **Persistente Cross-Session-Rank-Modelle / ML-Scoring:** das Ranking ist ein
  transparenter, regelbasierter Konsens-Score, kein gelerntes Modell.
- **Assistenten-Persona/-Instruktionen** (keine Diagnose, Arztfragen): KB-04
  (`config/assistant-instructions.md`). `docs/cli-guide.md` verweist nur darauf.

## Notes
- **Dedup über IDs, nicht über Namen.** Krankheiten heißen je nach Quelle leicht
  anders; zusammenführen über die stabilen IDs (OMIM/ORPHA/MONDO), nicht über
  Freitext-Namen. Cross-Referenzen aus dem Graph (CLI-04) helfen beim Mapping.
- **Reine Funktionen wiederverwenden.** CLI-02…05 müssen ihre Kernlogik (Param-Bildung,
  Parsing, Request über den CLI-01-Client) so kapseln, dass Compound sie **ohne**
  die Typer-Befehlsschicht aufrufen kann. Falls eine Quelle das nicht hergibt, ist
  das ein kleiner Drive-by-Fix in der jeweiligen Quelle (≤ 10 Zeilen, in der
  Commit-Message vermerken) — größere Anpassung → neues Ticket.
- **Guide aktuell halten.** `docs/cli-guide.md` ist die zentrale Referenz für Claude
  Code. Wenn später Subkommandos dazukommen, gehört der Guide mit aktualisiert
  (Doku-Sync, `CLAUDE.md`).
