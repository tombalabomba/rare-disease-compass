---
id: ONB-02
title: Nutzer-Guide (Endnutzer)
status: done
depends_on: []
stop_after: false
epic: onboarding
commit_type: docs(onboarding)
---

# ONB-02 — Nutzer-Guide (Endnutzer)

## Why
Der Endnutzer (z. B. ein betroffener Elternteil) ist keine technische Person und
hat den Ordner schon eingerichtet bekommen. Er braucht eine kurze, klare Anleitung
in **einfacher Sprache**: wie man Claude Code öffnet, gute Fragen stellt, die
Antworten und Quellen liest — und vor allem, was das System **nicht** kann (keine
Diagnose). Ohne diesen Guide wirkt das Werkzeug für die Zielperson überfordernd
oder es entstehen falsche Erwartungen an eine „Diagnose-Maschine". Der Guide grenzt
sich bewusst vom technischen Setup-Runbook (ONB-01) ab.

## Scope
Eine neue Datei `docs/user-guide.md` (deutsch, **einfache Sprache, kein Jargon**)
für den chattenden Endnutzer. Kein technisches Setup — das hat der Betreiber schon
erledigt. Pflicht-Bausteine (als Markdown-Überschriften, damit per `grep` prüfbar):

1. **## Claude Code öffnen** — in einfachen Worten: das Programm öffnen, in dem die
   Fallakte liegt, und losschreiben wie in einem Chat. Keine Kommandozeilen-Befehle,
   keine Installation — das ist Sache des Betreibers (Verweis auf `docs/runbook.md`
   nur als „falls etwas eingerichtet werden muss, frag die Person, die das aufgesetzt
   hat").
2. **## Beispiel-Fragen** — konkrete, abtippbare Beispielfragen in vier Richtungen:
   - **Symptome → mögliche Krankheiten** („Welche seltenen Krankheiten passen zu
     diesen Symptomen?").
   - **Variante → Bedeutung** („Was bedeutet diese genetische Veränderung?").
   - **Neue Studien** („Gibt es neue Studien oder Veröffentlichungen dazu?").
   - **Fragen für den nächsten Arzttermin** („Welche Fragen sollte ich beim nächsten
     Arzttermin stellen?").
   Jeweils ein, zwei Sätze, warum die Frage nützlich ist.
3. **## Was das System kann und was nicht** — klare Liste: es **recherchiert**,
   **fasst zusammen**, **nennt Quellen**, **schlägt Arztfragen vor**. Es **stellt
   keine Diagnose**, ersetzt keine Ärztin/keinen Arzt, ist kein Medizinprodukt
   (Sprache an `README.md` angelehnt: „keine Diagnose").
4. **## Quellen lesen** — in einfachen Worten: jede Antwort sollte auf Quellen
   verweisen (Paper, Datenbanken); ermutigen, die Quellen anzusehen oder mit dem Arzt
   zu teilen, und Antworten ohne Quelle skeptisch zu sehen.
5. **## Datenschutz in einfachen Worten** — kurz und ohne Jargon: die Fallakte liegt
   in einem geschützten Ordner, sie ist pseudonymisiert (nur Initialen), die
   Genetik-Rohdaten bleiben auf dem Rechner; beim Chatten gehen die Texte zur
   Beantwortung an den KI-Dienst (Claude), der **nicht** damit trainiert. Verweis auf
   `docs/consent-template.md` (ONB-03) für Details.

Ton durchgehend ermutigend, geduldig, ohne Fachbegriffe (oder Fachbegriff sofort
erklärt).

## Files
```
docs/user-guide.md   (NEU)
```

## Reality Check (Pflicht — vor Promotion nach `2.ready/`)
- [x] **Files in `Scope`/`Files`**: `docs/user-guide.md` wird bewusst NEU angelegt.
      `ls docs/` zeigt aktuell `architektur.md mockups security.md` — `user-guide.md`
      existiert noch nicht. `docs/` existiert.
- [x] **`depends_on`-IDs**: keine. Der Guide ist reine Prosa für den Endnutzer und
      hängt von keinem Code ab. Die optionalen Verweise auf `docs/runbook.md` (ONB-01)
      und `docs/consent-template.md` (ONB-03) sind „nice to have" und werden als reine
      Pfad-Strings notiert, damit kein Link-Check an der Bau-Reihenfolge scheitert.
- [x] **Externe Voraussetzungen**: keine. Kein Download, kein Secret, kein Server.
- [x] **Tooling**: `grep` für die Baustein-Checks verfügbar. `markdownlint` ist im
      Repo **nicht** installiert → markdownlint-Check ist „falls verfügbar".

## Acceptance
- [ ] Datei existiert: `test -f docs/user-guide.md`
- [ ] Alle Pflicht-Bausteine vorhanden, per `grep`:
      `grep -qiE 'Claude Code' docs/user-guide.md &&
       grep -qiE '^#+ .*(Beispiel-Fragen|Beispielfragen)' docs/user-guide.md &&
       grep -qiE 'keine Diagnose' docs/user-guide.md &&
       grep -qiE 'Quellen' docs/user-guide.md &&
       grep -qiE 'Datenschutz' docs/user-guide.md`
- [ ] Die vier Beispiel-Frage-Richtungen sind erkennbar (Symptome, Variante/genetische
      Veränderung, Studien, Arzttermin):
      `grep -qiE 'Symptome?' docs/user-guide.md &&
       grep -qiE 'Variante|genetische' docs/user-guide.md &&
       grep -qiE 'Studie' docs/user-guide.md &&
       grep -qiE 'Arzttermin|Arzt' docs/user-guide.md`
- [ ] Keine offensichtlich kaputten relativen Links (jedes `](…)`-Ziel auf eine
      Repo-Datei existiert; noch nicht gebaute Dep-Dateien als reine Pfad-Strings).
- [ ] markdownlint-sauber, **falls verfügbar**:
      `command -v markdownlint >/dev/null && markdownlint docs/user-guide.md || true`
- [ ] **Negativ-Check (kein Server-/Login-Jargon):**
      `! grep -qiE 'hetzner|librechat|\bserver\b|login|anmelden|registrier|account anlegen|api-key|kommandozeile|terminal-befehl|pipx|docker' docs/user-guide.md`
- [ ] **Negativ-Check (Datenschutz):** keine echten Patientendaten, Namen oder
      Geburtsdaten — Beispielfragen sind generisch/Platzhalter.

## Out of scope
- **Technisches Setup:** Installation, Ordner anlegen, Claude-Code-Konfiguration —
  das ist Betreiber-Sache und steht in ONB-01 (`docs/runbook.md`).
- **Volle Einwilligungs-/Datenschutz-Erklärung:** der Guide erklärt Datenschutz nur
  in einfachen Worten; die Vorlage ist ONB-03 (`docs/consent-template.md`).
- **Screenshots / UI-Tour:** keine Bilder in diesem Ticket (wären eigenes Asset-
  Ticket); reine Textanleitung.

## Notes
- **Zielgruppe = Laie.** Der Guide muss ohne Fachbegriffe funktionieren. HPO,
  VCF, „Variante", „Pseudonymisierung" entweder vermeiden oder in einem Halbsatz
  erklären. Im Zweifel die einfachere Formulierung wählen.
- **Kein Server-/Login-Jargon.** Es gibt keinen Login, keine Registrierung, keinen
  Server. Der Nutzer öffnet ein Programm, in dem alles schon liegt. Begriffe wie
  „anmelden", „Account", „API-Key", „Terminal" gehören nicht in diesen Guide (der
  Negativ-Check erzwingt das).
- **Sprach-Anker.** Die „keine Diagnose"-Formulierung und der Medizinprodukt-
  Disclaimer können sich an `README.md` (Kasten oben) orientieren — gleiche Aussage,
  einfachere Worte.
