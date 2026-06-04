---
id: GEN-03
title: Exomiser-Output → Fallakten-Markdown-Konverter
status: done
depends_on: [GEN-01, KB-01]
stop_after: false
epic: genetics
commit_type: feat(genetics)
---

# GEN-03 — Exomiser-Output → Fallakten-Markdown-Konverter

## Why
Exomiser produziert maschinen-orientierten Output (TSV/JSON mit gerankten Genen,
Varianten, Krankheiten). Niemand pflegt das von Hand in die Fallakte. GEN-03 parst
den Output und erzeugt **genau** die Sektion „Genetik-Zusammenfassung", die KB-01 im
Fallakten-Template leer gelassen hat — als kuratierte Top-Kandidaten-Tabelle mit
Disclaimer. Entscheidend für den Datenschutz: Es darf **nur** das kuratierte
Ergebnis in die Akte, **keine** vollständige Variantenliste und **keine** Rohgenom-
Zeilen (`docs/architektur.md`: „nur das Ergebnis fließt in die Akte"). Damit wird
das sensibelste Datum (Rohgenom) von der geteilten Fallakte ferngehalten.

## Scope
Code + Tests + synthetische Fixtures:

**1. `genetics/exomiser_to_casefile.py`** (Python 3.11, `ruff`-clean):
- **Parser:** liest einen Exomiser-Ergebnis-Output. Primär TSV (z. B. die
  `*.genes.tsv`/`*.variants.tsv`-Struktur), optional JSON. Funktionen klar getrennt:
  `parse_exomiser_tsv(text) -> list[Candidate]` (und/oder `parse_exomiser_json`).
  `Candidate` ist ein `dataclass`/`TypedDict` mit den kuratierten Feldern:
  `gene`, `variant`, `clinvar_significance`, `frequency`, `phenotype_score`, `source`.
- **Ranking/Filter:** nimmt nur die Top-N Kandidaten (Default z. B. 10, parametrierbar),
  sortiert nach Phänotyp-/Exomiser-Score absteigend.
- **Markdown-Erzeugung:** `render_genetics_section(candidates) -> str` erzeugt die
  Sektion im **Format des KB-01-Templates** — Überschrift `## Genetik-Zusammenfassung`,
  eine Tabelle mit den Spalten `Gen | Variante | ClinVar-Bedeutung | Häufigkeit |
  Phänotyp-Score | Quelle`, plus ein **medizinischer Disclaimer** (deutsch: keine
  Diagnose, computergestützte Priorisierung, ärztliche Bewertung nötig, Quelle
  Exomiser + zugrundeliegende DBs).
- **CLI:** `python genetics/exomiser_to_casefile.py <ergebnis-pfad> [--top N] [--format tsv|json]`
  gibt das Markdown auf stdout aus (zum Einfügen in die Akte). Liest **nur** den
  übergebenen Pfad, schreibt selbst keine Patientendatei.

**2. `genetics/tests/test_exomiser_to_casefile.py`** (`pytest`):
- testet `parse_exomiser_tsv` gegen die synthetische Fixture (richtige Anzahl
  Kandidaten, Felder korrekt gemappt),
- testet `render_genetics_section` (Überschrift `## Genetik-Zusammenfassung` und alle
  Tabellenspalten vorhanden, Disclaimer vorhanden, Top-N-Begrenzung greift),
- **Negativ-Test (Datenschutz):** das erzeugte Markdown enthält **keine** Rohgenom-/
  Roh-VCF-Zeilen — kein VCF-Header (`##fileformat=VCF`), keine `CHROM POS ID REF ALT`-
  Zeile, keine vollständige Variantenliste über die Top-N hinaus. Nur kuratierte
  Kandidaten.

**3. `genetics/tests/fixtures/exomiser_result.tsv.sample`** — ein **winziger,
synthetischer** Exomiser-TSV-Schnipsel (erfundene Gene/Varianten/Scores, plausibel
formatiert). Dateiname endet auf `.tsv.sample` (nicht `.tsv`), damit `.gitignore`
ihn nicht sperrt und keine Verwechslung mit echtem Output entsteht.

## Files
```
genetics/exomiser_to_casefile.py                 (NEU)
genetics/tests/test_exomiser_to_casefile.py      (NEU)
genetics/tests/fixtures/exomiser_result.tsv.sample (NEU, synthetisch)
genetics/tests/__init__.py                       (NEU, leer — Paket-Marker für pytest)
```

## Reality Check (Pflicht — vor Promotion nach `2.ready/`)
- [x] **Files in `Scope`/`Files`**: alle NEU. `genetics/` entsteht in GEN-01;
      `genetics/tests/fixtures/` wird hier neu angelegt.
- [x] **`depends_on`-IDs**: `KB-01` definiert die Ziel-Sektion
      `## Genetik-Zusammenfassung` (in `docs/case-file-TEMPLATE.md`), die dieses
      Skript erzeugen muss — die Überschrift ist verifizierbar gegen KB-01.
      `GEN-01` liefert Output-Format-Kontext (Compose/Templates). GEN-03 zieht der
      Loop erst, wenn **beide** in `done/` liegen.
- [x] **Externe Voraussetzungen**: **keine** — GEN-03 braucht keinen echten
      Exomiser-Lauf und keine Referenzdaten. Getestet wird gegen die synthetische
      Fixture. `docker` ist hier irrelevant.
- [x] **Tooling**: `ruff` und `pytest` (CLAUDE.md-Standard). Beide laufen offline
      gegen die Fixture. Falls lokal nicht installiert: per `pip` nachziehen
      (Installationsschritt, kein Blocker).
- [x] **`.gitignore`-Fixture-Pfad verifiziert**: `git check-ignore` erfasst
      `genetics/tests/fixtures/exomiser_result.tsv.sample` **nicht** (geprüft);
      `*.vcf` und `exomiser-results/` bleiben gesperrt. Daher ist die synthetische
      Fixture tracked, echte Outputs aber weiterhin geblockt.

## Acceptance
- [x] `ruff check genetics/` grün (Lint sauber für alle neuen Python-Dateien).
- [x] `pytest genetics/tests/` grün — Parsing **und** Markdown-Erzeugung getestet.
- [x] Erzeugte Sektion passt zu den Überschriften aus KB-01: die von
      `render_genetics_section` produzierte Überschrift ist exakt
      `## Genetik-Zusammenfassung` und matcht die Sektion in
      `docs/case-file-TEMPLATE.md`. Maschinell (sobald KB-01 done):
      `grep -q '## Genetik-Zusammenfassung' docs/case-file-TEMPLATE.md` und ein Test
      prüft denselben String im Konverter-Output.
- [x] Tabellen-Spalten vorhanden im erzeugten Markdown (im Test geprüft):
      `Gen | Variante | ClinVar-Bedeutung | Häufigkeit | Phänotyp-Score | Quelle`.
- [x] Disclaimer vorhanden im erzeugten Markdown (im Test geprüft, deutscher
      Hinweis-Text „keine Diagnose"/„ärztlich" o. Ä.).
- [x] **Negativ-Check (keine Rohgenom-Zeilen):** das erzeugte Markdown enthält
      keinen VCF-Header und keine Roh-Variantenzeile — im Test asserted:
      kein `##fileformat=VCF`, kein `#CHROM\tPOS\tID\tREF\tALT`, nur die kuratierten
      Top-N-Kandidaten. Über die Top-N hinaus erscheinen keine weiteren Varianten.
- [x] **Negativ-Check (Datenschutz Fixture):** `exomiser_result.tsv.sample` ist
      synthetisch — keine realen Patientendaten, keine echte VCF, kein
      Geburtsdatum-Muster `DD.MM.YYYY`:
      `! grep -qE '[0-9]{2}\.[0-9]{2}\.[0-9]{4}' genetics/tests/fixtures/exomiser_result.tsv.sample`
- [x] Fixture-Pfad ist nicht gitignored (tracked):
      `! git check-ignore -q genetics/tests/fixtures/exomiser_result.tsv.sample`

## Out of scope
- **Exomiser-Lauf selbst:** GEN-02 erzeugt den Output; GEN-03 konsumiert ihn nur.
- **Einfügen in die echte Akte:** GEN-03 gibt das Markdown auf stdout aus. Das
  tatsächliche Einsetzen in eine reale (lokale, gitignored) Fallakte ist ein
  manueller Schritt des Kurators — GEN-03 schreibt keine Patientendatei.
- **HPO-/ClinVar-Validierung gegen Live-DBs:** GEN-03 übernimmt die Werte aus dem
  Exomiser-Output, validiert sie nicht gegen externe APIs (das ist `epic-cli`).
- **Vollständige Variantenliste:** bewusst **nicht** ausgegeben — nur kuratierte
  Top-Kandidaten (Datensparsamkeit).

## Notes
- **Single source of truth für die Ziel-Sektion:** Die Überschrift
  `## Genetik-Zusammenfassung` stammt aus KB-01 (`docs/case-file-TEMPLATE.md`). Bei
  Implementierung dort gegenprüfen, nicht raten — der Konverter muss den **exakt**
  gleichen String erzeugen, sonst landet die Sektion nicht an der richtigen Stelle.
- **Fixture-Namenskonvention:** Fixtures enden auf `.tsv.sample` (nicht `.tsv`),
  liegen unter `genetics/tests/fixtures/`. `git check-ignore` erfasst diesen Pfad
  nicht — verifiziert. Echte Exomiser-Outputs (`*.tsv` in `exomiser-results/`)
  bleiben durch `.gitignore` gesperrt. Niemals eine echte `.vcf`/echten Output als
  Fixture verwenden.
- **Disclaimer ist Pflicht.** Die erzeugte Sektion enthält immer den medizinischen
  Hinweis: computergestützte Priorisierung, keine Diagnose, ärztliche Bewertung
  nötig, Quelle Exomiser + zugrundeliegende Datenbanken. Konsistent mit der
  Quellenpflicht/dem Disclaimer-Prinzip des Agenten (`epic-knowledge`, KB-04).
- **Kein Netzwerk, kein Container in den Tests.** GEN-03 ist reine Parsing-/Render-
  Logik gegen lokale Fixtures — Tests laufen offline und deterministisch.
