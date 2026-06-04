---
id: DEP-05
title: Login-User anlegen, Akte laden, Matze freischalten
status: todo
depends_on: [DEP-04, KB-03, ONB-01, ONB-02]
stop_after: true
epic: deploy
commit_type: chore(deploy)
---

# DEP-05 — Login & Fallakte (Go-Live)

> **Supervised.** Der letzte Schritt: echte Daten, echter Zugang für Matze.

## Why
Damit Matze sich einloggen und mit der hinterlegten Akte chatten kann.

## Scope
- Registrierung ist deaktiviert → User für Thomas + Matze manuell anlegen
  (LibreChat-User-CLI/Script, siehe `docs/runbook.md`).
- Zwei-Faktor für beide Konten aktivieren.
- Fallakte (pseudonymisiert, von Thomas kuratiert) per `tools/ingest_case_file.py`
  in die RAG-Wissensbasis laden — der PII-Guard (KB-02) läuft davor.
- Matze den Nutzer-Guide (`docs/user-guide.md`) geben.

## Acceptance (manuell)
- [ ] Thomas + Matze können sich einloggen (mit 2FA).
- [ ] `pii_guard` meldet keinen Fund auf der Akte vor dem Upload.
- [ ] Eine Beispiel-Frage liefert Antwort MIT Bezug auf die Akte und MIT Quellen.
- [ ] Einwilligung (ONB-03) dokumentiert vorliegend.

## Notes
Erst nach dokumentierter Einwilligung des Sorgeberechtigten live schalten.

## Stop-Gate
Go-Live abgeschlossen. Matze nutzt das System; Thomas pflegt im Hintergrund.
