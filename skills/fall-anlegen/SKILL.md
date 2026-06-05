---
name: fall-anlegen
description: Geführter, ruhiger Onboarding-Flow, der Schritt für Schritt eine pseudonymisierte, HPO-codierte Fallakte aus dem KB-01-Template aufbaut — empathisch, ohne Pflicht-Hürden, jederzeit pausierbar.
---

# fall-anlegen

Nimmt einen verunsicherten Nutzer an die Hand und baut mit ihm gemeinsam die
**erste strukturierte Fallakte** auf: für wen, welche Symptome, was wurde schon
gemacht, welche Daten existieren. Der Flow läuft im Gespräch — keine GUI, kein
Formularzwang. Er darf jederzeit pausiert und später fortgesetzt werden.

## Haltung
Diese Skill folgt `config/assistant-instructions.md`: **keine Diagnose**, keine
Therapieempfehlung, Quellen pflichtig, Unsicherheit explizit. Der Ton ist bewusst
**behutsam** und richtet sich nach `config/case-profile.yaml` (EXP-01). Es gibt
**keine Validierungs-Blockaden** wie bei einem Pflicht-Onboarding — fehlende
Angaben sind erlaubt und werden später ergänzt.

## Datenschutz zuerst
- **Schritt 0 — Einwilligung klären, bevor irgendetwas eingegeben wird.** Geht es
  um Daten eines Kindes, sollten die **Sorgeberechtigten** dokumentiert einwilligen
  (Vorlage: `docs/consent-template.md`). Dabei ausdrücklich nennen, dass die
  Chat-Inhalte zur Verarbeitung an **Anthropics Server** gehen (Claude Code rechnet nicht lokal; Details: `docs/security.md`,
  Abschnitt „Der ehrliche Punkt"). Erst wenn das geklärt ist, mit dem Anlegen beginnen.
- **Nichts wird ohne ausdrückliche Einwilligung gespeichert.** Vor dem Anlegen
  der Akte wird klar gesagt, was wohin geschrieben wird (lokaler/geteilter Fall-
  Ordner, außerhalb des Repos).
- **Pseudonymisierung von Anfang an:** nur Initialen, niemals Klarname; nur Alter
  in Jahren bzw. Altersspanne, niemals exaktes Geburtsdatum; keine VCF-/Genom-
  Dateien und keine Befund-PDFs in der Akte (siehe `docs/security.md`).
- Im Zweifel defensiv: lieber eine Angabe weglassen als ein PII-Leck riskieren.

## Voraussetzung
Installierte `rdc`-CLI (zum HPO-Nachschlagen). Das Fallakten-Template
`docs/case-file-TEMPLATE.md` (KB-01) und das Validierungs-Skript
`tools/validate_case_folder.py` (KB-03) liegen im Repo vor.

## Ablauf

### 1. Profil klären (`case-profile`)
Zuerst `config/case-profile.yaml` befüllen (Vorlage: `config/case-profile.example.yaml`).
Behutsam erfragen, ohne Druck:
- Fachsprache-Niveau (`medical_literacy`: laie | informiert | fachkundig),
  Sprache (`language`), emotionaler Register (`tone`).
- Pseudonymisierter Kontext (`about`): Initialen, Rolle, grobe Altersspanne —
  **keine** Klarnamen, **keine** Geburtsdaten.
- Ziele (`goals`), woran die Familie gerade arbeitet.

Dieses Profil steuert nur den **Ton** der späteren Antworten, nicht die Kernregeln.

### 2. Fallakte Schritt für Schritt füllen
Die Akte folgt exakt den Pflichtsektionen aus `docs/case-file-TEMPLATE.md` (KB-01).
Überschriften nicht umbenennen — sie werden maschinell geprüft. Reihenfolge,
ruhig und in einzelnen Schritten:

1. **`## Stammdaten`** — pseudonymisiert: Initialen, Alter in Jahren, Geschlecht.
2. **`## Zeitleiste`** — chronologischer Verlauf (älteste Ereignisse zuerst).
3. **`## Symptome`** — Symptome sammeln und als **HPO**-Tabelle codieren. Jede
   Zeile braucht eine gültige HPO-ID (`HP:` + genau 7 Ziffern). Die Zuordnung
   Symptom → HPO-Code passiert im Gespräch; bei Unklarheit lieber nachfragen als
   raten. Kandidaten-Codes lassen sich gegen die öffentlichen Quellen plausi-
   bilisieren, indem man sie durch die DDx-CLIs schickt:
   ```bash
   rdc pubcasefinder rank HP:0002028 HP:0001263 --json
   ```
4. **`## Befunde`** — Endoskopie / Histologie / Labor (nur Klartext-Zusammen-
   fassung, **keine** PDF-Anhänge).
5. **`## Ausgeschlossenes`** — bereits ausgeschlossene Diagnosen mit Begründung.
6. **`## Genetik-Zusammenfassung`** — leer lassen; wird von `rdc`/GEN-03 aus dem
   Exomiser-Ergebnis erzeugt. Hier nur den Hinweis geben, dass Genetik-Daten
   (VCF) lokal bleiben und separat über die Genetik-Skills laufen.
7. **`## Offene Fragen`** — Arbeitshypothesen und nächste diagnostische Schritte.
8. **`## Medikation`** — aktuelle und frühere Therapie.

Fehlt etwas, ist das in Ordnung: Lücke markieren, später ergänzen, Flow pausieren.

### 3. Abschluss-Check
Am Ende den Fall-Ordner durch die deterministische, offline laufende Validierung
schicken — prüft Pflichtsektionen, HPO-Format und den **PII-Guard**:
```bash
python tools/validate_case_folder.py <pfad-zum-fall-ordner>
```
Findet der PII-Guard ein Leck (Klarname, Geburtsdatum, eingebettete Rohdaten),
wird die Stelle gemeinsam bereinigt, bevor die Akte als angelegt gilt.

## Beispiel (synthetisch)
Alle Beispiele sind **erfunden** — keine realen Personen, keine echten Daten:

```markdown
## Stammdaten
- **Initialen:** L. K.
- **Alter:** 4 Jahre
- **Geschlecht:** weiblich

## Symptome
| Symptom | HPO-ID | seit wann |
|---|---|---|
| Muskelhypotonie | HP:0001252 | seit Geburt |
| Entwicklungsverzögerung | HP:0001263 | seit 2. Lebensjahr |
```

## Output
- Eine pseudonymisierte, HPO-codierte Fallakte nach KB-01-Schema im Fall-Ordner.
- Eine befüllte `config/case-profile.yaml` für die Ton-Adaption.
- Ein bestandener Validierungslauf (Pflichtsektionen, HPO-Format, PII-Guard).
- Hinweis: keine Diagnose; die Akte ist Recherche-Grundlage, keine ärztliche Bewertung.
