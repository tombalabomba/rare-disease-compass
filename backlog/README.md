# Backlog

Alle laufende und geplante Arbeit. Zwei orthogonale Achsen:
- **Stage** (Pipeline): `1.planning/` → `2.ready/` → `3.done/`
- **Form** (Einzelticket oder Epic): flaches `.md` direkt in der Stage, oder
  Epic-Ordner als Unterordner der Stage

## Struktur
```
backlog/
├── README.md             # diese Datei
├── AGENT-LOOP.md         # Operating-Manual für autonome Loop-Iteration
├── AGENT-TICKET.md       # Operating-Manual für genau ein Ticket
├── TICKET-TEMPLATE.md    # Vorlage (Frontmatter + Sektionen)
├── 1.planning/           # Idee notiert, noch nicht implementations-fertig
├── 2.ready/              # spezifiziert, sofort ziehbar (Loop greift hier zu)
│   └── epic-<slug>/
│       ├── README.md     # Ziel, Status, Entscheidungen, Modul-Karte
│       ├── tickets/      # offene Tickets
│       └── done/         # erledigte Tickets (per git mv aus tickets/)
└── 3.done/               # erledigte Flat-Tickets (Archiv)
```
Stage-Wechsel: `git mv` über Datei bzw. ganzen Epic-Ordner.

## Epics (Baureihenfolge über `depends_on`)

| Epic | Slug | Inhalt | hängt ab von |
|---|---|---|---|
| Infrastruktur | `epic-infra` | Docker-Stack, Caddy/HTTPS, Hetzner-Provisioning, Backups | — |
| Wissensbasis | `epic-knowledge` | Fallakten-Schema (HPO), Pseudonymisierung, RAG-Ingestion, System-Prompt | infra |
| Datenanbindung | `epic-mcp` | BioMCP + eigener MCP (Monarch/Orphanet/EuropePMC/PubCaseFinder) | infra |
| Genetik | `epic-genetics` | Exomiser-Runner (lokal), VCF+HPO → Kandidaten → Akte | knowledge |
| Onboarding | `epic-onboarding` | Betreiber-Runbook, Nutzer-Guide, Einwilligungs-Vorlage | infra, knowledge, mcp |

Die `depends_on`-Felder der einzelnen Tickets erzwingen die Reihenfolge feiner.
Der Loop zieht immer das nächste Ticket, dessen Dependencies in `done/` liegen.

## Loop ausführen
- **Autonom** (frische Session pro Ticket): `bash scripts/agent-loop.sh`
- **Status**: `bash scripts/agent-loop.sh status`
- **Einzel-Ticket** (manuell): „Bitte arbeite INF-01 nach `backlog/AGENT-TICKET.md` ab"

## Was hier NICHT hingehört
- Architektur/Datenfluss → [docs/architektur.md](../docs/architektur.md)
- Sicherheits-/Datenschutzregeln → [docs/security.md](../docs/security.md)
- Projektweite Lerneffekte/Gotchas → [AGENTS.md](../AGENTS.md) (`## Notes`)
