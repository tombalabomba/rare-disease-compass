---
name: was-ist-neu
description: Zeigt, was seit der letzten Sitzung dazugekommen ist — neue Literatur und Studien zum Fall, abgeglichen mit der lokalen Recherche-Historie.
---

# was-ist-neu

Beantwortet „Was hat sich seit dem letzten Mal getan?" Vergleicht den aktuellen
Stand der Literatur mit dem, was die lokale SQLite-Historie bereits kennt, und hebt
nur das Neue hervor.

## Haltung
Diese Skill folgt `config/assistant-instructions.md`: **keine Diagnose**, keine
Therapieempfehlung, Quellen pflichtig, Unsicherheit explizit. Neue Treffer werden
eingeordnet, nicht bewertet. Ton/Register nach `config/case-profile.yaml`.

## Voraussetzung
Installierte `rdc`-CLI. Die Historie liegt lokal (Default `~/.rdc/history.db`, per
`RCA_HISTORY_DB` überschreibbar) und außerhalb des Repos.

## Ablauf
1. Was wurde zuletzt recherchiert? Historie ansehen:
   ```bash
   rdc history list --limit 30 --json
   rdc history search "<krankheit-oder-gen>" --json
   ```
2. Aktuelle Literatur zu den Fall-Themen neu abfragen:
   ```bash
   rdc pubmed search "<krankheit> AND <jahr>" --json
   rdc europepmc search "<krankheit> AND review" --json
   ```
3. Differenz bilden: Treffer, deren PMID/PMCID **nicht** in der Historie auftaucht,
   sind „neu". Jeder neue Eintrag wird (durch den nächsten CLI-Lauf) automatisch in
   die Historie geschrieben.
4. Neue Studien/Reviews kurz einordnen: Relevanz für die offenen Fragen des Falls,
   Gegenevidenz nicht verschweigen.

## Output
- Liste der **neuen** Literatur/Studien seit der letzten Sitzung, je mit PMID/PMCID.
- Kurze Einordnung pro Eintrag (Relevanz, Unsicherheit).
- **Fragen für den nächsten Arzttermin**, falls etwas Neues das nahelegt.
- Hinweis: keine Diagnose; ärztliche Bewertung erforderlich.
