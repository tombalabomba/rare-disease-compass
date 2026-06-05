---
name: erklaer-mir
description: Erklärt einen Befund, einen Fachbegriff oder eine Diagnose-Hypothese in der Sprache, die zum Fall passt — laienverständlich, behutsam, ohne zu werten.
---

# erklaer-mir

Übersetzt medizinisches Fachvokabular aus der Fallakte oder aus gefundener Literatur
in eine verständliche Erklärung. Rein erklärend — diese Skill ruft keine CLI auf,
sondern nutzt den vorhandenen Fallkontext und bereits recherchierte Quellen.

## Haltung
Diese Skill folgt `config/assistant-instructions.md`. Sie stellt **keine Diagnose**
und gibt **keine Therapieempfehlung**. Jede medizinische Aussage nennt eine
nachprüfbare Quelle (PMID/PMCID, ClinVar-/Monarch-/Orphanet-Eintrag, OMIM-Nr.).
Sprachniveau und Ton richten sich nach `config/case-profile.yaml`
(`medical_literacy`, `tone`).

## Ablauf
1. Begriff oder Befund identifizieren — aus der Frage des Nutzers oder aus der Fallakte
   (`case-file-*.md`, Abschnitte `## Befunde`, `## Symptome`, `## Genetik-Zusammenfassung`).
2. Erklärung an `medical_literacy` ausrichten:
   - `laie`: erst einfache Sprache, dann der Fachbegriff in Klammern.
   - `informiert`: Fachbegriff direkt, bei Erstnennung kurz erläutert.
   - `fachkundig`: volle Fachsprache, keine Grundlagen-Erklärung.
3. Wo eine medizinische Aussage gemacht wird: die Quelle nennen, aus der sie stammt
   (bereits in der `## Befunde`-/`## Genetik`-Sektion oder in der Recherche-Historie).
4. Unsicherheit explizit machen, Gegenevidenz aktiv benennen, nichts erfinden.

## Output
- Eine verständliche Erklärung im passenden Register.
- Literatur/Quellen als **Tabelle** `Worum es geht | Was der Artikel sagt | Link`,
  nie als nackte PMID — jede ID in den vollständigen PubMed-Link umwandeln.
- Bei jedem relevanten Punkt: eine **konkrete Frage für den nächsten Arzttermin**.
- Hinweis am Ende: keine medizinische Beratung; alle Entscheidungen trifft das
  behandelnde ärztliche Team.
