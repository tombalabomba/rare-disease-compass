# rare-case-assistant

Selbst-gehosteter, datenschutzfreundlicher KI-Recherche-Assistent für einen
komplexen pädiatrischen Krankheitsfall (Verdachtsrichtung früh beginnende,
ggf. monogene Darmentzündung / VEO-IBD). Das System verknüpft eine **private,
strukturierte Fallakte** mit dem **öffentlich verfügbaren medizinischen Wissen**
(Literatur, Datenbanken für seltene Krankheiten, Genetik) und macht es über eine
einfache Chat-Oberfläche durchsuchbar.

> **Kein Medizinprodukt. Keine Diagnose.** Dieses System ist Recherche- und
> Entscheidungsunterstützung. Jede medizinische Schlussfolgerung gehört in die
> Hände behandelnder Fachärztinnen und Fachärzte.

## Was es ist

```
┌──────────────────┐        ┌──────────────────────────────┐
│  Matze (Browser) │──────▶ │  LibreChat (Login, Verlauf)  │
└──────────────────┘  HTTPS │   + RAG-Wissensbasis         │
┌──────────────────┐        │   = die private Fallakte     │
│  Thomas (Kurator)│──────▶ │   + MCP-Werkzeuge            │
└──────────────────┘        │   = Live-Datenanbindung      │
                            └───────────────┬──────────────┘
                                            │ fragt live ab
        ┌───────────────────────────────────┼────────────────────────────┐
        ▼                 ▼                  ▼                ▼            ▼
   PubMed/EuropePMC   ClinVar/gnomAD   Monarch/Orphanet  PubCaseFinder  Exomiser
   (Literatur)        (Varianten)      (Krankheits-Graph)  (DDx)        (lokal, Genetik)
```

Zwei strikt getrennte Datenwelten:

- **Privat (kommt rein, bleibt auf dem Server / lokal):** die Fallakte. Arztbriefe,
  Befunde, Laborwerte, Symptomverlauf (HPO-codiert), Genetik-Zusammenfassung.
- **Öffentlich (wird nur abgefragt, nie befüllt):** medizinische Datenbanken.

## Komponenten

| Bereich | Was | Epic |
|---|---|---|
| Infrastruktur | Docker-Stack (LibreChat + Postgres/pgvector + RAG), Caddy/HTTPS, Hetzner-Provisioning, Backups | `epic-infra` |
| Datenanbindung | BioMCP (PubMed/ClinVar/gnomAD/Trials) + eigener MCP (Monarch/Orphanet/EuropePMC/PubCaseFinder) | `epic-mcp` |
| Wissensbasis | HPO-codierte Fallakten-Struktur, Pseudonymisierung, RAG-Ingestion, System-Prompt | `epic-knowledge` |
| Genetik | Exomiser-Runner (lokal) für VCF + HPO → priorisierte Kandidaten | `epic-genetics` |
| Onboarding | Runbook (Betreiber), Nutzer-Guide (Matze), Einwilligungs-/Datenschutz-Vorlage | `epic-onboarding` |

## Autonomer Bau

Das gesamte Projekt ist als Backlog von Tickets in `backlog/2.ready/` geplant.
Eine autonome Loop baut es Ticket für Ticket ab:

```bash
bash scripts/agent-loop.sh status     # Überblick
bash scripts/agent-loop.sh            # autonom abarbeiten (frische Session pro Ticket)
```

Details: [backlog/README.md](backlog/README.md) und [backlog/AGENT-LOOP.md](backlog/AGENT-LOOP.md).

## Datenschutz auf einen Blick

- Patientendaten **nie** im Repo (siehe [.gitignore](.gitignore)) und nie in öffentlichen Datenbanken.
- Fallakte pseudonymisiert (Initialen), liegt verschlüsselt auf dem Hetzner-Server (EU).
- Genetik-Rohdaten (VCF) werden **lokal** ausgewertet, nur Ergebnisse fließen in die Akte.
- Chat-Inhalte gehen zur Inferenz an die Anthropic-API (kein Training auf API-Daten, DPA).
- Vollständig: [docs/security.md](docs/security.md).
