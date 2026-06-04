---
id: MCP-01
title: BioMCP in librechat.yaml einhängen
status: todo
depends_on: [INF-03]
stop_after: false
epic: mcp
commit_type: feat(mcp)
---

# MCP-01 — BioMCP in librechat.yaml einhängen

## Why
BioMCP ist ein fertiger MCP-Server, der fünf zentrale Quellen abdeckt (PubMed,
ClinVar, dbSNP, MyVariant/gnomAD, ClinicalTrials.gov). Ohne diesen Eintrag stellt
LibreChat dem Modell keine dieser Quellen bereit — Claude könnte Literatur und
Varianten-Frequenzen nicht live nachschlagen. Wir bauen nichts nach, wir hängen
den fertigen Server in die LibreChat-Konfiguration ein.

## Scope
- In `librechat.yaml` unter `mcpServers` einen Eintrag `biomcp` ergänzen:
  - Start als Container bzw. Command, der den BioMCP-Server im stdio-/MCP-Modus
    fährt (gemäß BioMCP-README: `biomcp run` über `uvx`/Container).
  - `env`-Block mit optionalem `NCBI_API_KEY` (nur höheres Rate-Limit, kann leer
    bleiben / aus einer Env-Variable gezogen werden — kein Hardcoding eines Keys).
  - Sprechender `description`-Eintrag, falls vom Schema unterstützt, damit klar ist,
    welche Quellen dieser Server bringt.
- `docs/mcp-biomcp.md` (NEU) anlegen: kurze deutsche Doku, die auflistet, welche
  Tools/Quellen über BioMCP verfügbar werden (PubMed, ClinVar, dbSNP,
  MyVariant/gnomAD, ClinicalTrials) und dass der NCBI-API-Key optional ist.

## Files
```
librechat.yaml          (erweitert: mcpServers.biomcp)
docs/mcp-biomcp.md      (NEU)
```

## Reality Check (Pflicht — vor Promotion nach `2.ready/`)
- [x] **Files in `Scope`/`Files`**: `librechat.yaml` wird von `INF-03`
      (`epic-infra`) angelegt → hier **erweitert**, nicht neu. `docs/mcp-biomcp.md`
      wird bewusst NEU angelegt (`docs/` existiert: `ls docs/` → `architektur.md`,
      `security.md`).
- [x] **`depends_on`-IDs**: `INF-03` ist im Backlog-Plan (`backlog/README.md`,
      Epic-Tabelle) als „laufende LibreChat-Konfiguration" vorgesehen, liegt aber
      noch nicht als Ticket vor → bis dahin im `## Notes` vermerkt, Loop zieht das
      Ticket erst, wenn `INF-03` in `done/` liegt.
- [x] **Externe Voraussetzungen**: NCBI-API-Key ist **optional** (nur Rate-Limit).
      Kein Secret zwingend nötig. Echter Tool-Aufruf braucht laufenden LibreChat →
      manueller Smoke-Test, im `## Notes` vermerkt.
- [x] **Tooling**: `python3` mit `yaml` (PyYAML) für die Acceptance vorhanden bzw.
      über `pip install pyyaml` nachrüstbar. Kein weiteres Tooling nötig.

## Acceptance
- [ ] `librechat.yaml` lädt fehlerfrei:
      `python3 -c "import yaml; yaml.safe_load(open('librechat.yaml'))"`
- [ ] Der Eintrag existiert:
      `python3 -c "import yaml; d=yaml.safe_load(open('librechat.yaml')); assert 'biomcp' in (d.get('mcpServers') or {}), 'biomcp fehlt'"`
- [ ] Kein NCBI-API-Key im Klartext eingecheckt:
      `! grep -Eiq 'NCBI_API_KEY:[[:space:]]*[A-Za-z0-9]' librechat.yaml`
      (Key kommt aus Env-Substitution `${NCBI_API_KEY}` oder bleibt leer).
- [ ] `docs/mcp-biomcp.md` existiert und nennt alle abgedeckten Quellen:
      `for q in PubMed ClinVar dbSNP MyVariant gnomAD ClinicalTrials; do grep -q "$q" docs/mcp-biomcp.md || { echo "fehlt: $q"; exit 1; }; done`

## Out of scope
- Eigene Tools nachbauen, die BioMCP schon liefert (PubMed/ClinVar/dbSNP/MyVariant/
  ClinicalTrials) — bewusst nicht, single source of truth.
- Den BioMCP-Server forken oder patchen — er wird as-is eingehängt.
- Compose-Service für BioMCP, falls `INF-03` BioMCP bereits als Container bringt —
  hier nur der `mcpServers`-Eintrag in `librechat.yaml`.

## Notes
- `INF-03` (laufende LibreChat-Config) ist Voraussetzung und noch nicht als Ticket
  geschrieben. Bis dahin bleibt MCP-01 für den Loop nicht ziehbar (Dependency
  nicht in `done/`).
- BioMCP-Start-Varianten laut Projekt-README prüfen (`uvx biomcp run` vs. Container).
  Die in `epic-infra` gewählte Variante (Command vs. Container im Compose-Netz)
  übernehmen, damit beide Server-Einträge konsistent sind.
- **Echter Test braucht laufenden LibreChat** → Smoke-Test manuell (in
  `2.ready/epic-mcp/SMOKE-TEST.md` bzw. am Epic-Ende durch den Menschen): Tool in
  einem Chat aufrufen und Antwort einer der fünf Quellen prüfen.
