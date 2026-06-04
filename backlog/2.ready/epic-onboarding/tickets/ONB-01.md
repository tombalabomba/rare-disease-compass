---
id: ONB-01
title: Betreiber-Runbook (Thomas)
status: todo
depends_on: [INF-01, INF-03, KB-03, MCP-06]
stop_after: false
epic: onboarding
commit_type: docs(onboarding)
---

# ONB-01 — Betreiber-Runbook (Thomas)

## Why
Thomas baut und pflegt das System, aber das verteilte Wissen über Compose-Stack,
`librechat.yaml`, Secrets, Ingestion und Backups liegt heute nur in den einzelnen
Tickets und im Kopf. Ohne ein zusammenhängendes Runbook ist der Betrieb nicht
reproduzierbar: ein neuer User für Matze, ein Akten-Update oder ein Restore nach
Server-Verlust würden jedes Mal zur Detektivarbeit. Bei Gesundheitsdaten eines
Kindes (Art. 9 DSGVO) ist das inakzeptabel. Dieses Ticket bündelt alle
Betreiber-Abläufe in `docs/runbook.md` — ein Ort, eine Reihenfolge, kopierbare
Befehle.

## Scope
**`docs/runbook.md`** — Schritt-für-Schritt-Handbuch für den Betreiber. Pflicht-
Abschnitte (als `##`-Überschriften, exakt so benannt, damit die Acceptance per
`grep` greift):

- **`## Provisionierung`** — Server reproduzierbar in den Soll-Zustand bringen:
  Verweis auf `scripts/provision-server.sh` (INF-04), was es härtet (Docker,
  Deploy-User, ufw 22/80/443, fail2ban, unattended-upgrades, SSH), und der Hinweis,
  dass der eigentliche Lauf gegen die Maschine manuell erfolgt.
- **`## Start/Stop`** — Stack hoch- und runterfahren: `docker compose up -d`,
  `docker compose down`, `docker compose ps`, Logs (`docker compose logs -f api`),
  Reihenfolge/Healthchecks, was „läuft sauber" bedeutet.
- **`## Konfiguration & Secrets`** — `librechat.yaml` (INF-03) und `.env`: welche
  Variablen gesetzt sein müssen (`ANTHROPIC_API_KEY`, `JWT_SECRET`,
  `JWT_REFRESH_SECRET`, `CREDS_KEY`, `CREDS_IV`, DB-Credentials …), dass `.env`
  gitignored ist und Secrets nie im Repo landen, wo der Anthropic-Endpoint und das
  Modell `claude-opus-4-8` konfiguriert sind, und dass die Selbstregistrierung
  **aus** ist. **Keine echten Secret-Werte** im Runbook — nur Platzhalter.
- **`## User-Anlage`** — User für Matze und Thomas anlegen, obwohl Registrierung
  deaktiviert ist: der LibreChat-CLI-/Container-Weg zum manuellen Anlegen, Hinweis
  auf starke Passwörter und Zwei-Faktor (docs/security.md).
- **`## Akte-Update`** — Fallakte aktualisieren und **neu ingestieren**: bearbeiten,
  PII-Guard läuft im Ladepfad (bricht bei Fund ab), dann Ingestion via KB-03
  (`tools/ingest_case_file.py`), Idempotenz (Re-Upload aktualisiert statt
  dupliziert). Verweis auf KB-03.
- **`## MCP-Tools prüfen`** — verdrahtete MCP-Server (BioMCP + eigener `rare-case`
  aus MCP-06) prüfen: dass die Tools in einem Chat verfügbar sind, ein einfacher
  Test-Aufruf, wo nachzusehen ist, wenn ein Tool fehlt. Verweis auf MCP-06.
- **`## Backup/Restore`** — verschlüsseltes Backup via `scripts/backup.sh` (INF-05)
  und der **Restore-Weg**: entschlüsseln, Mongo + Postgres wiederherstellen, Volumes
  zurückspielen, Stack neu starten. Verweis auf INF-05.
- **`## Updates & Key-Rotation`** — Images/Stack aktualisieren (`docker compose pull`
  + Neustart), Secrets/Keys rotieren (welche, in welcher Reihenfolge, was danach neu
  startet), und der Hinweis, vor Updates ein Backup zu ziehen.
- **`## Troubleshooting`** — die häufigen Fehlerbilder: Stack startet nicht,
  Healthcheck rot, Login klemmt, RAG findet die Akte nicht, MCP-Tool antwortet
  nicht, TLS-/Caddy-Problem — je mit erstem Diagnose-Schritt.

