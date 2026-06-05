---
name: differential
description: Phänotyp-Workup aus den HPO-Codes der Fallakte — listet passende Krankheiten und Gene über mehrere Quellen und ordnet sie ein, ohne sich vorschnell festzulegen.
---

# differential

Erzeugt aus den HPO-Codes des Falls eine quellengestützte Differentialdiagnose-Liste.
Nutzt die `rdc`-CLIs als Datenplumbing und bündelt die Ergebnisse zu einer
besprechbaren Übersicht.

## Haltung
Diese Skill folgt `config/assistant-instructions.md`: **keine Diagnose**, keine
Therapieempfehlung, Quellen pflichtig, Unsicherheit explizit. Sie zeigt
**Differentialdiagnosen** statt einer einzelnen Festlegung und nennt aktiv
Gegenevidenz. Ton/Register nach `config/case-profile.yaml`.

**Emotional achtsam:** Eine Differentialliste kann für Betroffene schwere oder
beängstigende Krankheitsbilder enthalten — das liegt in der Natur der Sache. Solche
Kandidaten **mit Einordnung** präsentieren (wie häufig/selten, wie sicher/unsicher,
dass es sich um Hypothesen zum Weiterfragen handelt, nicht um Befunde), nie als
nackte Liste schwerer Diagnosen. Bei sichtlich belastenden Treffern ruhig bleiben
und den nächsten konkreten Schritt (welche Frage an welche Ärztin) anbieten.

## Voraussetzung
Installierte `rdc`-CLI (siehe Setup-Runbook). HPO-Codes im Format `HP:` + 7 Ziffern,
zu finden in der Fallakte unter `## Symptome`.

## Ablauf
1. HPO-Codes aus der Fallakte (`## Symptome`) sammeln.
2. Multi-Quellen-Workup in einem Aufruf:
   ```bash
   rdc compound phenotype-workup HP:0001250 HP:0001263 --limit 20 --json
   ```
   (kombiniert Krankheits- und Gen-Kandidaten plus Literatur zur Top-Krankheit).
3. Zur Vertiefung einzelne Quellen gegenprüfen:
   ```bash
   rdc pubcasefinder rank HP:0001250 HP:0001263 --json
   rdc monarch diseases-by-phenotypes HP:0001250 HP:0001263 --json
   rdc phen2gene genes HP:0001250 HP:0001263 --json
   ```
4. Kandidaten konsolidieren: Übereinstimmungen über Quellen hinweg stärken die
   Konfidenz, Abweichungen offen benennen. Bereits Ausgeschlossenes (`## Ausgeschlossenes`)
   markieren.

## Output
- **Einleitungssatz:** „mögliche Ursachen / Hypothesen, keine Diagnosen" + Hinweis,
  dass die DB nach Symptom-Überlappung rankt und manche Treffer nicht passen
  (ein konkretes Beispiel aus der Liste nennen).
- **Gruppierte Tabelle:** `Mögliche Ursache | Was das ist (1 Satz) | Quelle (Link)`
  — Kandidaten in beschriftete Gruppen bündeln, jede ID als klickbarer Link
  (Muster s. assistant-instructions.md), jeder Eintrag mit Klartext-Satz.
- Übereinstimmungen über Quellen stärken die Konfidenz; Abweichungen + bereits
  Ausgeschlossenes offen markieren.
- **Konkrete Fragen für den nächsten Arzttermin** zu den Top-Hypothesen.
- Hinweis: keine Diagnose; ärztliche Bewertung erforderlich.
