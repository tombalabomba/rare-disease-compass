---
id: EXP-01
title: Persona & Ton-Adaption (Companion-Charakter + case-profile)
status: todo
depends_on: [KB-04]
stop_after: false
epic: experience
commit_type: feat(experience)
---

# EXP-01 — Persona & Ton-Adaption

## Why
Der Charakter entscheidet, ob RDC vertraut wird. Anders als ein Produktivitäts-Assistent
spricht RDC mit verunsicherten Betroffenen: ruhig, demütig, befähigend, emotional
achtsam, immer mit Quellen, nie diagnostizierend. Und der Ton muss sich an Vorwissen
und Verfassung des Nutzers anpassen (Laie ↔ belesener Elternteil; sachlich ↔ behutsam).

## Scope
- `config/assistant-instructions.md` (aus KB-04) um eine **Ton-Adaptions-Sektion**
  erweitern: wie RDC Antworten je nach `case-profile.yaml` anpasst (Fachsprache-Level,
  Sprache, emotionaler Register), plus expliziter **geschützter User-Block**
  (`<!-- USER_OVERRIDES_START -->` / `_END`), den Updates verbatim erhalten.
- `config/case-profile.example.yaml` (NEU, **synthetisch**): Vorlage mit Feldern
  `medical_literacy` (laie | informiert | fachkundig), `language`, `tone`
  (sachlich | behutsam | direkt), `about` (pseudonymisiert: Initialen, Alter, Rolle
  des Nutzers z. B. Elternteil), `goals` (z. B. „Diagnose finden", „Symptome lindern").
- Die echte `case-profile.yaml` lebt im **Fall-Ordner** (privat), nie im Repo.

## Files
```
config/assistant-instructions.md     (erweitert: Ton-Adaption + geschützter User-Block)
config/case-profile.example.yaml      (NEU, synthetisch)
```

## Reality Check
- [x] `config/assistant-instructions.md` wird von KB-04 angelegt → `depends_on: [KB-04]`.
- [x] Echte case-profile gehört in den Fall-Ordner (außerhalb Repo) — siehe `docs/security.md`,
      `docs/project-layout.md` (SET-01). Im Repo nur die `*.example.yaml`.
- [x] Externe Voraussetzungen: keine. Reines Markdown/YAML.

## Acceptance
- [ ] `assistant-instructions.md` enthält per grep: `medical_literacy`, `tone`,
      `USER_OVERRIDES_START`, `USER_OVERRIDES_END`.
- [ ] `python -c "import yaml; yaml.safe_load(open('config/case-profile.example.yaml'))"` lädt fehlerfrei.
- [ ] `case-profile.example.yaml` enthält die Felder `medical_literacy`, `language`, `tone`, `about`, `goals`.
- [ ] Negativ-Check: example enthält keine realen Namen/Geburtsdaten (kein `DD.MM.YYYY`).

## Out of scope
- Die eigentliche Befüllung mit echten Nutzerdaten (passiert lokal beim Onboarding, EXP-04).
- Mehrsprachige Übersetzung der Instruktionen (separat).

## Notes
Ton-Register sind Leitplanken für das Modell, kein starres Skript. Kernregeln aus KB-04
(keine Diagnose, Quellenpflicht, Arzt-Verweis) bleiben unabhängig vom Ton immer aktiv.
