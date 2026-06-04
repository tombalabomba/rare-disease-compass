# Epic: Genetik (`epic-genetics`)

**Status:** geplant
**Slug:** `genetics`
**Hängt ab von:** `epic-knowledge` (KB-01 liefert das Fallakten-Template, dessen
Sektion „Genetik-Zusammenfassung" GEN-03 befüllt). Kein Hard-Dependency auf
`epic-infra` — Exomiser läuft **lokal**, nicht auf dem Server.

## Ziel

Die Genetik-Auswertung des Falls — **datensparsam und vollständig lokal**. Eine
VCF-Datei (das Rohgenom des Kindes) plus die HPO-Symptome aus der Fallakte gehen
in **Exomiser**, einen lokal als Docker-Container laufenden Java-Priorisierer.
Exomiser ranked die wahrscheinlich krankheitsverursachenden Varianten, Gene und
Krankheiten. **Nur das kuratierte Ergebnis** (keine Rohdaten, keine vollständigen
Variantenlisten) fließt anschließend als Markdown in die Sektion
„Genetik-Zusammenfassung" der Fallakte.

Der zentrale Datenschutz-Punkt (`docs/architektur.md`, `docs/security.md`): Das
Rohgenom (VCF) **verlässt den lokalen Rechner nie**. Es wird nicht ins Repo
committet (`.gitignore` sperrt `*.vcf`, `exomiser-results/`), nicht zum Server
übertragen und nicht an die Anthropic-API geschickt. Auf dem Server landet
ausschließlich die abgeleitete, gerankte Ergebnis-Zusammenfassung.

Drei Bausteine:

1. **GEN-01** — Exomiser lokal lauffähig machen: Docker-Compose für den lokalen
   Lauf, Konfig-Templates (`application.properties`, Analysis-YAML mit
   HPO-Platzhaltern) und eine Doku, welche großen Referenzdaten wo herunterzuladen
   sind und dass alles lokal bleibt.
2. **GEN-02** — ein Wrapper-Skript, das VCF-Pfad + HPO-Liste entgegennimmt, daraus
   ein Analysis-YAML generiert, den Container startet und das Ergebnis unter
   `exomiser-results/` (gitignored) ablegt. Mit harter Input-Validierung.
3. **GEN-03** — ein Konverter, der den Exomiser-Output (TSV/JSON) parst und daraus
   die Genetik-Sektion im Format des Fallakten-Templates (KB-01) erzeugt — nur
   kuratierte Top-Kandidaten, mit Disclaimer, **ohne** Rohgenom-Zeilen.

## Defaults & Entscheidungen

- **Exomiser läuft lokal, nicht auf dem Server.** Das ist die Defense-in-Depth für
  das sensibelste Datum (Rohgenom). Das lokale Compose-File (`docker-compose.exomiser.yml`)
  ist bewusst **getrennt** vom Server-Compose-Stack (`epic-infra`) und wird nie
  zusammen mit ihm deployed.
- **VCF und Ergebnisse sind gitignored.** `.gitignore` sperrt `*.vcf`, `*.vcf.gz`,
  `*.bam`, `*.cram`, `*.fastq*`, `*.ped` und `exomiser-results/`. Das Wrapper-Skript
  (GEN-02) schreibt **ausschließlich** nach `exomiser-results/` — nie in ein
  getracktes Verzeichnis.
- **Synthetische Fixtures, niemals echte Daten.** Tests arbeiten mit winzigen,
  **erfundenen** VCF-/Ergebnis-Schnipseln. Damit `.gitignore` sie nicht sperrt,
  enden Fixture-Dateinamen **nicht** auf `.vcf`/`.tsv`, sondern auf `.vcf.sample` /
  `.tsv.sample` und liegen unter `genetics/tests/fixtures/` (verifiziert: dieser
  Pfad wird von `git check-ignore` nicht erfasst). Alternativ stehen Mini-Schnipsel
  als String direkt im Testmodul.
- **Referenzdaten = manueller Schritt.** Exomiser braucht große Datenbank-Releases
  (mehrere GB: Phenotype-DB, Variant-DB pro Assembly hg19/hg38, optional CADD/REMM).
  Diese werden **nicht** versioniert und **nicht** automatisch geladen — die Doku
  (GEN-01) beschreibt den Download, der Mensch führt ihn lokal aus.
- **HPO als Verbindungsschlüssel.** Die HPO-IDs aus der Fallakte (`Symptom | HPO-ID`)
  sind exakt der Input für Exomiser (Analysis-YAML `hpoIds`). Format strikt
  `HP:nnnnnnn` (Präfix `HP:`, sieben Ziffern) — identisch zu KB-01 und `epic-mcp`.
- **Nur kuratiertes Ergebnis in die Akte.** GEN-03 gibt **keine** vollständige
  Variantenliste und **keine** Rohgenom-Zeilen aus, nur die gerankten Top-Kandidaten
  (Gen, Variante, ClinVar-Bedeutung, Häufigkeit, Phänotyp-Score, Quelle) plus einen
  medizinischen Disclaimer.
- **Sprache:** Doku/Tickets/Commit-Bodies deutsch, Code/Tool-Namen/Config-Keys
  englisch (CLAUDE.md).
- **Python-Tooling:** `ruff` (lint+format), `pytest`. Shell: `bash`,
  `shellcheck`-clean, `set -euo pipefail`.

## Modul-Karte

```
genetics/
├── docker-compose.exomiser.yml         ← GEN-01  lokaler Exomiser-Lauf (Container)
├── config/
│   ├── application.properties.template ← GEN-01  Pfade zu Referenzdaten, Output-Format
│   └── analysis.template.yml           ← GEN-01  Analysis-YAML mit HPO-Platzhaltern
├── run_exomiser.sh                     ← GEN-02  VCF + HPO → Analysis-YAML → Container → Ergebnis
├── exomiser_to_casefile.py             ← GEN-03  Exomiser-Output → Genetik-Markdown (KB-01-Format)
└── tests/
    ├── test_exomiser_to_casefile.py    ← GEN-03  Parsing + Markdown-Erzeugung (synthetisch)
    └── fixtures/
        ├── exomiser_result.tsv.sample  ← GEN-03  synthetischer Exomiser-TSV-Output
        └── tiny.vcf.sample             ← GEN-02/03  synthetischer VCF-Schnipsel (kein echter Mensch)

docs/genetics-setup.md                  ← GEN-01  welche Referenzdaten, wo, wie groß, alles lokal

exomiser-results/                       ← Laufzeit-Output (gitignored, nie getracked)
```

Datenfluss innerhalb des Epics:
`GEN-01 (Exomiser lauffähig + Templates) → GEN-02 (VCF+HPO → Lauf → Ergebnis) → GEN-03 (Ergebnis → Akten-Markdown)`.
GEN-03 hängt zusätzlich an `KB-01` (Fallakten-Template, dessen Sektionen die
erzeugte Genetik-Sektion treffen muss).

## Ticket-Liste (Baureihenfolge über `depends_on`)

| ID | Titel | depends_on | commit_type |
|---|---|---|---|
| GEN-01 | Exomiser-Runner (Docker, lokal) + Konfig-Templates + Daten-Doku | `[]` | `feat(genetics)` |
| GEN-02 | VCF + HPO → Exomiser Wrapper-Skript | `[GEN-01]` | `feat(genetics)` |
| GEN-03 | Exomiser-Output → Fallakten-Markdown-Konverter | `[GEN-01, KB-01]` | `feat(genetics)` |

**Reihenfolge-Logik:**
- GEN-01 ist die Wurzel (kein Dependency) — Container-Definition, Konfig-Templates,
  Daten-Doku. Sofort baubar, der eigentliche Referenzdaten-Download bleibt manuell.
- GEN-02 baut auf den Templates aus GEN-01 auf (generiert das Analysis-YAML aus
  `analysis.template.yml`, startet das in GEN-01 definierte Compose-Setup).
- GEN-03 braucht GEN-01 (Output-Format/Container-Setup als Kontext) und `KB-01`
  (Ziel-Sektionen der Fallakte). GEN-03 ist gegen einen **synthetischen** Beispiel-
  Output testbar und braucht **keinen** echten Exomiser-Lauf.

**Externe Abhängigkeit aus `epic-knowledge`:**
- `KB-01` — Fallakten-Template (`docs/case-file-TEMPLATE.md`) mit der Sektion
  „Genetik-Zusammenfassung". Solange KB-01 nicht in einem `done/`-Ordner liegt,
  zieht der Loop GEN-03 nicht. GEN-01 und GEN-02 sind davon unberührt.

## Smoke-Test (Mensch, am Epic-Ende)

Ein **echter** Exomiser-Lauf (Container startet, lädt mehrere GB Referenzdaten,
wertet eine reale VCF gegen die HPO-Liste aus, GEN-02 schreibt das Ergebnis,
GEN-03 erzeugt die Akten-Sektion) ist **kein** Teil der maschinellen Acceptance —
er braucht die lokal heruntergeladenen Referenzdaten und eine echte (lokale,
gitignored) VCF. Dieser End-to-End-Durchlauf gehört in `SMOKE-TEST.md` und macht
der Mensch lokal, sobald die Referenzdaten liegen. Die maschinelle Acceptance der
Tickets prüft Config-Validität, Skript-Korrektheit und Parsing/Markdown gegen
synthetische Fixtures.
