---
id: ONB-02
title: Nutzer-Guide (Matze)
status: todo
depends_on: []
stop_after: false
epic: onboarding
commit_type: docs(onboarding)
---

# ONB-02 — Nutzer-Guide (Matze)

## Why
Matze ist der Vater des Kindes und der eigentliche Nutzer — er chattet mit dem
System, baut es aber nicht. Ohne eine einfache, jargonfreie Anleitung weiß er
nicht, wie er sich einloggt, wie er gute Fragen stellt oder — am wichtigsten —
wo die Grenzen liegen (das System stellt **keine Diagnose**). Ein technisches
Runbook hilft ihm nicht. Dieses Ticket schreibt einen Guide in einfacher Sprache,
der ihn handlungsfähig macht und gleichzeitig klar abgrenzt, was das System darf.

## Scope
**`docs/user-guide.md`** — Nutzer-Handbuch in **einfacher Sprache**, kein
Technik-Jargon, **keine** Code-Blöcke. Pflicht-Bausteine (als `##`-Überschriften,
exakt so benannt, damit die Acceptance per `grep` greift):

- **`## Login`** — wie Matze sich anmeldet: die Adresse aufrufen, mit dem von
  Thomas eingerichteten Konto einloggen (Selbstregistrierung gibt es nicht — Konten
  legt Thomas an), Hinweis auf Zwei-Faktor und sicheres Passwort in einfachen Worten.
- **`## Gute Fragen stellen`** — wie man dem Assistenten hilft, gute Antworten zu
  geben: konkret sein, einen Punkt pro Frage, nachfragen, wenn etwas unklar ist,
  ruhig in eigenen Worten beschreiben.
- **`## Beispiel-Fragen`** — vier Sorten von Beispielfragen, jeweils mit einer
  synthetischen, erfundenen Beispiel-Formulierung (keine echten Patientendaten):
  - Symptome → mögliche Krankheiten („Welche seltenen Krankheiten passen zu
    folgenden Beschwerden …?")
  - eine genetische Variante → Bedeutung („Was ist über die Variante … bekannt?")
  - neue Studien / aktuelle Literatur („Gibt es neue Studien zu …?")
  - Fragen für den nächsten Arzttermin („Welche Fragen sollte ich der Ärztin
    beim nächsten Termin stellen?")
- **`## Was das System kann und was nicht`** — klare Liste: es **kann** Literatur
  und Datenbanken durchsuchen, Zusammenhänge erklären, Fragen für Ärzte vorbereiten;
  es **kann nicht** und **darf nicht** diagnostizieren, behandeln oder ärztlichen
  Rat ersetzen. Der Satz **„keine Diagnose"** muss wörtlich vorkommen.
- **`## Quellen lesen`** — der Assistent nennt Quellen; wie man sie erkennt und
  warum sie wichtig sind (Nachprüfbarkeit, mit zum Arzt nehmen), in einfacher Sprache.
- **`## Datenschutz`** — in einfachen Worten: die Fallakte liegt verschlüsselt auf
  einem Server in der EU, nur unter Pseudonym (Initialen, kein Klarname), für die
  Antworten gehen Inhalte an die KI von Anthropic (die nicht damit trainiert),
  niemand außer den eingerichteten Konten kommt rein. Verweis auf die ausführliche
  Einwilligungs-/Datenschutz-Vorlage (ONB-03, `consent-template.md`).

Ein kurzer Hinweis am Anfang oder Ende, dass dieses System **kein Medizinprodukt**
ist und ärztlichen Rat nicht ersetzt (konsistent mit dem README-Disclaimer).

## Files
```
docs/user-guide.md   (NEU)
```

## Reality Check (Pflicht — vor Promotion nach `2.ready/`)
- [x] **Files in `Scope`/`Files`**: `docs/user-guide.md` ist **NEU** — verifiziert,
      existiert noch nicht (`ls docs/` zeigt nur `architektur.md`, `security.md`).
- [x] **`depends_on`-IDs**: keine. Der Guide beschreibt die Nutzersicht (Login,
      Fragen stellen, Grenzen) und braucht keinen fertigen Stack — er kann jederzeit
      geschrieben werden. Der Datenschutz-Abschnitt verweist auf ONB-03, ist aber
      nicht von dessen Fertigstellung abhängig (Forward-Link genügt).
- [x] **Externe Voraussetzungen**: keine. Reine Doku, synthetische Beispiele.
- [x] **Tooling**: nur ein Texteditor. Acceptance über `grep`/`test`; `markdownlint`
      falls verfügbar.

## Acceptance
- [ ] Datei existiert: `test -f docs/user-guide.md`.
- [ ] Pflicht-Bausteine vorhanden:
      `grep -q '## Login' docs/user-guide.md`,
      `grep -q '## Beispiel-Fragen' docs/user-guide.md`,
      `grep -q '## Datenschutz' docs/user-guide.md`.
- [ ] „keine Diagnose"-Hinweis vorhanden (wörtlich):
      `grep -qi 'keine Diagnose' docs/user-guide.md`.
- [ ] Alle vier Beispiel-Fragen-Sorten erkennbar (Symptome, Variante, Studien,
      Arzttermin): `grep -qi 'Arzttermin\|Arztterminen\|nächsten Termin' docs/user-guide.md`
      und Sichtprüfung der vier Beispiel-Formulierungen.
- [ ] **Einfache Sprache (keine Code-Blöcke):** keine Markdown-Codezäune im Text —
      `grep -c '```' docs/user-guide.md` ergibt `0`.
- [ ] **Negativ-Check (Datenschutz):** keine echten Patientendaten, Namen oder
      Geburtsdaten — nur synthetische Beispiele (Sichtprüfung des Diffs).
- [ ] Markdown-Links nicht offensichtlich kaputt: keine leeren Linkziele
      (`grep -nE '\]\(\s*\)' docs/user-guide.md` findet nichts).
- [ ] `markdownlint docs/user-guide.md` ohne Findings (falls Tool verfügbar; sonst
      manuelle Prüfung).

## Out of scope
- Betreiber-/Technik-Schritte (Provisionierung, Start/Stop, Backup) — das ist ONB-01.
- Rechtsverbindliche Einwilligungstexte — das ist ONB-03 (hier nur einfacher
  Datenschutz-Abschnitt + Verweis).
- Screenshots / UI-Tour mit echten Daten — nicht nötig und datenschutzkritisch.

## Notes
- Tonalität bewusst niedrigschwellig: kurze Sätze, „du"-Ansprache passend, keine
  Fachbegriffe ohne Erklärung. Im Zweifel lieber ein Wort mehr erklären.
- Beispiel-Fragen so formulieren, dass sie als **Vorlagen** taugen, aber nie
  reale Symptome/Varianten des Kindes enthalten — erfundene Platzhalter verwenden.
