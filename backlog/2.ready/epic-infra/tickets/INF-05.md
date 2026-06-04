---
id: INF-05
title: Verschlüsseltes Backup-Skript (Mongo + Postgres + Volumes)
status: todo
depends_on: [INF-01]
stop_after: false
epic: infra
commit_type: feat(infra)
---

# INF-05 — Verschlüsseltes Backup-Skript (Mongo + Postgres + Volumes)

## Why
Geht der Server verloren, ist die pseudonymisierte Fallakte weg — Arbeit von
Wochen und der einzige strukturierte Stand der Krankengeschichte. Backups sind
Pflicht. Und weil es um Gesundheitsdaten eines Kindes geht (Art. 9 DSGVO), dürfen
die Sicherungen **nie** als Klartext herumliegen: mongodump, pg_dump und der
Volume-Snapshot werden verschlüsselt abgelegt, mit Retention. docs/security.md
fordert „Backup verschlüsselt" explizit.

## Scope
- `scripts/backup.sh`, `set -euo pipefail`:
  - **MongoDB**: `mongodump` **aus dem laufenden Container** (`docker exec`),
    Ausgabe in ein temporäres Arbeitsverzeichnis.
  - **Postgres/pgvector**: `pg_dump` **aus dem `vectordb`-Container**
    (`docker exec`), gleiches Arbeitsverzeichnis.
  - **Volume-Snapshot**: relevante benannte Volumes (LibreChat-Uploads,
    Meili-Daten) als Tar sichern.
  - **Verschlüsselung**: das gesamte Backup-Bündel mit `age` (oder `restic`)
    verschlüsseln; Klartext-Zwischenstände nach dem Verschlüsseln sicher löschen
    (`shred`/`rm`).
  - **Retention**: alte verschlüsselte Backups jenseits einer Aufbewahrungsfrist
    (z. B. 14 Tage) löschen.
  - Konfigurierbare Pfade/Recipient-Key über Umgebung (kein hartkodiertes Secret).

## Files
```
scripts/backup.sh   (NEU)
```

## Reality Check (Pflicht — vor Promotion nach `2.ready/`)

- [x] **Files in `Scope`/`Files`**: `scripts/backup.sh` existiert noch nicht
      (`ls scripts/backup.sh` → not found), wird NEU angelegt.
- [x] **`depends_on`-IDs**: INF-01 definiert die Container (`mongodb`, `vectordb`)
      und die benannten Volumes, gegen die `docker exec` / der Volume-Tar laufen —
      genau die Namen, die dieses Skript referenziert.
- [x] **Externe Voraussetzungen**: Ausführung erfordert laufende Container und
      einen `age`/`restic`-Verschlüsselungs-Recipient/Repo-Key — beides
      **Laufzeit/Deploy**, nicht Teil dieses Tickets. Hier wird das Skript nur
      geschrieben und statisch geprüft (shellcheck, `bash -n`). Hinweis in `## Notes`.
- [x] **Tooling**: `shellcheck`/`bash` als Shell-Tooling (CLAUDE.md). `age` bzw.
      `restic` sind Laufzeit-Abhängigkeiten auf dem Server (im Skript als
      Vorhandensein-Check), nicht für die statische Acceptance nötig.

## Acceptance
- [ ] `shellcheck scripts/backup.sh` ohne Findings.
- [ ] `bash -n scripts/backup.sh` (Syntax-Check) ok.
- [ ] `set -euo pipefail` vorhanden
      (`grep -F 'set -euo pipefail' scripts/backup.sh`).
- [ ] Ein expliziter Verschlüsselungsschritt ist vorhanden:
      `grep -E 'age|restic|gpg' scripts/backup.sh` liefert einen Treffer.
- [ ] mongodump und pg_dump laufen per `docker exec` gegen die Container
      (`grep -E 'docker exec.*(mongodump|pg_dump)' scripts/backup.sh`).
- [ ] **Negativ-Check**: Skript legt **keine** unverschlüsselten Dumps dauerhaft
      am Zielpfad ab — jeder Klartext-Zwischenstand wird nach der Verschlüsselung
      gelöscht (`grep -E 'shred|rm ' scripts/backup.sh` nach dem Verschlüsselungs-
      schritt; Sichtprüfung, dass am `DEST`/Zielpfad nur die `.age`/restic-Artefakte
      verbleiben).
- [ ] **Negativ-Check**: kein hartkodierter Schlüssel/Recipient im Skript
      (`grep -E 'AGE-SECRET-KEY|BEGIN.*PRIVATE' scripts/backup.sh` liefert nichts;
      Recipient/Repo kommt aus Umgebung).

## Out of scope
- Off-site-Transfer der Backups (S3/Storage-Box) → späteres Ticket, falls gewünscht.
- Restore-/Recovery-Skript → eigenes Ticket (Backup ohne getesteten Restore ist
  unvollständig, aber das ist ein separater Scope).
- Scheduling (cron/systemd-timer auf dem Server) → Deploy-/Runbook-Schritt
  (epic-onboarding).

## Notes
- **Externe Voraussetzung:** Ausführung braucht den laufenden Stack (INF-01
  deployed) und einen konfigurierten `age`-Recipient (öffentlicher Key) bzw. ein
  `restic`-Repository samt Passwort — beides wird auf dem Server gesetzt, nie im
  Repo. Dieses Ticket liefert nur das geprüfte Skript.
- `age` ist die schlanke Default-Empfehlung (ein Recipient-Public-Key, keine
  Repo-Verwaltung). `restic` ist die Alternative, wenn dedup + Off-site später
  gewünscht ist — eine der beiden, nicht beide.
- Klartext-Zwischenstände gehören in ein `mktemp -d`-Arbeitsverzeichnis mit
  `trap ... EXIT`-Cleanup, damit auch bei Abbruch nichts Unverschlüsseltes
  liegenbleibt.
