---
id: INF-04
title: Hetzner-Provisioning-Skript (Docker, Firewall, Härtung)
status: todo
depends_on: []
stop_after: false
epic: infra
commit_type: feat(infra)
---

# INF-04 — Hetzner-Provisioning-Skript (Docker, Firewall, Härtung)

## Why
Der Stack braucht eine gehärtete Basis. Ein frischer Ubuntu-Server auf Hetzner
ist ohne Härtung angreifbar — bei Gesundheitsdaten eines Kindes inakzeptabel.
Dieses Skript bringt einen Server reproduzierbar in den in docs/security.md
geforderten Mindeststandard: Docker, non-root Deploy-User, Firewall (nur
22/80/443), fail2ban, automatische Sicherheitsupdates, SSH-Härtung. Manuelles
Klick-Setup wäre fehleranfällig und nicht wiederholbar.

## Scope
- `scripts/provision-server.sh`, idempotent, `set -euo pipefail`:
  - **Docker + Compose-Plugin** installieren (offizielles Repo), nur wenn nicht
    vorhanden (Guard).
  - **Non-root Deploy-User** anlegen (Guard: nur wenn User fehlt), in `docker`-
    und `sudo`-Gruppe.
  - **ufw**: Default deny incoming / allow outgoing; nur 22 (SSH), 80, 443 (Caddy)
    erlauben; `ufw --force enable` (idempotent).
  - **fail2ban** installieren und aktivieren (Guard).
  - **unattended-upgrades** installieren und für Sicherheitsupdates konfigurieren.
  - **SSH-Härtung**: `PasswordAuthentication no`, `PermitRootLogin no` in der
    sshd-Config setzen (idempotent, nur ändern wenn nicht schon gesetzt),
    sshd-Reload.
  - Klare Abschnitts-Echos, damit ein erneuter Lauf nachvollziehbar ist.

## Files
```
scripts/provision-server.sh   (NEU)
```

## Reality Check (Pflicht — vor Promotion nach `2.ready/`)

- [x] **Files in `Scope`/`Files`**: `scripts/provision-server.sh` existiert noch
      nicht (`ls scripts/provision-server.sh` → not found), wird NEU angelegt
      (`scripts/`-Verzeichnis ggf. mit `mkdir -p` im Skript-Schreibschritt anlegen).
- [x] **`depends_on`-IDs**: keine — Provisioning ist von Compose/Caddy unabhängig
      und kann parallel zu INF-01 gezogen werden (README-Graph).
- [x] **Externe Voraussetzungen**: ein **echter** Hetzner-Server existiert noch
      **nicht**. Dieses Ticket **schreibt** nur das Skript und prüft es statisch
      (shellcheck, `bash -n`). Der Lauf gegen die Maschine ist ein manueller
      Schritt nach dem Epic. Hinweis in `## Notes`. `stop_after: false`, weil hier
      ausschließlich die Datei entsteht.
- [x] **Tooling**: `shellcheck` und `bash` sind das in CLAUDE.md vorgesehene
      Shell-Tooling. Falls `shellcheck` lokal fehlt → vor Acceptance installieren
      (`brew install shellcheck` / `apt-get install shellcheck`).

## Acceptance
- [ ] `shellcheck scripts/provision-server.sh` ohne Findings.
- [ ] `bash -n scripts/provision-server.sh` (Syntax-Check) ok.
- [ ] `set -euo pipefail` ist vorhanden
      (`grep -F 'set -euo pipefail' scripts/provision-server.sh`).
- [ ] Idempotente Guards vorhanden: vor jeder Installation/Änderung wird geprüft,
      ob der Zustand schon existiert (z. B. `command -v docker`, `id deploy`,
      `grep`-Check der sshd-Config). Nachweis per `grep -E 'command -v|id |grep '`
      im Skript + Sichtprüfung der Guard-Struktur.
- [ ] **Negativ-Check**: Skript öffnet **keine** anderen Ports als 22/80/443 —
      `grep -E 'ufw allow' scripts/provision-server.sh` listet ausschließlich
      22, 80, 443.
- [ ] **Negativ-Check**: keine Secrets/Klartext-Passwörter im Skript
      (`grep -E 'PASSWORD=|sk-ant-|BEGIN.*PRIVATE' scripts/provision-server.sh`
      liefert nichts).

## Out of scope
- Tatsächliches Provisionieren der echten Maschine → manueller Schritt nach Epic.
- Anlegen/Deploy des Compose-Stacks auf dem Server → separater Deploy-Schritt.
- IP-Allowlisting für SSH (in security.md als „idealerweise" genannt) → optionaler
  späterer Hardening-Schritt, hier nicht erzwungen.
- Disk-Encryption-Setup (Hetzner-seitig zur Server-Erstellung) → manuell.

## Notes
- **Externe Voraussetzung:** Der Lauf erfordert einen existierenden Ubuntu-Server
  (Hetzner Cloud, EU-Rechenzentrum, AVV aktiv — siehe docs/security.md). Dieses
  Ticket liefert nur das geprüfte Skript; der Aufruf gegen `root@<server>` ist ein
  bewusster manueller Schritt.
- Das Skript muss als root bzw. via sudo laufen — am Skriptanfang prüfen und mit
  klarer Meldung abbrechen, wenn nicht.
- Idempotenz ist hart gefordert: ein zweiter Lauf darf nichts kaputt machen und
  keine Duplikate (User, ufw-Regeln, sshd-Zeilen) erzeugen.
