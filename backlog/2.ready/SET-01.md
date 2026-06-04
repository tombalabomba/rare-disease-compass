---
id: SET-01
title: Projekt-Layout & Fallakten-Ordner-Konvention
status: todo
depends_on: []
stop_after: false
epic: setup
commit_type: feat(setup)
---

# SET-01 — Projekt-Layout & Fallakten-Ordner-Konvention

## Why
Ohne eine klare, schriftliche Konvention, **wo** die Fallakte liegt und **wie**
Claude Code darauf zeigt, würde jeder Nutzer das selbst erfinden — mit dem Risiko,
die pseudonymisierte Akte oder (schlimmer) die Genetik-Rohdaten versehentlich ins
Open-Source-Repo zu legen. Das wäre ein PII-Leck (`docs/security.md`). Dieses
Ticket schreibt die verbindliche Ordner-Trennung fest: Software im Repo,
Patientendaten strikt außerhalb (standardmäßig ein lokaler Ordner; bei zwei Rollen optional geteilt+verschlüsselt, z. B. Dropbox, für die
Zwei-Rollen-Nutzung), Genetik-Rohdaten nur lokal, nicht geteilt. Es ist die
Grundlage, auf die ONB-01 (Runbook) und KB-03 (Ordner-Validierung) aufsetzen.

## Scope
Eine neue Doku-Datei `docs/project-layout.md` (deutsch), die die Ordnerstruktur
verbindlich beschreibt. Pflicht-Abschnitte (als Markdown-Überschriften, exakt so
benannt, damit die Acceptance per `grep` greift):

- **`## Fallakten-Ablage`** — wo die Fallakte liegt: ein lokaler Ordner **außerhalb**
  des Repos. Empfohlen ein eigener Top-Level-Ordner (z. B. `~/rca-fall-mustermann/`),
  niemals ein Unterordner des geklonten Repos. Begründung: das Repo ist öffentlich,
  die Akte ist es nie.
- **`## Datentrennung (lokal & optional geteilt)`** — die Zwei-Rollen-Nutzung: die **pseudonymisierte**
  Fallakte (Markdown) liegt standardmäßig in einem lokalen Ordner; bei Zwei-Rollen-Nutzung optional in einem geteilten, verschlüsselten Ordner (z. B. Dropbox)
  (einer kuratiert, einer liest mit). Die Genetik-**Rohdaten** liegen NICHT in
  diesem geteilten Ordner. Klare Tabelle: was wird geteilt (Akte) vs. was bleibt
  privat-lokal (VCF, Befund-PDFs, CLI-SQLite-History).
- **`## Genetik lokal`** — die VCF-/Rohgenom-Dateien liegen ausschließlich lokal auf
  dem Rechner des Kurators, außerhalb eines etwaigen geteilten Ordners und außerhalb des
  Repos. Nur die kuratierte Ergebnis-Zusammenfassung (GEN-03) wandert in die Akte.
- **`## Claude-Code-Konfig`** — wie Claude Code auf den Fall-Ordner zeigt: Claude
  Code wird **im Fall-Ordner** (nicht im Repo) gestartet bzw. der Fall-Ordner als
  zusätzliches Arbeitsverzeichnis aufgenommen; eine `CLAUDE.md` **im Fall-Ordner**
  lädt die Assistenten-Persona (Inhalt aus KB-04, `config/assistant-instructions.md`).
  Die installierten `rca`-CLIs sind global verfügbar und werden über die Shell
  aufgerufen.
- Ein **Beispiel-Layout** (ASCII-Baum in einem Code-Block), das Repo-Ordner und
  Fall-Ordner nebeneinander zeigt und sichtbar macht, dass der Fall-Ordner außerhalb
  des Repos liegt.

## Files
```
docs/project-layout.md   (NEU)
```

## Reality Check (Pflicht — vor Promotion nach `2.ready/`)
- [x] **Files in `Scope`/`Files`**: `docs/project-layout.md` wird NEU angelegt;
      `docs/` existiert bereits (`ls docs/` → `architektur.md mockups security.md`).
