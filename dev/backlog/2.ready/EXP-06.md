---
id: EXP-06
title: Lesbarkeit & Aufbereitung von Reports (Hypothesen-Framing, klickbare Quellen, Klartext)
status: todo
depends_on: [KB-04, EXP-02]
stop_after: false
epic: experience
commit_type: feat(experience)
---

# EXP-06 — Lesbarkeit & Aufbereitung von Reports

## Why
Datenbank-Treffer und Literatur sind nur nützlich, wenn ein Mensch ohne Vorwissen
(auch die Familie) sofort versteht, was gemeint ist, und die Quelle selbst anklicken
kann. Fünf Hebel: (1) als Hypothese rahmen, (2) DB-Grenzen + Gegenbeispiel zeigen,
(3) jede ID → klickbarer Link, (4) ein Klartext-Satz pro Eintrag, (5) gruppierte,
weitergabe-taugliche Tabelle.

## Scope
Die folgenden Texte **wortgetreu** einfügen (Stil der vorhandenen Doku beibehalten).

### 1) `config/assistant-instructions.md` — neuer Abschnitt (ans Ende der Ergebnis-/Antwortregeln)

````markdown
## Aufbereitung & Lesbarkeit von Ergebnissen

Datenbank-Treffer und Literatur sind nur dann nützlich, wenn ein Mensch ohne
Vorwissen — auch die Familie — sofort versteht, was gemeint ist, und die Quelle
selbst anklicken kann. Immer:

- **Als Hypothesen benennen, nie als Diagnose.** Vor jeder Kandidaten-Liste ein
  Satz: „Das sind mögliche Ursachen, die noch nicht geprüft/ausgeschlossen sind —
  keine Diagnosen." Kandidaten sind Vorschläge zum Weiterfragen.
- **Grenzen der Datenbank offenlegen.** Sagen, dass die DB nur nach
  Symptom-Überlappung rankt und manche Treffer nicht passen — mit einem
  konkreten Beispiel aus der aktuellen Liste (z. B. „Treffer X betrifft fast nur
  Jungen"). So weiß der Leser, dass ein Arzt filtern muss.
- **Jede Zeile bekommt eine anklickbare Quelle.** Nackte IDs (PMID, OMIM, MONDO …)
  sind unbrauchbar — immer in einen vollständigen Link umwandeln (Muster s. u.).
- **Ein Satz Klartext pro Eintrag.** Was ist das / warum ist es relevant — im
  Register nach `medical_literacy` (laie: Alltagssprache zuerst, Fachbegriff in
  Klammern).
- **Gruppieren statt flache Liste.** Kandidaten in beschriftete Gruppen bündeln
  (z. B. „Blutungsstörungen, die Standardtests übersehen" / „brüchige Gefäße").
- **Tabellen mit festen Spalten** verwenden, wo es mehrere Einträge gibt:
  Kandidaten → `Mögliche Ursache | Was das ist (1 Satz) | Quelle (anklickbar)`;
  Literatur → `Worum es geht | Was der Artikel sagt | Link`.
- **Weitergabe-tauglich schreiben.** Der Abschnitt muss isoliert funktionieren:
  jemand öffnet ihn, tippt einen Link, landet bei der Quelle — ohne den Chatverlauf.
- **Wegweiser-Prinzip.** Relevante Ressourcen, die RDC **nicht** direkt abfragt
  (z. B. Patienten-Matching-Netze, Register), immer als anklickbaren Wegweiser
  nennen — nie verschweigen, nie automatisch ansteuern.
- **Disclaimer bleibt**, auch knapp: Recherche, keine Diagnose/Therapie.

### IDs in klickbare Links umwandeln (Pflicht-Muster)

| Quelle | ID-Beispiel | Link-Muster |
|---|---|---|
| PubMed | `41347994` | `https://pubmed.ncbi.nlm.nih.gov/41347994/` |
| OMIM | `193400` | `https://omim.org/entry/193400` |
| Monarch / MONDO | `MONDO:0009276` | `https://monarchinitiative.org/MONDO:0009276` |
| Orphanet | ORPHA `903` | `https://www.orpha.net/en/disease/detail/903` |
| ClinVar | `VCV000012345` | `https://www.ncbi.nlm.nih.gov/clinvar/variation/12345/` |
| HPO-Term | `HP:0000421` | `https://hpo.jax.org/browse/term/HP:0000421` |
| Europe PMC | PMID `41347994` | `https://europepmc.org/article/MED/41347994` |
````

### 2) `skills/differential/SKILL.md` — den `## Output`-Abschnitt durch diesen ersetzen

````markdown
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
````

### 3) `skills/erklaer-mir/SKILL.md` — im `## Output` ergänzen

````markdown
- Literatur/Quellen als **Tabelle** `Worum es geht | Was der Artikel sagt | Link`,
  nie als nackte PMID — jede ID in den vollständigen PubMed-Link umwandeln.
````

## Files
```
config/assistant-instructions.md   (erweitert: Abschnitt + Link-Muster-Tabelle)
skills/differential/SKILL.md       (erweitert: ## Output ersetzt)
skills/erklaer-mir/SKILL.md        (erweitert: ## Output ergänzt)
```

## Reality Check
- [x] `config/assistant-instructions.md` (KB-04), `skills/differential/SKILL.md` und
      `skills/erklaer-mir/SKILL.md` (EXP-02) existieren in `3.done/`-Bauzustand.
- [x] Reine Markdown-Änderungen; keine externen Voraussetzungen, keine Secrets.

## Acceptance
- [ ] `config/assistant-instructions.md` enthält per grep: „Aufbereitung & Lesbarkeit",
      „Hypothesen", „klickbare" bzw. „anklickbar", „Wegweiser-Prinzip" und die
      Link-Muster-Tabelle (z. B. `pubmed.ncbi.nlm.nih.gov`).
- [ ] `skills/differential/SKILL.md` `## Output` enthält die gruppierte Tabelle
      `Mögliche Ursache | Was das ist` und den Hypothesen-Einleitungssatz.
- [ ] `skills/erklaer-mir/SKILL.md` enthält die Literatur-Tabelle `Worum es geht`.
- [ ] Negativ-Check: keine echten Patientendaten; bestehende Pflicht-Bausteine
      (keine Diagnose, Quellen, Arztfragen) bleiben erhalten.

## Out of scope
- Änderungen an den CLIs selbst — Formatierung passiert in Persona/Skills.

## Notes
Texte sind vom Nutzer vorgegeben und **wortgetreu** einzusetzen. Wo ein `## Output`
bereits existiert (differential), den vorhandenen ersetzen; bei erklaer-mir die Zeile
ergänzen, ohne bestehende Punkte zu entfernen.
