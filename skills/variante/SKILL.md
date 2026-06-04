---
name: variante
description: Ordnet eine einzelne Genvariante ein — ClinVar-Signifikanz und gnomAD-Häufigkeit über die rdc-CLI — und macht die Evidenz besprechbar, ohne sie zu bewerten.
---

# variante

Schlägt eine Genvariante in öffentlichen Datenbanken nach und bereitet die
Klassifikation quellengestützt auf. Die VCF-/Genom-Datei bleibt lokal; diese Skill
arbeitet nur mit der bereits identifizierten Variante (z. B. aus der
Exomiser-Auswertung in `## Genetik-Zusammenfassung`).

## Haltung
Diese Skill folgt `config/assistant-instructions.md`: **keine Diagnose**, keine
Therapieempfehlung, Quellen pflichtig. Die Bewertung der Variante (pathogen/benigne
im konkreten Fall) trifft ausschließlich das ärztliche/humangenetische Team. Ton nach
`config/case-profile.yaml` (`fachkundig` zeigt HGVS-Nomenklatur und Konfidenzzahlen direkt).

## Voraussetzung
Installierte `rdc`-CLI. Variante in HGVS (`chr7:g.140453136A>T`) oder als rsID
(`rs113488022`).

## Ablauf
1. Variante aus der Fallakte (`## Genetik-Zusammenfassung`) übernehmen.
2. Vollständiges Lookup (ClinVar + gnomAD):
   ```bash
   rdc variant lookup rs113488022 --json
   ```
3. Gezielt nur die klinische Signifikanz:
   ```bash
   rdc variant clinvar chr7:g.140453136A>T --json
   ```
4. Einordnen: ClinVar-Signifikanz und Review-Status nennen, gnomAD-Allelfrequenz als
   Häufigkeits-Kontext, Diskrepanzen offen benennen. Nichts dazu erfinden.

## Output
- Klassifikation mit **ClinVar-Eintrag als Quelle** und gnomAD-Frequenz.
- Konfidenz und Gegenevidenz explizit.
- **Fragen für den nächsten (human-)genetischen Termin**.
- Hinweis: keine Diagnose; die genetische Bewertung erfolgt ärztlich.
