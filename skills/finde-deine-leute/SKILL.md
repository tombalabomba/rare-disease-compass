---
name: finde-deine-leute
description: Führt aus dem konkreten Fall (Verdachtskrankheit, Gen, HPO) zu den passenden Anlaufstellen — Patientenorganisationen, RareConnect, rekrutierende Studien und genetisches Matching als bewusst gegatete Option.
---

# finde-deine-leute

Macht „du bist nicht allein" konkret: bündelt aus der Fallakte
(Verdachtskrankheit / Gen / HPO) die menschlichen Anlaufstellen — andere
Betroffene, Organisationen, Zentren und, als bewusste Entscheidung, genetische
Matching-Netze. Klammer um die einzelnen `rdc`-Community-Quellen.

## Haltung
Diese Skill folgt `config/assistant-instructions.md`: **keine Diagnose**, keine
Therapieempfehlung, Quellen pflichtig, Unsicherheit explizit. Ton **behutsam und
ermächtigend** nach `config/case-profile.yaml` — die Familie behält die Kontrolle.
Jede genannte Stelle bekommt einen **anklickbaren Link** (Wegweiser-Prinzip:
relevante Ressourcen nennen, nie automatisch ansteuern). RDC reicht **nichts**
ein und überträgt keine Daten an Dritte.

## Voraussetzung
Installierte `rdc`-CLI und Web-Zugriff. Gepflegte Fallakte (`case-file-*.md`) mit
Verdachtskrankheit / Gen / HPO.

## Ablauf
Reihenfolge bewusst: erst die niedrigschwelligen, **datensparsamen** Wege, dann
das Matching als bewusste, gegatete Option.

1. Anker aus der Fallakte lesen: Verdachtskrankheit/ORPHA, betroffenes Gen,
   führende HPO-Terme (`## Genetik-Zusammenfassung`, `## Symptome`).

2. **Patientenorganisationen + RareConnect-Community** (COM-01) — der erste,
   niedrigschwellige Weg zu anderen Betroffenen:
   ```bash
   rdc community orgs "Marfan syndrome" --json
   rdc community rareconnect "Marfan syndrome" --json
   ```
   (akzeptiert auch ORPHA-Code, z. B. `ORPHA:558`). Liefert klickbare Wegweiser zu
   Orphanet-Disease-Seiten und RareConnect — keine erfundenen Organisationsnamen.

3. **Rekrutierende Studien** (COM-02) als Weg zu Zentren und Betroffenen:
   ```bash
   rdc trials search "Marfan syndrome" --recruiting --json
   ```
   Studienzentren sind oft der direkteste Kontakt zu spezialisierten Teams.

4. **Genetisches Matching als Wegweiser** (COM-03) — bewusste, gegatete Option,
   **ohne** automatische Datenweitergabe:
   ```bash
   rdc community matchmaking
   ```
   Reiner Info-Befehl (offline, kein Netzwerk-Aufruf). Gibt die Wegweiser-Links zu
   MME/GeneMatcher/MyGene2 aus. **Einwilligungs-Hinweis pflichtig:** Eine
   Einreichung übermittelt Gen-/Symptomdaten (oft eines Kindes) — eine bewusste
   **Einwilligungs**-Entscheidung der Sorgeberechtigten, üblicherweise über die
   Humangenetik/behandelnde Klinik. RDC reicht selbst nichts ein. Details:
   `docs/connect-genetic-matching.md`, `docs/consent-template.md`, `docs/security.md`.

## Output
- Gruppierte, weitergabe-taugliche Übersicht in drei Blöcken — **Organisationen &
  Community**, **rekrutierende Studien**, **genetisches Matching (gegatet)** — jede
  Zeile mit **anklickbarem Link**.
- Beim Matching der **Einwilligungs-Hinweis** sichtbar: RDC überträgt keine Daten;
  eine Einreichung ist eine bewusste Entscheidung der Sorgeberechtigten über die
  Klinik.
- Herkunfts-Fußzeile: „Erstellt mit RareDiseaseCompass — Recherche-Unterstützung,
  keine Diagnose" (https://github.com/tombalabomba/rare-disease-compass).
- Hinweis: **keine Diagnose**, keine Empfehlung einer konkreten Stelle als „die
  richtige"; die Auswahl trifft die Familie mit dem ärztlichen Team.
