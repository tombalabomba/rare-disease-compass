---
id: CLI-03
title: Varianten-Quelle (ClinVar / gnomAD / MyVariant)
status: todo
depends_on: [CLI-01]
stop_after: false
epic: cli
commit_type: feat(cli)
---

# CLI-03 — Varianten-Quelle (ClinVar / gnomAD / MyVariant)

## Why
Bei genetisch verdächtigen seltenen Fällen ist die Frage „Ist diese Variante
pathogen, und wie selten ist sie?" zentral. MyVariant.info aggregiert genau das:
ClinVar-Klinische-Bedeutung und gnomAD-Allelfrequenz pro Variante. Claude Code
braucht einen knappen Befehl, der zu einer Variante (HGVS/rsID/Position) die
Pathogenität und Frequenz mit Quellen-IDs (RCV/RS) zurückgibt. Ohne dieses Ticket
fehlt dem System die Varianten-Bewertung neben der Genetik-Pipeline (Exomiser,
`genetics`-Epic).

## Scope
**`cli/rca/sources/variant.py`** — Typer-Subkommando-Gruppe, registriert über die
CLI-01-Registry. Befehle:

- **`rca variant lookup <variant>`** — fragt **MyVariant.info** ab (Endpoint
  `/v1/variant/<id>` bzw. die Query-API) und liefert kompakt:
  ClinVar-**klinische Bedeutung** (z. B. Pathogenic/Likely pathogenic/VUS/Benign),
  zugehörige RCV-/Variation-IDs, betroffenes Gen, und die **gnomAD-Allelfrequenz**
  (exome/genome, sofern vorhanden). Eingabe akzeptiert die von MyVariant
  unterstützten Kennungen (HGVS, rsID). Optionen: `--fields` (Feld-Auswahl
  durchreichen), `--json`.
- **`rca variant clinvar <variant>`** — fokussiert auf die ClinVar-Sicht: klinische
  Signifikanz, Review-Status, Condition(s)/Phänotyp, RCV-IDs. Ebenfalls über
  MyVariant.info (ClinVar-Feldsatz) oder direkt über die ClinVar-Quelle, mit denselben
  Output-/History-Konventionen.

Eigenschaften:
- Nutzt den **zentralen httpx-Client** aus CLI-01 — keine eigene HTTP-Schicht.
- **Parsing** der MyVariant-/ClinVar-Antwort in **reinen Funktionen**: extrahiere
  Pathogenität (`clinvar.rcv.clinical_significance` o. ä.) und Frequenz
  (`gnomad_exome.af.af` / `gnomad_genome.af.af` o. ä.) robust, auch wenn Felder
  fehlen (defensiv, kein Crash bei VUS ohne Frequenz).
- Optionaler API-Key (MyVariant erlaubt anonymen Zugriff) — wenn ein Key per Env
  vorhanden ist, anhängen; sonst ohne.
- Jede Abfrage schreibt einen **History-Eintrag** (source `variant`/`clinvar`).
- Ausgabe über `output.py` (Tabelle/JSONL) mit Quellen-IDs (Variant-ID, RCV, rsID).

## Files
```
cli/rca/sources/__init__.py    (NEU, falls CLI-02 es nicht schon anlegte)
cli/rca/sources/variant.py     (NEU)
cli/rca/main.py                (erweitert: Registrierung der variant-Gruppe)
cli/tests/test_variant.py      (NEU)
```

## Reality Check (Pflicht — vor Promotion nach `2.ready/`)
- [x] **Files in `Scope`/`Files`**: `variant.py` und der Test sind NEU.
      `cli/rca/sources/` wird hier oder in CLI-02 angelegt (beide hängen nur an
      CLI-01, daher das `__init__.py` defensiv mit aufführen). `main.py` existiert
      nach CLI-01 und wird erweitert.
- [x] **`depends_on`-IDs**: CLI-01 liefert Client, History, Output, Registry. Nutzbar
      sobald CLI-01 in `backlog/3.done/`. **Nicht** abhängig von CLI-02.
- [x] **Externe Voraussetzungen**: MyVariant.info ist ohne Auth nutzbar; API-Key
      optional. Kein Pflicht-Secret → kein `stop_after`.
- [x] **Tooling**: `ruff`/`pytest`; Tests injizieren `httpx.MockTransport` — keine
      echten MyVariant-/ClinVar-Calls.

## Acceptance
- [ ] `ruff check cli/` ohne Findings.
- [ ] `python -m py_compile cli/rca/sources/variant.py cli/tests/test_variant.py`
      ohne Fehler.
- [ ] `pytest cli/tests/test_variant.py` grün — alle HTTP-Calls über
      `httpx.MockTransport` (kein echter Netzwerk-Call).
- [ ] CLI startbar: `rca variant --help` listet `lookup` und `clinvar`.
- [ ] **Parsing von Pathogenität getestet:** aus einer gemockten MyVariant-Response
      wird die ClinVar-Signifikanz korrekt extrahiert (inkl. RCV-ID).
- [ ] **Parsing von Frequenz getestet:** die gnomAD-Allelfrequenz wird korrekt
      extrahiert; fehlt sie in der Response, liefert die Funktion einen definierten
      Leerwert statt eines Crashes.
- [ ] **History-Eintrag getestet:** nach einem (gemockten) `lookup` existiert ein
      History-Eintrag mit `source` `variant`.
- [ ] **Negativ-Check:** keine eigene HTTP-Implementierung —
      `! grep -nE 'httpx\.(get|post|Client\()' cli/rca/sources/variant.py`.

## Out of scope
- **VCF-Verarbeitung / lokale Genom-Priorisierung:** das ist Exomiser
  (`genetics`-Epic, GEN-01…03), nicht diese CLI. Hier nur Einzelvarianten-Lookup
  über öffentliche Aggregatoren.
- **Andere Quellen** (Literatur, Graph, DDx): CLI-02/04/05.
- **Compound-Verknüpfung** (Variante ∩ Literatur ∩ Krankheit): CLI-06.

## Notes
- **Felder defensiv lesen.** MyVariant-Responses sind tief verschachtelt und je nach
  Variante unterschiedlich besetzt. Parsing-Funktionen müssen fehlende
  Schlüssel tolerieren (VUS ohne Frequenz, Variante ohne ClinVar-Eintrag).
- **Keine Diagnose-Sprache.** Die CLI gibt nur Datenbank-Fakten (Signifikanz,
  Frequenz, Quellen-ID) aus — keine Interpretation. Bewertung übernimmt Claude Code,
  klinische Einordnung der Arzt (`docs/security.md`, `config/assistant-instructions.md`
  aus KB-04).
- **Mehrere Frequenz-Quellen.** gnomAD liefert exome/genome getrennt; beide ausgeben,
  wenn vorhanden, statt stillschweigend eine zu wählen.
