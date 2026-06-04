---
id: ONB-01
title: Setup-Runbook (Betreiber/Kurator)
status: todo
depends_on: [SET-02, CLI-06, KB-03]
stop_after: false
epic: onboarding
commit_type: docs(onboarding)
---

# ONB-01 — Setup-Runbook (Betreiber/Kurator)

## Why
Der Betreiber/Kurator (die technische Rolle, die die Fallakte einrichtet und
pflegt) braucht eine einzige, lückenlose Schritt-für-Schritt-Anleitung, um das
System auf einer Maschine lauffähig zu machen. Ohne dieses Runbook ist das Wissen
über CLIs, Fallakten-Ordner, Validierung, Claude-Code-Konfiguration und die
Zwei-Rollen-Dropbox über `docs/` verstreut und reproduzierbar nur für den, der
den Code geschrieben hat. Das Runbook bündelt den **einmaligen, manuellen**
Einrichtungspfad (kein Server-Deployment) und verlinkt in die jeweiligen
Detail-Dokumente.

## Scope
Eine neue Datei `docs/runbook.md` (deutsch) als geführtes Setup-Runbook für den
Betreiber/Kurator. Sie ist ein **Verweis-Hub** — die Tiefe steht in den verlinkten
Dokumenten, das Runbook gibt die richtige Reihenfolge und das große Bild. Pflicht-
Abschnitte (als Markdown-Überschriften, damit per `grep` prüfbar):

1. **## Installation** — die CLIs auf der Maschine installieren. Verweis auf das
   Installer-Skript `scripts/install.sh` und die Installations-Doku `docs/install.md`
   (beide aus SET-02). Voraussetzungen kurz nennen (Python 3.11, Docker für die
   Genetik), aber nicht duplizieren — auf `docs/install.md` verweisen.
2. **## API-Keys** — optionale API-Keys hinterlegen (z. B. PubMed/NCBI). Wo sie
   hingehören (lokale, gitignored `.env`), dass sie **optional** sind (die meisten
   Quellen brauchen keinen Key, siehe `docs/architektur.md`) und **nie** ins Repo.
3. **## Akte anlegen und validieren** — den Fallakten-Ordner anlegen (Verweis auf
   die Ordner-Konvention `docs/project-layout.md` und die Fallakten-Vorlage
   `docs/case-file-TEMPLATE.md`), die Akte HPO-codiert und pseudonymisiert pflegen,
   anschließend mit `tools/validate_case_folder.py` (aus KB-03) prüfen. Den
   konkreten Aufruf des Validators nennen.
4. **## Claude-Code-Konfiguration** — Claude Code im Fall-Ordner öffnen und die
   Assistenten-Instruktionen `config/assistant-instructions.md` (aus KB-04) als
   `CLAUDE.md` in den Fall-Ordner legen, damit der Assistent Persona und Regeln
   (keine Diagnose, Quellen nennen, Arztfragen) übernimmt.
5. **## Dropbox-Zwei-Rollen** — für die Zwei-Rollen-Nutzung den Fall-Ordner in eine
   **geteilte, verschlüsselte Dropbox** legen: einer kuratiert die Akte, der andere
   (Endnutzer) liest und chattet. Klarstellen: die Genetik-**Rohdaten** (VCF) bleiben
   **lokal außerhalb** des geteilten Ordners (siehe `docs/architektur.md`,
   `docs/security.md`).
6. **## Genetik (Exomiser lokal)** — Exomiser einmalig lokal lauffähig machen,
   Verweis auf `docs/genetics-setup.md` (Referenzdaten-Download, Docker-Lauf). Nur
   verlinken, nicht duplizieren.
7. **## Troubleshooting** — die häufigsten Stolpersteine: CLI nicht im `PATH`,
   fehlendes/fehlerhaftes API-Key-Format, Validator meldet PII/Schema-Fehler, Docker
   nicht gestartet, Dropbox synchronisiert nicht.

Querverweise als relative Markdown-Links auf die genannten Dateien. Reihenfolge der
Abschnitte folgt dem realen Einrichtungsablauf.

## Files
```
docs/runbook.md   (NEU)
```

## Reality Check (Pflicht — vor Promotion nach `2.ready/`)
- [x] **Files in `Scope`/`Files`**: `docs/runbook.md` wird bewusst NEU angelegt.
      `ls docs/` zeigt aktuell nur `architektur.md mockups security.md` — `runbook.md`
      existiert noch nicht. `docs/` existiert.
- [x] **`depends_on`-IDs**: SET-02 liefert `scripts/install.sh` + `docs/install.md`,
      CLI-06 liefert den CLI-Guide (`docs/cli-guide.md`) als Abschluss des CLI-Epics,
      KB-03 liefert `tools/validate_case_folder.py` + `docs/case-folder.md`. Alle drei
      Tickets stehen in `backlog/PLAN.md` (Modul-Karte) und sind die Quellen der hier
      verlinkten Dateien. Das Runbook **verlinkt** nur — es importiert keinen Code,
      daher reicht, dass die Ziel-Pfade nach `done` der Deps existieren. Zusätzlich
      verlinkte Dateien aus Schwester-Tickets desselben `knowledge`/`setup`-Bereichs
      (`docs/project-layout.md` SET-01, `docs/case-file-TEMPLATE.md` KB-01,
      `config/assistant-instructions.md` KB-04, `docs/genetics-setup.md` GEN-01)
      gehören zum geplanten Doku-Set (PLAN.md Modul-Karte) und werden vom Loop vor/neben
      diesem Ticket gebaut. Sollte eine Ziel-Datei beim Bau noch fehlen, bleibt der
      Verweis als relativer Link korrekt (Pfad ist festgelegt) — der Negativ-Link-Check
      prüft nur **dieses** File auf offensichtlich kaputte Inline-Links.
