---
id: COM-04
title: Skill /finde-deine-leute (Community-Workflow)
status: todo
depends_on: [COM-01, COM-02, COM-03, EXP-01]
stop_after: false
epic: community
commit_type: feat(community)
---

# COM-04 — Skill /finde-deine-leute

## Why
Die einzelnen Community-Quellen brauchen eine menschliche Klammer: einen Workflow,
der aus dem konkreten Fall (Verdachtskrankheit, Gen, HPO) die passenden Anlaufstellen
zusammenträgt — damit „du bist nicht allein" konkret wird.

## Scope
- `skills/finde-deine-leute/SKILL.md` — geführter Workflow, der aus der Fallakte
  (Verdachtskrankheit / Gen / HPO) zusammenstellt:
  1. **Patientenorganisationen + RareConnect-Community** (`rdc community orgs` /
     `rareconnect`, COM-01).
  2. **Rekrutierende Studien** als Weg zu Zentren und Betroffenen
     (`rdc trials search --recruiting`, COM-02).
  3. **Genetisches Matching als Wegweiser** (`rdc community matchmaking`, COM-03) —
     mit Einwilligungs-Hinweis, **ohne** automatische Datenweitergabe.
- Persona/Ton nach `config/assistant-instructions.md` + `case-profile.yaml` (EXP-01):
  behutsam, ermächtigend; alle Ausgaben mit anklickbaren Links; Disclaimer.
- Frontmatter (`name`, `description`) wie die anderen Skills.

## Files
```
skills/finde-deine-leute/SKILL.md   (NEU)
```

## Reality Check
- [x] Die genutzten Befehle entstehen in COM-01..03; Persona in EXP-01 — alle als
      `depends_on` gesetzt, der Loop zieht COM-04 erst, wenn diese in `3.done/` liegen.
- [x] Skill ist Doku/Anleitung; echte Ausführung braucht installierte CLIs →
      Smoke-Test manuell.
- [x] Externe Voraussetzungen: keine zum Schreiben.

## Acceptance
- [ ] `skills/finde-deine-leute/SKILL.md` hat YAML-Frontmatter (`name`,
      `description`) — per grep.
- [ ] Nennt per grep die drei Wege: `rdc community`, `rdc trials`, `matchmaking`.
- [ ] Enthält den Einwilligungs-Hinweis zum Matching (grep „Einwilligung") und den
      Disclaimer („keine Diagnose").
- [ ] Negativ-Check: keine echten Patientendaten; kein Schritt, der ohne Zustimmung
      Daten an Matching-Netze gibt.

## Out of scope
- Die Quell-Befehle selbst (COM-01..03).

## Notes
Reihenfolge im Workflow bewusst: erst die niedrigschwelligen, datensparsamen Wege
(Organisationen, Studien), dann das Matching als bewusste, gegatete Option.
