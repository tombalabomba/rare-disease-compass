---
id: DEP-04
title: Stack hochfahren, TLS & MCP-Tools verifizieren
status: todo
depends_on: [DEP-03, MCP-01, MCP-06]
stop_after: true
epic: deploy
commit_type: chore(deploy)
---

# DEP-04 — Stack starten & Smoke-Test

> **Supervised.** End-to-End-Checks gegen den laufenden Server (siehe `backlog/SMOKE-TEST.md`).

## Why
Erst auf dem laufenden Stack lassen sich TLS und die Live-Datenanbindung prüfen.

## Scope
- `docker compose up -d` auf dem Server.
- Caddy holt automatisch ein Let's-Encrypt-Zertifikat.
- Smoke-Test der MCP-Tools (BioMCP + eigener Server) in einem Test-Chat.

## Acceptance (manuell, siehe SMOKE-TEST.md)
- [ ] `https://fall.deine-domain.de` lädt mit gültigem TLS.
- [ ] Alle Container `healthy` (`docker compose ps`).
- [ ] Test-Frage löst einen PubMed- und einen Monarch/PubCaseFinder-Call aus.
- [ ] HTTP wird auf HTTPS umgeleitet; Security-Header gesetzt.

## Notes
Bei TLS-Problemen: DNS (DEP-02) und Port 80 erreichbar prüfen.

## Stop-Gate
App läuft öffentlich erreichbar mit TLS. Weiter mit DEP-05 (Login & Akte).
