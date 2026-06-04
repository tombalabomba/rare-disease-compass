# Epic: Wissensbasis (`epic-knowledge`)

**Status:** geplant
**Slug:** `knowledge`
**Hängt ab von:** `epic-infra` (Docker-Stack + LibreChat-RAG-API müssen laufen,
bevor real ingestet wird)

## Ziel

Die strukturierte, HPO-codierte, **pseudonymisierte** Fallakte und alles, was sie
in den Assistenten bringt. Konkret:

1. ein **Schema/Template** für die Fallakte, das den Verlauf, die Symptome als
   HPO-Begriffe und die Befunde so erfasst, dass sie der gemeinsame Verbindungs-
   schlüssel zu allen Datenbanken sind (HPO-IDs),
2. eine **Datenschutz-Schranke** (PII-Guard), die jede Akte vor Verarbeitung auf
   Klarnamen/Geburtsdaten/Kontaktdaten prüft,
3. die **RAG-Ingestion**, die die geprüfte Akte chunked und idempotent in die
   LibreChat-Wissensbasis lädt,
4. der **System-Prompt** des Agenten, der Rolle, Quellenpflicht, Disclaimer und
   Arzttermin-Fragen festlegt.

Ohne dieses Epic gibt es nichts, worüber der Assistent recherchieren kann: Die
Fallakte ist die einzige private Datenquelle, und HPO-IDs sind der Schlüssel,
ohne den `epic-mcp` (Monarch/Orphanet/PubCaseFinder) und `epic-genetics`
(Exomiser) nicht greifen.

## Defaults & Entscheidungen

- **Format der Fallakte:** ein einzelnes Markdown-File. Versionierbar, diff-bar,
  menschenlesbar, und LibreChat-RAG kann es direkt chunken. Kein YAML-Frontmatter
  mit Patientendaten, keine DB — Single source of truth ist die Markdown-Akte.
- **HPO als Verbindungsschlüssel:** Symptome werden **immer** als HPO-Begriffe mit
  HPO-ID notiert (Tabelle `Symptom | HPO-ID | seit wann`). Freitext-Symptome ohne
  HPO-ID sind erlaubt, gelten aber als „noch nicht codiert" und sind kein
  Datenbank-Anker.
- **Pseudonymisierung ist Pflicht, nicht optional:** Stammdaten enthalten nur
  Initialen, Alter (Jahre, optional Monat-Jahr), Geschlecht. Kein Klarname, kein
  exaktes Geburtsdatum, keine Kontaktdaten. Durchgesetzt durch KB-02 (PII-Guard).
- **Genetik-Sektion bleibt im Template leer:** Das Template enthält die Sektion
  „Genetik-Zusammenfassung", füllt sie aber nicht — das macht später `epic-genetics`
  (GEN-03) mit dem Exomiser-Ergebnis. Hier nur die Struktur.
- **Ingestion ruft den Guard auf:** KB-03 ruft vor jedem Upload KB-02 und bricht
  bei einem PII-Fund ab (Defense-in-Depth: Guard ist auch pre-commit-Hook UND
  Laufzeit-Schranke der Ingestion).
- **Idempotenz:** Re-Upload derselben Akte aktualisiert die Chunks statt zu
  duplizieren (stabile Quelle/Datum-Metadaten als Dedup-Schlüssel).
- **Synthetische Fixtures überall:** Jedes Beispiel und jeder Test arbeitet mit
  einem **erfundenen** Kind. Niemals reale Initialen oder Daten — auch nicht als
  „Platzhalter". Siehe `docs/security.md`.

## Modul-Karte

```
docs/case-file-TEMPLATE.md          ← KB-01  Schema der Fallakte (HPO-codiert)
docs/fixtures/case-file-FIXTURE.md  ← KB-01  synthetisches Beispiel-Kind
tools/pii_guard.py                  ← KB-02  PII-/Pseudonymisierungs-Schranke
tools/tests/test_pii_guard.py       ← KB-02  Tests (clean + Leck-Fixture)
tools/ingest_case_file.py           ← KB-03  RAG-Ingestion (ruft KB-02 auf)
docs/ingestion-guide.md             ← KB-03  Betreiber-Anleitung Ingestion
config/system-prompt.md             ← KB-04  Agent-Instruktionen / Rolle
```

Datenfluss innerhalb des Epics:
`KB-01 (Akte) → KB-02 (prüft) → KB-03 (lädt geprüfte Akte in RAG)`.
`KB-04` ist orthogonal (Agent-Verhalten) und hat keine Dependency.

## Tickets

| ID | Titel | depends_on | commit_type |
|---|---|---|---|
| KB-01 | Fallakten-Schema/Template (HPO-codiert) | — | `feat(knowledge)` |
| KB-02 | Pseudonymisierungs- & PII-Validierungs-Skript | KB-01 | `feat(knowledge)` |
| KB-03 | RAG-Ingestion-Skript + Guide | KB-01, INF-03 | `feat(knowledge)` |
| KB-04 | System-Prompt / Agent-Instruktionen | — | `feat(knowledge)` |

**Hinweis zu KB-03:** `INF-03` (LibreChat-RAG-API erreichbar) ist eine Dependency
aus `epic-infra`. Die Chunking-/Metadaten-Logik und der Guard-Aufruf sind mit
gemocktem HTTP voll testbar; der **echte** Upload gegen den Server-Endpoint ist
ein manueller Schritt, sobald `epic-infra` steht (siehe KB-03 `## Notes`).
