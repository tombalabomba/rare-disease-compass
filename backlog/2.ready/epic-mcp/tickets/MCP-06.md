---
id: MCP-06
title: Eigenen MCP in Compose + librechat.yaml verdrahten
status: todo
depends_on: [MCP-03, MCP-04, MCP-05, INF-01, INF-03]
stop_after: false
epic: mcp
commit_type: feat(mcp)
---

# MCP-06 — Eigenen MCP in Compose + librechat.yaml verdrahten

## Why
Der eigene MCP-Server (MCP-02..05) existiert dann als Code, ist aber noch nicht
Teil des laufenden Systems. Dieses Ticket macht ihn betriebsbereit: als Service im
Docker-Compose-Stack (internes Netz) und als `mcpServers`-Eintrag in
`librechat.yaml`, damit LibreChat Claude die Tools bereitstellt. Erst danach kann
Claude Monarch/Orphanet/Europe PMC/PubCaseFinder/Phen2Gene live abfragen. Aus
Datenschutz-/Härtungsgründen läuft der Server **nur intern**, nie nach außen
exponiert (Defense-in-Depth, siehe `docs/security.md`).

## Scope
- `docker-compose.yml` (erweitert): Service `mcp-server`:
  - `build: ./mcp-server` (Dockerfile aus MCP-02).
  - im **internen** Docker-Netz des Stacks; **keine** `ports:`-Veröffentlichung
    nach außen (nur LibreChat erreicht den Dienst über das interne Netz).
  - sinnvolle `restart`-Policy; optional `NCBI_API_KEY` nicht nötig (eigener Server
    braucht keinen Key).
- `librechat.yaml` (erweitert): `mcpServers.rare-case`-Eintrag, der auf diesen
  Server zeigt (Transport/Host gemäß der in `epic-infra` gewählten Konvention,
  konsistent mit dem BioMCP-Eintrag aus MCP-01). Sprechende `description`.

## Files
```
docker-compose.yml      (erweitert: service mcp-server)
librechat.yaml          (erweitert: mcpServers.rare-case)
```

## Reality Check (Pflicht — vor Promotion nach `2.ready/`)
- [x] **Files in `Scope`/`Files`**: `docker-compose.yml` und `librechat.yaml`
      stammen aus `epic-infra` (`INF-01`/`INF-03`) → hier **erweitert**, nicht neu.
      Existenz gilt erst nach deren `done`.
- [x] **`depends_on`-IDs**: MCP-03/04/05 liefern die Tools + das baubare
      `mcp-server/`-Image (alle bauen auf MCP-02). `INF-01` liefert
      `docker-compose.yml`, `INF-03` die laufende `librechat.yaml`.
- [x] **Externe Voraussetzungen**: laufender Stack ist **nicht** für die
      maschinelle Acceptance nötig (`docker compose config` validiert statisch,
      ohne Container zu starten). Echter End-to-End-Test braucht den Stack →
      manueller Smoke-Test, im `## Notes` vermerkt.
- [x] **Tooling**: `docker compose` (für `config`-Validierung) und `python3` mit
      `yaml` vorhanden.

## Acceptance
- [ ] Compose validiert statisch: `docker compose config -q`
      (bzw. `docker compose -f docker-compose.yml config -q`) ohne Fehler.
- [ ] Service vorhanden: `docker compose config` listet `mcp-server`
      (`docker compose config | grep -q 'mcp-server'`).
- [ ] **Negativ-Check (Härtung):** `mcp-server` ist **nicht** nach außen exponiert —
      kein veröffentlichter Port. Prüfbar über die normalisierte Config:
      `python3 -c "import yaml,subprocess; c=yaml.safe_load(subprocess.check_output(['docker','compose','config'])); s=c['services']['mcp-server']; assert not s.get('ports'), 'mcp-server darf keine ports veröffentlichen'"`
- [ ] `librechat.yaml` lädt:
      `python3 -c "import yaml; yaml.safe_load(open('librechat.yaml'))"`
- [ ] Eintrag vorhanden:
      `python3 -c "import yaml; d=yaml.safe_load(open('librechat.yaml')); m=d.get('mcpServers') or {}; assert 'rare-case' in m, 'rare-case mcpServer fehlt'"`

## Out of scope
- BioMCP-Eintrag — MCP-01.
- Änderungen an Tool-Code — MCP-03..05.
- Reverse-Proxy/Caddy-Regeln — `epic-infra`. Hier wird **nichts** nach außen
  geöffnet, also keine Proxy-Anpassung nötig.

## Notes
- `INF-01` (Compose-Stack) und `INF-03` (LibreChat-Config) sind im Backlog-Plan
  (`backlog/README.md`) vorgesehen, aber noch nicht als Tickets geschrieben → bis
  dahin zieht der Loop MCP-06 nicht (Dependencies nicht in `done/`).
- Transport zwischen LibreChat und dem eigenen Server muss zum FastMCP-Start aus
  MCP-02 passen (stdio-Command vs. Netzwerk-Transport). Die in `epic-infra`
  gewählte Variante für BioMCP (MCP-01) konsistent übernehmen.
- **Echter End-to-End-Test braucht laufenden Stack** → Smoke-Test manuell
  (`2.ready/epic-mcp/SMOKE-TEST.md` bzw. Epic-Ende): Stack hochfahren, in einem
  Chat ein `rare-case`-Tool (z. B. `disease_by_phenotypes`) mit einer HPO-Liste
  aufrufen und die Antwort prüfen.
