# RareDiseaseCompass

Ein lokaler, datenschutzfreundlicher KI-Recherche-Assistent für komplexe und
seltene Krankheitsfälle — gedacht als **„Dex für seltene Erkrankungen"**. Er
verknüpft eine **private, strukturierte Fallakte** (lokaler Ordner) mit dem
**öffentlich verfügbaren medizinischen Wissen** (Literatur, Datenbanken für
seltene Krankheiten, Genetik) über agenten-native CLIs, die du direkt in
**Claude Code** nutzt.

> **Kein Medizinprodukt. Keine medizinische Beratung. Keine Diagnose.**
> Dieses Open-Source-Werkzeug ist Recherche- und Entscheidungs*unterstützung*.
> Jede medizinische Schlussfolgerung gehört in die Hände qualifizierter
> Ärztinnen und Ärzte. Nutzung auf eigene Verantwortung.

## Idee in einem Satz

Claude Code + ein Satz CLIs auf öffentliche Medizin-APIs + ein lokaler Ordner mit
der Fallakte = ein persönlicher Recherche-Assistent, der das Weltwissen immer durch
deinen konkreten Fall filtert. Kein Server, keine Cloud-Infrastruktur, keine
Installation für Nicht-Techniker außer einem einmaligen Setup.

```
                 ┌─────────────────────────────┐
   Fallakte ────▶│         Claude Code         │
  (lok. Ordner)  │  liest Akte · ruft CLIs auf │────▶ Antwort mit Quellen
                 └──────────────┬──────────────┘      + Fragen für den Arzt
                                │ ruft auf
   ┌────────────────────────────┼─────────────────────────────┐
   ▼            ▼               ▼              ▼               ▼
 PubMed     ClinVar/gnomAD   Monarch/Orphanet  PubCaseFinder  Exomiser
(Literatur) (Varianten)     (Krankheits-Graph) (DDx, HPO)    (lokal, Genetik)
```

Jede CLI folgt dem **Printing-Press-Muster**: agenten-nativ, mit lokaler
SQLite-History (du baust dir über die Zeit einen durchsuchbaren Recherche-Speicher
auf) und zusammengesetzten Abfragen, die eine rohe API nicht direkt beantwortet.

## Komponenten

| Bereich | Was | Epic |
|---|---|---|
| Setup | Lokales Projekt-Layout, Installer, Claude-Code-Konfiguration | `setup` |
| Daten-CLIs | Agenten-native CLIs: PubMed, ClinVar/gnomAD, Monarch, Orphanet, Europe PMC, PubCaseFinder, Phen2Gene | `cli` |
| Wissensbasis | HPO-codierte Fallakten-Struktur, PII-Guard, Assistenten-Instruktionen | `knowledge` |
| Genetik | Exomiser lokal: VCF + HPO → priorisierte Kandidaten | `genetics` |
| Experience | Companion-Persona, Ton-Adaption, Skills-Schicht, Onboarding-Flow | `experience` |
| Onboarding | Setup-Runbook, Nutzer-Guide, Einwilligungs-/Datenschutz-Vorlage | `onboarding` |

## Angeschlossene Datenbanken

Alle öffentlichen Quellen werden **live abgefragt** (nie kopiert, nie mit
Patientendaten befüllt). Jede Abfrage landet zusätzlich in einer lokalen
SQLite-History, die den „seit-letzter-Sitzung-neu"-Hinweis speist.

