---
id: EXP-04
title: Onboarding-Flow (/fall-anlegen)
status: todo
depends_on: [KB-01, EXP-01]
stop_after: false
epic: experience
commit_type: feat(experience)
---

# EXP-04 — Onboarding-Flow

## Why
Ein verunsicherter Nutzer kann keine HPO-codierte Akte aus dem Stand bauen. Ein geführter
Flow nimmt ihn an die Hand: für wen, welche Symptome, was wurde schon gemacht, welche
Daten existieren — und erzeugt daraus die erste strukturierte Fallakte. Spiegelt Dex'
Onboarding, aber empathisch und ohne Pflicht-Hürden.

## Scope
- `skills/fall-anlegen/SKILL.md` — geführter, ruhiger Flow:
  1. `case-profile.yaml` befüllen (Vorwissen, Sprache, Ton, Ziele — aus EXP-01).
  2. Schritt für Schritt die Fallakte aus `docs/case-file-TEMPLATE.md` (KB-01) füllen:
     Stammdaten (pseudonymisiert), Zeitleiste, Symptome → HPO codieren (mithilfe der
     CLIs/Nachfragen), Befunde, Ausgeschlossenes, vorhandene Daten (inkl. Genetik-Hinweis).
  3. Am Ende `tools/validate_case_folder.py` (KB-03) laufen lassen, inkl. PII-Guard.
- Klar machen: nichts wird ohne Zustimmung gespeichert; Pseudonymisierung von Anfang an.

## Files
```
skills/fall-anlegen/SKILL.md   (NEU)
```

## Reality Check
- [x] Nutzt das Template aus KB-01 → `depends_on: [KB-01]`.
- [x] Nutzt `case-profile.yaml` + Ton-Regeln aus EXP-01 → `depends_on: [EXP-01]`.
- [x] `validate_case_folder.py` (KB-03) ist im Flow referenziert, aber kein harter Build-Block
      (Flow ist Doku/Anleitung); zur Laufzeit muss es vorhanden sein → Hinweis in Notes.
- [x] Externe Voraussetzungen: keine zum Schreiben.

## Acceptance
- [ ] `skills/fall-anlegen/SKILL.md` hat YAML-Frontmatter (`name`, `description`) — per grep.
- [ ] Enthält per grep die Schritte: `case-profile`, `HPO`, Verweis auf `case-file-TEMPLATE.md`,
      Verweis auf `validate_case_folder.py`.
- [ ] Enthält den Einwilligungs-/Pseudonymisierungs-Hinweis (grep „Einwilligung" und „Pseudonym").
- [ ] Negativ-Check: keine echten Daten; Beispiele synthetisch.

## Out of scope
- Automatisches Parsen von Befund-PDFs (separates Ticket / `/befund-hinzufügen` in EXP-02).
- Eine GUI — der Flow läuft im Gespräch.

## Notes
Tonalität bewusst behutsam (EXP-01). Keine Validierungs-Blockaden wie bei Dex' Pflicht-Step;
der Flow darf jederzeit pausiert und später fortgesetzt werden.