- [x] **Externe Voraussetzungen**: keine. Reine Doku, kein Download, kein Secret,
      kein Server. Der einzige „manuelle" Teil ist der vom Runbook **beschriebene**
      Setup-Vorgang selbst — der gehört in den Text, nicht in die Acceptance.
- [x] **Tooling**: `grep` (für die Abschnitts- und Verweis-Checks) ist verfügbar.
      `markdownlint` ist im Repo **nicht** installiert (`command -v markdownlint` →
      leer) → der markdownlint-Check ist „falls verfügbar" und wird sonst übersprungen.

## Acceptance
- [ ] Datei existiert: `test -f docs/runbook.md`
- [ ] Alle Pflicht-Abschnitte vorhanden (Markdown-Überschriften), per `grep`:
      `grep -qiE '^#+ .*Installation' docs/runbook.md &&
       grep -qiE '^#+ .*API-Keys' docs/runbook.md &&
       grep -qiE '^#+ .*(Akte anlegen|anlegen und validieren|validieren)' docs/runbook.md &&
       grep -qiE '^#+ .*Claude-Code' docs/runbook.md &&
       grep -qiE '^#+ .*(Dropbox|Zwei-Rollen)' docs/runbook.md &&
       grep -qiE '^#+ .*Troubleshooting' docs/runbook.md`
- [ ] Verweise auf die referenzierten Dateien vorhanden (als Pfad-Strings im Text):
      `for ref in scripts/install.sh docs/install.md docs/project-layout.md \
        docs/case-file-TEMPLATE.md tools/validate_case_folder.py \
        config/assistant-instructions.md docs/genetics-setup.md; do \
        grep -q "$ref" docs/runbook.md || { echo "fehlt: $ref"; exit 1; }; done`
- [ ] Keine offensichtlich kaputten relativen Links: jedes Ziel eines
      `](relativer/pfad)`-Links, das auf eine `.md`/`.sh`/`.py`-Datei im Repo zeigt,
      existiert. Prüfung relativ zu `docs/` für `../`-Pfade. (Verweise auf noch nicht
      gebaute Dep-Dateien dürfen als reine Pfad-Strings ohne Link-Syntax stehen, damit
      dieser Check nicht an Dep-Reihenfolge scheitert.)
- [ ] markdownlint-sauber, **falls verfügbar**:
      `command -v markdownlint >/dev/null && markdownlint docs/runbook.md || true`
- [ ] **Negativ-Check (Architektur):** erwähnt KEINEN Server/Hetzner/Login:
      `! grep -qiE 'hetzner|librechat|\bserver\b|server-deployment|login|anmeldung am server' docs/runbook.md`
- [ ] **Negativ-Check (Datenschutz):** keine echten Patientendaten, Namen oder
      Geburtsdaten — nur generische Anleitung und Platzhalter.

## Out of scope
- **Inhalt der verlinkten Dokumente:** `docs/install.md`, `docs/project-layout.md`,
  `docs/case-file-TEMPLATE.md`, `tools/validate_case_folder.py`,
  `config/assistant-instructions.md`, `docs/genetics-setup.md` werden von ihren
  eigenen Tickets erzeugt. Das Runbook **verlinkt** nur, dupliziert nicht.
- **Nutzer-Guide (Endnutzer):** Die Anleitung für den chattenden Endnutzer ist
  ONB-02 (`docs/user-guide.md`).
- **Einwilligungs-/Datenschutz-Vorlage:** ist ONB-03 (`docs/consent-template.md`).
- **Tatsächliche Installation/Smoke-Test:** das reale Ausführen von `install.sh`,
  Exomiser-Lauf etc. ist ein menschlicher Schritt (lokal), kein Doku-Ticket.

## Notes
- **Kein Server.** Das Runbook beschreibt ausschließlich lokales Setup: CLIs
  installieren, Claude Code im Ordner öffnen, Fallakte im (Dropbox-)Ordner pflegen.
  `docs/security.md` enthält noch Alt-Referenzen (Hetzner/LibreChat/Login) aus der
  verworfenen Server-Architektur (siehe `AGENTS.md`, 2026-06-04 Architektur-Pivot) —
  **nicht** ins Runbook übernehmen. Bereinigung von `security.md` ist nicht Scope
  dieses Tickets (eigenes Ticket/Drive-by außerhalb von `Files`).
- **Verweise als robuste Pfad-Strings.** Damit der Link-Check nicht an der
  Bau-Reihenfolge der Dep-Dateien scheitert, dürfen Verweise auf noch nicht erzeugte
  Dateien als reiner Code-Pfad (z. B. `` `tools/validate_case_folder.py` ``) statt als
  klickbarer Link stehen. Verweise auf bereits existierende Dokumente
  (`docs/architektur.md`, `docs/security.md`) gern als relativer Link.
- **Reihenfolge = realer Ablauf.** Installation → API-Keys → Akte → Claude-Code →
  Dropbox-Zwei-Rollen → Genetik → Troubleshooting. So liest es sich als durchgängiges
  Runbook, nicht als Referenzliste.
