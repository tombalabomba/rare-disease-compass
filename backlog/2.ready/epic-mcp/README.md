# Epic: Datenanbindung (`epic-mcp`)

**Status:** geplant
**Hängt ab von:** `epic-infra` (Docker-Stack + LibreChat müssen stehen)

## Ziel

Claude im Chat bekommt **Live-Zugriff** auf das öffentlich verfügbare medizinische
Wissen — als MCP-Werkzeuge, die LibreChat dem Modell bereitstellt. Zwei Bausteine:

1. **BioMCP** ([genomoncology/biomcp](https://github.com/genomoncology/biomcp)) —
   ein **fertiger** MCP-Server. Deckt PubMed, ClinVar, dbSNP, MyVariant (inkl.
   gnomAD-Frequenzen) und ClinicalTrials.gov ab. Wird nur **konfiguriert und
   eingehängt**, nicht nachgebaut.
2. **Eigener FastMCP-Server** (`mcp-server/`, Python 3.11) — deckt die Lücken, die
   BioMCP nicht abdeckt: Monarch Initiative, Orphanet, Europe PMC, PubCaseFinder,
   Phen2Gene.

Beide Server fragen öffentliche APIs **nur ab** (read-only), befüllen sie nie und
bekommen niemals die private Fallakte zu sehen. Siehe `docs/architektur.md` und
`docs/security.md`.

## Defaults & Entscheidungen

- **Sprache:** Doku/Tickets/Commit-Bodies deutsch, Code/Tool-Namen englisch (CLAUDE.md).
- **BioMCP nicht nachbauen.** Was BioMCP kann, baut der eigene Server nicht doppelt
  (single source of truth). Der eigene Server deckt ausschließlich die Lücken.
- **Höflicher Netzwerk-Zugriff (eigener Server):** zentraler async-HTTP-Client mit
  In-Memory-Cache (TTL), Rate-Limit (öffentliche APIs nicht hämmern), Timeouts,
  begrenzten Retries mit Backoff und sprechendem `User-Agent`. Jedes Tool nutzt
  diesen Client — kein direktes `httpx.get` in den Tool-Modulen.
- **Tool-Beschreibungen sind Doku für Claude.** Jedes Tool hat ein präzises
  Pydantic-Schema und einen deutschen Docstring, der Eingabe (oft eine Liste von
  HPO-IDs wie `HP:0002014`), Ausgabe und Quelle benennt. Claude liest diese als
  Tool-Beschreibung.
- **Read-only, keine PII.** Tools nehmen nur öffentliche Identifier (HPO-IDs, Gene,
  Krankheits-IDs, Suchbegriffe) entgegen. Niemals Patientendaten an externe APIs.
- **Container-Isolation:** der eigene MCP-Server läuft als Service im internen
  Docker-Netz und wird **nicht** nach außen exponiert (nur LibreChat spricht ihn an).
- **API-Keys optional:** NCBI-API-Key (BioMCP) erhöht nur das Rate-Limit, ist
  optional. Kein Tool des eigenen Servers braucht einen Key (alle Quellen offen).

## Modul-Karte

```
librechat.yaml                         # mcpServers.biomcp + mcpServers.rare-case
docker-compose.yml                     # Service "mcp-server" (internes Netz)
docs/mcp-biomcp.md                     # welche Tools BioMCP bereitstellt

mcp-server/
├── pyproject.toml                     # fastmcp, httpx, pydantic + ruff/pytest
├── Dockerfile
├── README.md
└── app/
    ├── server.py                      # FastMCP-Instanz + Tool-Registry
    ├── http_client.py                 # async-Client: Cache, Rate-Limit, Retry, Timeout
    ├── tools/
    │   ├── monarch.py                 # disease_by_phenotypes, gene_to_diseases, disease_detail
    │   ├── orphanet.py                # rare-disease lookup, Gene/Vererbung
    │   ├── europepmc.py               # search, get_fulltext_links, citations
    │   ├── pubcasefinder.py           # ranked_diseases(HPO-Liste)
    │   └── phen2gene.py               # candidate_genes(HPO-Liste)
    └── tests/                         # pytest, HTTP gemockt
```

Quellen-Abdeckung im Überblick:

| Quelle | Wer deckt ab | Zugriff |
|---|---|---|
| PubMed, ClinVar, dbSNP, MyVariant/gnomAD, ClinicalTrials | **BioMCP** | über BioMCP |
| Monarch Initiative (Phänotyp↔Gen↔Krankheit, integriert OMIM/Orphanet/GARD/NORD) | eigener Server | REST |
| Orphanet / Orphadata | eigener Server | REST |
| Europe PMC | eigener Server | REST |
| PubCaseFinder (HPO → gerankte seltene Krankheiten) | eigener Server | REST |
| Phen2Gene (HPO → Kandidatengene) | eigener Server | REST |

## Ticket-Liste (Baureihenfolge über `depends_on`)

| ID | Titel | depends_on | commit_type |
|---|---|---|---|
| MCP-01 | BioMCP in `librechat.yaml` einhängen | `[INF-03]` | `feat(mcp)` |
| MCP-02 | Eigener FastMCP-Server: Scaffold + HTTP-Basis | `[]` | `feat(mcp)` |
| MCP-03 | Tools: Monarch + Orphanet | `[MCP-02]` | `feat(mcp)` |
| MCP-04 | Tool: Europe PMC | `[MCP-02]` | `feat(mcp)` |
| MCP-05 | Tools: PubCaseFinder + Phen2Gene | `[MCP-02]` | `feat(mcp)` |
| MCP-06 | Eigenen MCP in Compose + `librechat.yaml` verdrahten | `[MCP-03, MCP-04, MCP-05, INF-01, INF-03]` | `feat(mcp)` |

**Reihenfolge-Logik:**
- MCP-02 ist die Wurzel des eigenen Servers (kein Dependency, kann sofort starten).
- MCP-03/04/05 bauen je eigene Tool-Module auf MCP-02 auf — parallel ziehbar,
  sobald MCP-02 done ist.
- MCP-01 (BioMCP) hängt nur an der laufenden LibreChat-Config (`INF-03`) und ist
  unabhängig vom eigenen Server.
- MCP-06 verdrahtet den fertigen eigenen Server in Compose (`INF-01`) und
  LibreChat (`INF-03`) — braucht daher alle Tool-Tickets **und** die Infra.

**Externe Abhängigkeiten aus `epic-infra` (noch nicht geschrieben, im Backlog-Plan
vorgesehen):**
- `INF-01` — Docker-Compose-Stack (LibreChat + Postgres + RAG)
- `INF-03` — laufende LibreChat-Konfiguration (`librechat.yaml` existiert)

Solange diese Tickets nicht in einem `done/`-Ordner liegen, zieht der Loop MCP-01
und MCP-06 nicht. MCP-02..05 sind davon unberührt und sofort baubar.

## Smoke-Test (Mensch, am Epic-Ende)

Echte End-to-End-Tests (LibreChat startet, Claude ruft ein Tool live auf, BioMCP
und der eigene Server antworten) sind **kein** Teil der maschinellen Acceptance —
sie brauchen den laufenden Stack. Sie gehören in `SMOKE-TEST.md` und macht der
Mensch, sobald `epic-infra` und dieses Epic durch sind.
