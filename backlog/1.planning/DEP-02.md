---
id: DEP-02
title: Domain & DNS auf den Server zeigen lassen
status: todo
depends_on: [DEP-01]
stop_after: true
epic: deploy
commit_type: chore(deploy)
---

# DEP-02 — Domain & DNS

> **Supervised.** Läuft mit dir, nicht im autonomen Loop.

## Why
Caddy braucht einen erreichbaren Hostnamen, um automatisch ein TLS-Zertifikat zu holen.

## Scope
- Subdomain wählen (z. B. `fall.deine-domain.de`).
- A-/AAAA-Record auf die Server-IP setzen.
- DNS-Propagation abwarten.

## Acceptance (manuell)
- [ ] `dig +short fall.deine-domain.de` liefert die Server-IP.
- [ ] Port 80/443 vom Server aus erreichbar.

## Notes
Hostname wird in DEP-03 in `Caddyfile`/`.env` eingetragen.

## Stop-Gate
DNS zeigt auf den Server. Weiter mit DEP-03 (Secrets & Konfiguration).
