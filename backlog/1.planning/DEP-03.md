---
id: DEP-03
title: Secrets erzeugen & Konfiguration befüllen
status: todo
depends_on: [DEP-02, INF-01, INF-02, INF-03]
stop_after: true
epic: deploy
commit_type: chore(deploy)
---

# DEP-03 — Secrets & Konfiguration

> **Supervised.** Secrets gehören NIE ins Repo. Nur auf dem Server.

## Why
Der Stack braucht echte Secrets und den echten Hostnamen, um zu starten.

## Scope
- Repo auf den Server klonen (oder per Deploy ziehen).
- `.env` aus `.env.example` erzeugen und befüllen: `ANTHROPIC_API_KEY`,
  `JWT_SECRET`, `CREDS_KEY`, `MEILI_MASTER_KEY`, `POSTGRES_*`, `MONGO_URI` —
  starke, einzigartige Werte (z. B. `openssl rand -hex 32`).
- Hostname in `Caddyfile` / `.env` eintragen (aus DEP-02).
- System-Prompt aus `config/system-prompt.md` im Agent hinterlegen.

## Acceptance (manuell)
- [ ] `.env` vollständig, keine Platzhalter mehr.
- [ ] `git status` zeigt `.env` als ignoriert (nicht eingecheckt).
- [ ] `docker compose config` auf dem Server validiert mit echten Werten.

## Notes
`openssl rand -hex 32` für Secrets. Anthropic-DPA vorher abschließen.

## Stop-Gate
Konfiguration steht. Weiter mit DEP-04 (Stack starten).
