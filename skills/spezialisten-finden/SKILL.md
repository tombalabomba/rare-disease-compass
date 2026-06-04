---
name: spezialisten-finden
description: Findet Zentren für Seltene Erkrankungen, Spezialambulanzen und passende Studien — über rdc-Quellen (Orphanet) plus gezielte Web-Recherche.
---

# spezialisten-finden

Hilft, Anlaufstellen zu finden: Referenzzentren für Seltene Erkrankungen,
Spezialambulanzen und laufende Studien, die zur aktuellen Hypothese passen.
Kombiniert `rdc`-Quellen mit gezielter Web-Suche.

## Haltung
Diese Skill folgt `config/assistant-instructions.md`: **keine Diagnose**, keine
Empfehlung einer bestimmten Einrichtung als „die richtige", Quellen pflichtig. Sie
listet Optionen mit Beleg, die Auswahl trifft die Familie mit dem ärztlichen Team.
Ton nach `config/case-profile.yaml`.

## Voraussetzung
Installierte `rdc`-CLI und Web-Zugriff.

## Ablauf
1. Aktuelle Verdachtsdiagnose/Hypothese aus der Fallakte (`## Genetik-Zusammenfassung`,
   offene Differentialliste) nehmen.
2. Krankheits-Metadaten und assoziierte Ressourcen über Orphanet ziehen:
   ```bash
   rdc orphanet lookup "Marfan syndrome" --json
   rdc orphanet lookup ORPHA:558 --json
   ```
   (liefert ORPHA-Code, Synonyme, Verknüpfungen als Ankerpunkte für die Suche).
3. Aktuelle Studien über die Literatur-Suche eingrenzen:
   ```bash
   rdc europepmc search "Marfan syndrome AND clinical trial" --json
   ```
4. Gezielte Web-Recherche nach Referenzzentren/Studienregistern (z. B. ERN, nationale
   SE-Zentren, ClinicalTrials/DRKS) — jede genannte Stelle mit Quelle/Link belegen.

## Output
- Liste möglicher Zentren/Ambulanzen und passender Studien, je mit **Quelle/Link**.
- Hinweis auf Region/Sprache aus `case-profile.yaml`, falls relevant.
- **Fragen für den nächsten Arzttermin** (z. B. Überweisung, Studieneignung).
- Hinweis: keine Diagnose und keine Empfehlung einer konkreten Einrichtung; die
  Entscheidung trifft das behandelnde ärztliche Team.
