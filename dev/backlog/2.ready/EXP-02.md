---
id: EXP-02
title: Skills-Schicht (modulare /Workflows über den CLIs)
status: todo
depends_on: [CLI-06, EXP-01]
stop_after: false
epic: experience
commit_type: feat(experience)
---

# EXP-02 — Skills-Schicht

## Why
Die CLIs sind das Datenplumbing. Ein Mensch denkt aber in **Aufgaben**, nicht in API-Calls.
Eine Skills-Schicht (modulare `/befehle`) übersetzt menschliche Workflows in die richtige
Folge von CLI-Aufrufen und Antworten — genau wie Dex' Skills über seinem MCP. Modular,
erweiterbar, einzeln auffindbar.

## Scope
Pro Skill ein Ordner `skills/<name>/SKILL.md` mit Frontmatter (`name`, `description`)
und Markdown-Anweisung, die die `rdc`-CLIs nutzt und die Persona/Ton-Regeln (EXP-01) beachtet:

| Skill | Zweck | nutzt CLI |
|---|---|---|
| `skills/erklaer-mir/` | Befund/Begriff in einfacher Sprache erklären | (Kontext + Literatur) |
| `skills/differential/` | Phänotyp-Workup: passende Krankheiten | `rdc compound`, `rdc pubcasefinder`, `rdc monarch` |
| `skills/variante/` | Genvariante einordnen | `rdc variant` |
| `skills/arzttermin-vorbereiten/` | Fragen + 1-Seiten-Dossier für den nächsten Termin | (Akte + alle Quellen) |
| `skills/spezialisten-finden/` | Zentren für Seltene Erkrankungen / Studien | `rdc` + Web |
| `skills/was-ist-neu/` | Neue Literatur/Studien seit letzter Sitzung | `rdc` + SQLite-History |

## Files
```
skills/erklaer-mir/SKILL.md             (NEU)
skills/differential/SKILL.md            (NEU)
skills/variante/SKILL.md                (NEU)
skills/arzttermin-vorbereiten/SKILL.md  (NEU)
skills/spezialisten-finden/SKILL.md     (NEU)
skills/was-ist-neu/SKILL.md             (NEU)
```

## Reality Check
- [x] Die `rdc`-CLI-Subkommandos entstehen in CLI-02..06 → `depends_on: [CLI-06]`.
- [x] Persona/Ton-Regeln aus EXP-01 → `depends_on: [EXP-01]`.
- [x] Externe Voraussetzungen: keine zum Schreiben der Skills (Ausführung braucht installierte CLIs, Smoke-Test manuell).

## Acceptance
- [ ] Alle 6 `SKILL.md` existieren mit YAML-Frontmatter (`name:` und `description:` per grep).
- [ ] Jede Skill nennt mindestens einen konkreten `rdc`-Befehl (grep `rdc `), außer `erklaer-mir` (rein erklärend).
- [ ] Jede Skill enthält den Disclaimer-Verweis (grep „keine Diagnose" oder Verweis auf assistant-instructions).
- [ ] Negativ-Check: keine echten Patientendaten in den Skills.

## Out of scope
- Eine `create-skill`-Mechanik (das ist EXP-05).
- End-to-End-Ausführung gegen echte APIs (manueller Smoke-Test).

## Notes
SKILL.md-Konvention bewusst kompatibel zum Agent-Skills-Standard (Frontmatter + Markdown),
damit die Skills auch außerhalb von RDC nutzbar bleiben.
