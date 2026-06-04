# Fallakten-Ordner — Konvention & Validierung

Wie ein Fall-Ordner aufgebaut sein muss, damit der Assistent ihn zuverlässig
nutzen kann — und wie man das maschinell prüft.

## Wichtig: Kein RAG, kein Server, keine Ingestion

Claude Code liest den Fall-Ordner **direkt** als Dateien. Es gibt **keinen
Server**, **keine RAG-Ingestion**, **keinen Vektor-Index** und **keine
Datenbank**. Der Ordner *ist* der Speicher — pseudonymisierte, HPO-codierte
Markdown-Dateien in einem lokalen oder geteilten Ordner (z. B. Dropbox). Wer
eine Ingestion oder einen Index erwartet: bewusst entfernt (Architektur-Pivot,
siehe [architektur.md](architektur.md)). Die einzige Verarbeitung ist diese
lokale, offline laufende Validierung.

## Die Ordner-Konvention

- Die Fallakte(n) heißen `case-file-<kürzel>.md` und liegen im Fall-Ordner.
- Schema und Pflichtsektionen sind im KB-01-Template definiert:
  [case-file-TEMPLATE.md](case-file-TEMPLATE.md). Das Template ist die *single
  source of truth* für die Sektionsnamen — nicht umbenennen.
- Das Projekt-Layout (wo der Fall-Ordner relativ zum Repo liegt) regelt
  `docs/project-layout.md` (SET-01).

**Pflichtsektionen** (exakte Überschriften):

- `## Stammdaten`
- `## Zeitleiste`
- `## Symptome`
- `## Befunde`
- `## Ausgeschlossenes`
- `## Genetik-Zusammenfassung`
- `## Offene Fragen`
- `## Medikation`

**HPO-IDs** in der Symptom-Tabelle müssen dem Format `HP:` + genau 7 Ziffern
folgen (z. B. `HP:0002028`). Das Skript prüft nur das **Format**, nicht ob die
ID im HPO-Vokabular existiert (Existenz-Lookup ist Sache des `cli`-Epics).

**PII** darf nicht vorkommen: kein Klarname, kein exaktes Geburtsdatum, keine
Kontaktdaten. Details in [security.md](security.md).

## Aufruf

```bash
python tools/validate_case_folder.py <ordner-pfad>
```

Das Skript sucht im Ordner die `case-file*.md`-Datei(en) und prüft sie. Der
Report listet alle Befunde; bei Befunden endet das Skript mit Exit-Code `!= 0`,
bei einem sauberen Ordner mit `0` (geeignet für CI / Pre-Commit).

## Befund-Arten

| Art | Bedeutung |
|---|---|
| `kein_ordner` | Der angegebene Pfad ist kein Verzeichnis. |
| `keine_akte` | Im Ordner liegt keine `case-file*.md`-Datei. |
| `fehlende_sektion` | Eine Pflichtsektion fehlt in der Akte. |
| `hpo_format` | Eine HPO-ID ist falsch formatiert (nicht `HP:` + 7 Ziffern). |
| `pii` | Der PII-Guard ([KB-02](../tools/pii_guard.py)) meldet einen Verdacht. |
| `lesefehler` | Die Datei konnte nicht gelesen werden. |

Die PII-Prüfung ruft `tools/pii_guard.py` auf — die PII-Logik lebt dort (single
source of truth), KB-03 meldet nur. Das Skript **repariert nichts**; es meldet.
