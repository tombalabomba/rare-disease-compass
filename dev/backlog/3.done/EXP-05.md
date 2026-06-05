---
id: EXP-05
title: Erweiterbarkeit (eigene Skills, updatefest)
status: done
depends_on: [EXP-02]
stop_after: false
epic: experience
commit_type: feat(experience)
---

# EXP-05 — Erweiterbarkeit

## Why
RDC soll eine Plattform sein, kein Einzelwerkzeug. Nutzer und Community sollen eigene
Skills bauen können (andere Krankheitsbilder, andere Datenquellen), ohne dass ein Update
sie überschreibt. Greift das bewÃ¤hrte `create-skill` + `-custom`-Schutz-Muster auf.

## Scope
- `skills/skill-erstellen/SKILL.md` — geführte Erstellung einer neuen Skill: legt
  `skills/<name>-custom/SKILL.md` an (Suffix `-custom`), mit Frontmatter-Gerüst und
  Verweis auf die Konvention.
- `docs/extending.md` — wie man RDC erweitert: eigene Skills, eigene CLI-Quelle
  (Quelle nach `cli/rdc/sources/` ergänzen), die `-custom`-Update-Regel.
- Update-Regel dokumentieren: ein künftiger Update-Mechanismus überschreibt **nur**
  Nicht-`-custom`-Skills.

## Files
```
skills/skill-erstellen/SKILL.md   (NEU)
docs/extending.md                 (NEU)
```

## Reality Check
- [x] Baut auf der Skills-Konvention aus EXP-02 auf → `depends_on: [EXP-02]`.
- [x] Externe Voraussetzungen: keine.

## Acceptance
- [ ] `skills/skill-erstellen/SKILL.md` hat Frontmatter (`name`, `description`) — grep.
- [ ] Beschreibt per grep die `-custom`-Namenskonvention und den Update-Schutz.
- [ ] `docs/extending.md` enthält per grep: „eigene Skill", „eigene Quelle"/`cli/rdc/sources`, „-custom".
- [ ] Negativ-Check: keine echten Patientendaten.

## Out of scope
- Der eigentliche Update-/Installer-Mechanismus von RDC (eigenes späteres Ticket).
- Ein zentrales Skill-Repository/Marktplatz.

## Notes
`-custom`-Konvention als bewusst vertrautes, robustes Update-Schutz-Muster.
