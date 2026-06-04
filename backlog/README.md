# Backlog

Flache Pipeline, ein Markdown-File pro Ticket. Keine Epic-Unterordner — die
Epic-Zugehörigkeit steht im Frontmatter (`epic:`).

## Struktur
```
backlog/
├── README.md             # diese Datei
├── PLAN.md               # Projekt-Übersicht: Ziele, Modul-Karte, Abhängigkeitsgraph
├── AGENT-LOOP.md         # Operating-Manual für autonome Loop-Iteration
├── AGENT-TICKET.md       # Operating-Manual für genau ein Ticket
├── TICKET-TEMPLATE.md    # Vorlage (Frontmatter + Sektionen)
├── 1.planning/           # noch nicht baufertig — u. a. die Deploy-Tickets (supervised)
├── 2.ready/              # baufertig, flach: <ID>.md — der Loop greift hier zu
│   ├── INF-01.md … INF-05.md
│   ├── KB-01.md  … KB-04.md
│   ├── MCP-01.md … MCP-06.md
│   ├── GEN-01.md … GEN-03.md
│   └── ONB-01.md … ONB-03.md
└── 3.done/               # erledigte Tickets (per git mv aus 2.ready/)
```

Stage-Wechsel: `git mv backlog/2.ready/<ID>.md backlog/3.done/<ID>.md`.
`depends_on` referenziert **IDs** (nicht Pfade); ein Ticket ist ziehbar, sobald
alle seine Dependency-IDs in `3.done/` liegen.

## Loop ausführen
- **Autonom** (frische Session pro Ticket): `bash scripts/agent-loop.sh`
- **Status** (gruppiert nach epic): `bash scripts/agent-loop.sh status`
- **Einzel-Ticket** (manuell): „Bitte arbeite INF-01 nach `backlog/AGENT-TICKET.md` ab"

## Was hier NICHT hingehört
- Projekt-Übersicht / Modul-Karte / Abhängigkeiten → [PLAN.md](PLAN.md)
- Architektur/Datenfluss → [docs/architektur.md](../docs/architektur.md)
- Sicherheits-/Datenschutzregeln → [docs/security.md](../docs/security.md)
- Projektweite Lerneffekte/Gotchas → [AGENTS.md](../AGENTS.md) (`## Notes`)