| Datenbank | Wofür | Befehl | Auth |
|---|---|---|---|
| **PubMed** (NCBI E-utilities) | wissenschaftliche Literatur | `rdc pubmed` | optionaler API-Key |
| **Europe PMC** | Literatur inkl. Volltext/Preprints | `rdc europepmc` | keine |
| **ClinVar / gnomAD / MyVariant** | Bedeutung einer Genvariante + Häufigkeit in der Bevölkerung | `rdc variant` | optionaler API-Key |
| **Monarch Initiative** | Krankheits-Graph (Phänotyp ↔ Gen ↔ Krankheit); integriert OMIM, Orphanet, GARD, NORD | `rdc monarch` | keine |
| **Orphanet** | Referenz für seltene Krankheiten (Gene, Vererbung) | `rdc orphanet` | keine |
| **PubCaseFinder** | phänotyp-getriebene Differentialdiagnose: HPO-Symptome → gerankte Krankheiten | `rdc pubcasefinder` | keine |
| **Phen2Gene** | HPO-Symptome → Kandidatengene | `rdc phen2gene` | keine |
| **Exomiser** | Genetik **lokal**: VCF + HPO → priorisierte Varianten/Krankheiten | `genetics/` (Docker) | lokal |

Die Befehle lassen sich kombinieren (`rdc compound`), und Claude Code ruft sie im
Gespräch selbstständig auf, je nach Frage. Details: [docs/architektur.md](docs/architektur.md).

## Repo-Struktur: Produkt vs. Bau-Werkzeug

Klar getrennt, damit man sofort sieht, was man als Nutzer braucht und was nur dem
Entwickeln dient:

```
RareDiseaseCompass/
├── cli/          ← PRODUKT: die installierbaren Daten-CLIs (rdc)
├── skills/       ← PRODUKT: die /Workflows (erklär-mir, differential, …)
├── config/       ← PRODUKT: Assistenten-Persona + Ton-Adaption
├── tools/        ← PRODUKT: PII-Guard, Fallakten-Validierung
├── genetics/     ← PRODUKT: Exomiser-Runner (lokal)
├── docs/         ← PRODUKT: Nutzer-Doku, Vorlagen, Runbook
├── README · LICENSE · CONTRIBUTING · CLAUDE.md · AGENTS.md
└── dev/          ← NUR BAU-WERKZEUG (für Nutzer irrelevant)
    ├── backlog/      Tickets + Planung
    └── agent-loop.sh autonome Build-Loop
```

**Als Nutzer brauchst du `dev/` nie.** Du installierst die CLI (`pipx install ./cli`)
und kopierst dir `skills/`, `config/` und die Vorlagen. Das `dev/`-Verzeichnis ist
die Werkstatt, in der das Projekt gebaut wird — transparent im Repo, aber kein Teil
des nutzbaren Produkts.

## Loslegen (sobald gebaut)

```bash
# 1. CLIs installieren (Setup-Epic)
pipx install ./cli        # oder das mitgelieferte setup-Skript

# 2. Fallakte anlegen (aus docs/case-file-TEMPLATE.md), lokal/privat halten
# 3. Claude Code im Projektordner öffnen und fragen, z. B.:
#    „Welche seltenen Krankheiten passen zu diesen HPO-Symptomen?"
```

Das komplette Projekt ist als Backlog geplant und wird autonom Ticket für Ticket
gebaut: [dev/backlog/PLAN.md](dev/backlog/PLAN.md), `bash dev/agent-loop.sh`.

## Datenschutz auf einen Blick

- Patientendaten **nie** im Repo (siehe [.gitignore](.gitignore)) und nie an
  öffentliche Datenbanken gesendet — die werden nur abgefragt.
- Die Fallakte liegt in einem **lokalen Ordner** (bei Bedarf optional geteilt,
  z. B. verschlüsselte Dropbox/Nextcloud), pseudonymisiert (Initialen).
- Genetik-Rohdaten (VCF) werden **lokal** ausgewertet, nur Ergebnisse fließen in die Akte.
- Chat-Inhalte gehen zur Inferenz an die Claude-API (kein Training auf API-Daten).
- Vollständig: [docs/security.md](docs/security.md).

## Mitmachen / Lizenz

Open Source unter [MIT](LICENSE). Beiträge willkommen — siehe
[CONTRIBUTING.md](CONTRIBUTING.md). Die Daten-CLIs sind generisch nutzbar, nicht an
einen bestimmten Fall gebunden.