- [x] **`depends_on`-IDs**: keine. SET-01 ist eine reine Doku-Datei, hängt von nichts
      ab. Verweist konzeptionell auf KB-04 (Persona) und GEN-03 (Genetik-Ergebnis),
      braucht deren Code aber nicht — es beschreibt nur die Ablage.
- [x] **Externe Voraussetzungen**: keine. Reine Markdown-Doku, kein Tool, kein
      Account, kein Download.
- [x] **Tooling**: nur `grep` für die Acceptance (überall verfügbar). Kein
      Build/Test nötig.

## Acceptance
- [ ] Alle Pflicht-Abschnitte vorhanden (maschinell):
      `grep -q '## Fallakten-Ablage' docs/project-layout.md &&
       grep -q '## Datentrennung (lokal & optional geteilt)' docs/project-layout.md &&
       grep -q '## Genetik lokal' docs/project-layout.md &&
       grep -q '## Claude-Code-Konfig' docs/project-layout.md`
- [ ] Persona-Hinweis vorhanden: die Datei nennt eine `CLAUDE.md` im Fall-Ordner:
      `grep -q 'CLAUDE.md' docs/project-layout.md`
- [ ] CLI-Bezug vorhanden: die Doku benennt die `rca`-CLIs:
      `grep -q 'rca' docs/project-layout.md`
- [ ] Beispiel-Layout vorhanden: mindestens ein Code-Block (Fenced):
      `grep -q '```' docs/project-layout.md`
- [ ] **Negativ-Check (Datenschutz):** die Doku rät NICHT, die Akte ins Repo zu
      legen. Es darf keine Empfehlung geben, die Fallakte unter dem Repo abzulegen.
      Maschinell — keine Erwähnung eines Repo-internen Akten-Pfads:
      `! grep -qiE 'akte.*(im|ins) repo|repo/.*case-file|fallakte.*im repo' docs/project-layout.md`
      Die Doku stellt im Gegenteil explizit klar, dass die Akte **außerhalb** des
      Repos liegt: `grep -qiE 'außerhalb des repos' docs/project-layout.md`
- [ ] **Negativ-Check (keine echten Daten):** keine realen Namen/Geburtsdaten im
      Beispiel-Layout — kein Muster `DD.MM.YYYY`:
      `! grep -qE '[0-9]{2}\.[0-9]{2}\.[0-9]{4}' docs/project-layout.md`

## Out of scope
- **CLI-Installation:** wie `rca` auf eine Maschine kommt, ist SET-02
  (`scripts/install.sh` + `docs/install.md`).
- **Inhalt der Persona:** die Assistenten-Instruktionen selbst sind KB-04
  (`config/assistant-instructions.md`). SET-01 verweist nur darauf.
- **Fallakten-Schema:** die innere Struktur der Akte (HPO-Tabelle etc.) ist KB-01.
- **Validierungs-Skript:** das Prüfen eines Fall-Ordners gegen die Konvention ist
  KB-03 (`tools/validate_case_folder.py`).
- **Setup-Runbook:** die Schritt-für-Schritt-Einrichtung auf einer Maschine ist
  ONB-01 (`docs/runbook.md`).

## Notes
- **Single source of truth für die Ablage-Konvention.** Diese Datei ist die
  Referenz, auf die ONB-01 und KB-03 verweisen. Konventionen hier definieren, nicht
  in anderen Docs duplizieren.
- **Konsistenz mit `docs/security.md`** beachten: dort steht der Grundsatz
  „Repo enthält nie echte Daten" und „VCF bleibt nur lokal". SET-01 macht daraus die
  konkrete Ordner-Anleitung. Achtung: `docs/security.md` enthält noch eine ältere
  Server-Tabelle (Hetzner/Postgres) aus der Pre-Pivot-Phase — das ist NICHT die
  aktuelle Architektur (server-los, siehe `docs/architektur.md` und `AGENTS.md`
  Pivot-Note 2026-06-04). SET-01 beschreibt ausschließlich die lokale (optional geteilte) Ablage,
  übernimmt nichts vom Server-Modell. (Die Server-Tabelle in `docs/security.md` zu
  bereinigen ist ein eigenes Doku-Ticket, nicht Teil von SET-01.)
