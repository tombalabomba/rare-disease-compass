---
id: DEP-01
title: Hetzner-Server provisionieren & härten
status: todo
depends_on: [INF-04]
stop_after: true
epic: deploy
commit_type: chore(deploy)
---

# DEP-01 — Hetzner-Server provisionieren & härten

> **Supervised.** Läuft NICHT im autonomen Loop (braucht echten Server-Zugang).
> Gemeinsame Session: du gibst SSH-Zugang, Claude führt durch. Deshalb in `1.planning/`.

## Why
Bevor irgendetwas deployt werden kann, muss der Server existieren und gehärtet sein.

## Scope
- Hetzner-Cloud-Server in einem DE-Rechenzentrum erstellen (Ubuntu LTS).
- AVV im Hetzner-Konto aktivieren.
- `scripts/provision-server.sh` (aus INF-04) auf dem Server ausführen:
  Docker, Deploy-User, ufw (22/80/443), fail2ban, unattended-upgrades, SSH-Härtung.
- SSH nur per Key, Passwort-Login aus.

## Acceptance (manuell, beim Deployment)
- [ ] `docker --version` und `docker compose version` laufen auf dem Server.
- [ ] `ufw status` zeigt nur 22/80/443.
- [ ] SSH-Passwort-Login deaktiviert (Key-only).
- [ ] AVV im Hetzner-Konto aktiv.

## Notes
Manueller, sicherheitskritischer Schritt. Server-Zugangsdaten gehören NICHT ins Repo.

## Stop-Gate
Nach diesem Ticket: Server steht und ist gehärtet. Weiter mit DEP-02 (DNS).