Querverweise als Markdown-Links auf die referenzierten Tickets
(`../tickets/`-relativ in `2.ready/`) bzw. auf `docs/security.md` und
`docs/architektur.md`.

## Files
```
docs/runbook.md   (NEU)
```

## Reality Check (Pflicht — vor Promotion nach `2.ready/`)
- [x] **Files in `Scope`/`Files`**: `docs/runbook.md` ist **NEU** — verifiziert,
      existiert noch nicht (`ls docs/` zeigt nur `architektur.md`, `security.md`).
- [x] **`depends_on`-IDs**: INF-01, INF-03, KB-03, MCP-06 existieren als Tickets
      (`backlog/2.ready/epic-infra/tickets/INF-01.md`,
      `.../INF-03.md`, `backlog/2.ready/epic-knowledge/tickets/KB-03.md`,
      `backlog/2.ready/epic-mcp/tickets/MCP-06.md`). Das Runbook dokumentiert deren
      Output (Compose-Stack, `librechat.yaml`, Ingestion-Skript, verdrahteter MCP) —
      darum müssen sie vor ONB-01 `done` sein.
- [x] **Externe Voraussetzungen**: keine. Reine Doku, kein laufender Server, kein
      Secret nötig. Beschriebene Befehle setzen den fertigen Stack voraus, werden
      hier aber nur **dokumentiert**, nicht ausgeführt.
- [x] **Tooling**: nur ein Texteditor. Für die Acceptance reichen `grep`/`test`
      (vorhanden); `markdownlint` falls verfügbar, sonst manueller Lint-Check.

## Acceptance
- [ ] Datei existiert: `test -f docs/runbook.md`.
- [ ] Alle Pflicht-Abschnitte vorhanden (jeweils als Überschrift):
      `grep -q '## Provisionierung' docs/runbook.md`,
      `grep -q '## Start/Stop' docs/runbook.md`,
      `grep -q '## User-Anlage' docs/runbook.md`,
      `grep -q '## Akte-Update' docs/runbook.md`,
      `grep -q '## Backup/Restore' docs/runbook.md`,
      `grep -q '## Troubleshooting' docs/runbook.md`.
- [ ] Verweise auf die referenzierten Tickets/Dateien vorhanden:
      `grep -q 'INF-04' docs/runbook.md` (Provisioning),
      `grep -q 'KB-03' docs/runbook.md` (Ingestion),
      `grep -q 'INF-05' docs/runbook.md` (Backup),
      `grep -q 'MCP-06' docs/runbook.md` (MCP-Tools),
      `grep -q 'librechat.yaml' docs/runbook.md`.
- [ ] **Negativ-Check (Datenschutz):** kein echter Secret-Wert / keine echten
      Patientendaten im Diff — nur Platzhalter. Sichtprüfung + grep auf typische
      Leak-Muster (`grep -nEi 'sk-ant-[a-z0-9]|BEGIN .*PRIVATE KEY' docs/runbook.md`
      findet **nichts**).
- [ ] Markdown-Links nicht offensichtlich kaputt: keine leeren Linkziele
      (`grep -nE '\]\(\s*\)' docs/runbook.md` findet nichts), relative Ziele zeigen
      auf existierende Pfade.
- [ ] `markdownlint docs/runbook.md` ohne Findings (falls Tool verfügbar; sonst
      manuelle Prüfung auf konsistente Überschriften-Ebenen und Codeblock-Zäune).

## Out of scope
- Schreiben oder Ändern von Skripten/Configs (`provision-server.sh`, `backup.sh`,
  `librechat.yaml`, `ingest_case_file.py`) — die kommen aus ihren eigenen Tickets.
  Hier wird nur ihre **Bedienung** beschrieben.
- Nutzer-Anleitung für Matze — das ist ONB-02.
- Einwilligungs-/Datenschutz-Vorlage — das ist ONB-03.
- Live-Smoke-Test gegen den laufenden Stack — Epic-Ende, nicht maschinelle Acceptance.

## Notes
- Die exakten Befehle (CLI zum User-Anlegen, Ingestion-Aufruf, Restore-Schritte)
  aus den `done`-Tickets INF-01/INF-03/KB-03/MCP-06 und INF-04/INF-05 übernehmen,
  damit das Runbook zur tatsächlichen Implementierung passt — nicht erfinden.
- Beim manuellen User-Anlegen den von der finalen `librechat.yaml`/LibreChat-Version
  unterstützten Weg verwenden (Container-CLI). Falls der dokumentierte Weg von der
  Implementierung abweicht, ist das eine Doku-Inkonsistenz → in der Commit-Message
  als zweite Zeile vermerken.
