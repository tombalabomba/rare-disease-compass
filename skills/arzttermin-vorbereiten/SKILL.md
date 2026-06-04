---
name: arzttermin-vorbereiten
description: Erstellt ein 1-Seiten-Dossier und konkrete Fragen für den nächsten Arzttermin — aus Fallakte und allen bisher recherchierten Quellen.
---

# arzttermin-vorbereiten

Bündelt den aktuellen Fallstand zu einem kompakten Dossier, das die Familie zum
nächsten Termin mitnehmen kann: was bekannt ist, was offen ist, und welche Fragen
sich lohnen. Zieht Fallakte und Recherche-Historie zusammen.

## Haltung
Diese Skill folgt `config/assistant-instructions.md`: **keine Diagnose**, keine
Therapieempfehlung, Quellen pflichtig, Unsicherheit explizit. Das Dossier ist eine
Gesprächsvorbereitung, keine ärztliche Bewertung. Ton/Register nach
`config/case-profile.yaml`.

## Voraussetzung
Installierte `rdc`-CLI. Gepflegte Fallakte (`case-file-*.md`).

## Ablauf
1. Fallstand aus der Akte lesen: `## Stammdaten`, `## Symptome`, `## Befunde`,
   `## Ausgeschlossenes`, `## Genetik-Zusammenfassung`, `## Offene Fragen`, `## Medikation`.
2. Bisherige Recherche einbeziehen:
   ```bash
   rdc history list --limit 30 --json
   ```
   und bei Bedarf gezielt nachschlagen (`rdc history search <begriff>`).
3. Offene Hypothesen kurz gegenprüfen (z. B. `rdc compound phenotype-workup <HPO...> --json`),
   wenn seit dem letzten Termin neue Phänotypen dazugekommen sind.
4. Dossier auf **eine Seite** verdichten: Stand, offene Fragen, Differentialhypothesen
   mit Quelle, was als Nächstes geklärt werden sollte.

## Output
- 1-Seiten-Dossier: aktueller Stand, offene Punkte, Hypothesen mit **Quelle pro Aussage**.
- Priorisierte, **konkrete Fragen für den nächsten Arzttermin**.
- Hinweis: keine medizinische Beratung; das Dossier dient nur der Gesprächsvorbereitung.
