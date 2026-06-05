---
id: EXP-03
title: Session-Start-Kontext (Fallstand + neue Literatur)
status: done
depends_on: [KB-03, CLI-06]
stop_after: false
epic: experience
commit_type: feat(experience)
---

# EXP-03 — Session-Start-Kontext

## Why
Damit jede Sitzung sofort weiß, wo der Fall steht, ohne dass der Nutzer alles wiederholt.
Spiegelt ein bewÃ¤hrtes Session-Start-Muster, aber medizinisch: Fallzusammenfassung, offene Fragen und
„seit deiner letzten Sitzung gibt es N neue Studien" (die SQLite-History weiß, was schon
abgefragt wurde). Das ist die **eine** Proaktivität, die hier passt — kein Nagging.

## Scope
- `scripts/session-context.sh` — liest den Fall-Ordner (Zusammenfassung + Abschnitt
  „Offene Fragen / Hypothesen" aus der Akte) und gibt einen knappen Kontextblock aus.
- Optionaler Literatur-Hinweis: über die `rdc`-History prüfen, ob es zu gespeicherten
  Suchanfragen neue Treffer seit dem letzten Lauf gibt; falls ja, als 1-Zeiler ausgeben.
  **Nur Hinweis, keine automatische Aktion.**
- Dokumentation, wie man es als Claude-Code-SessionStart-Hook einbindet (optional,
  in `docs/project-layout.md`-Stil), ohne dass RDC ohne Hook unbrauchbar wäre.

## Files
```
scripts/session-context.sh   (NEU)
```

## Reality Check
- [x] Liest den Fall-Ordner gemäß Konvention aus KB-03 → `depends_on: [KB-03]`.
- [x] Literatur-Hinweis nutzt die History aus CLI-01/CLI-06 → `depends_on: [CLI-06]`.
- [x] Externe Voraussetzungen: ein befüllter Fall-Ordner zur echten Nutzung (Test läuft gegen synthetische Fixture).

## Acceptance
- [ ] `shellcheck scripts/session-context.sh` ohne Findings; `bash -n` ok; `set -euo pipefail`.
- [ ] Gegen eine synthetische Fall-Fixture gibt das Skript die Sektionen „Fallstand" und
      „Offene Fragen" aus (Testlauf mit Fixture-Pfad).
- [ ] Fehlt der Fall-Ordner / die History: sauberer, freundlicher Hinweis statt Fehler (Exit 0).
- [ ] Negativ-Check: gibt keine Rohdaten/Genomzeilen aus, nur Zusammenfassung.

## Out of scope
- Verpflichtende Hook-Installation — der Block ist auch manuell aufrufbar.
- Push-Benachrichtigungen außerhalb der Sitzung.

## Notes
Bewusst opt-in und nicht-drängend gehalten (siehe Persona-Leitplanken EXP-01): ein
ruhiger Lagebericht, kein Alarm.
