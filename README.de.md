# RareDiseaseCompass

[English](README.md) · **Deutsch**

Ein lokaler, datenschutzfreundlicher KI-Recherche-Assistent für komplexe und
seltene Krankheitsfälle. Wie ein persönliches Wissenssystem für genau einen
Krankheitsfall: Er verknüpft eine **private, strukturierte Fallakte** (lokaler Ordner) mit dem
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

Jede CLI ist **agenten-nativ** gebaut: knappe, kombinierbare Befehle mit lokaler
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

## Loslegen

```bash
# 1. CLIs installieren
pipx install ./cli        # oder das mitgelieferte scripts/install.sh

# 2. Fallakte anlegen (aus docs/case-file-TEMPLATE.md), lokal/privat halten
# 3. Claude Code im Projektordner öffnen und fragen, z. B.:
#    „Welche seltenen Krankheiten passen zu diesen HPO-Symptomen?"
```

Das komplette Projekt ist als Backlog geplant und wird autonom Ticket für Ticket
gebaut: [dev/backlog/PLAN.md](dev/backlog/PLAN.md), `bash dev/agent-loop.sh`.

## Datenschutz, ehrlich betrachtet

**Sei ehrlich zu dir selbst:** Das ist **kein** „100 % privat, nichts verlässt
deinen Rechner"-Werkzeug. Claude Code läuft lokal, aber das KI-Modell nicht. Um
deine Fragen zu beantworten, werden **deine Eingaben UND die Aktendaten, die Claude
liest, an Anthropic übertragen.** Solange du Claude nutzt, führt daran kein Weg
vorbei. (Wenn ein Tool in Videos klingt, als sei alles 1000 % privat: bei jedem
cloud-basierten KI-Modell stimmt das schlicht nicht.)

Was das Werkzeug trotzdem tut, um deine Daten so privat wie möglich zu halten:

- Patientendaten **nie** im Repo (siehe [.gitignore](.gitignore)); öffentliche
  Datenbanken werden nur **abgefragt**, nie mit deinen Daten befüllt.
- Die Fallakte liegt in einem **lokalen Ordner** (bei Bedarf geteilt, z. B.
  verschlüsselte Dropbox/Nextcloud), **pseudonymisiert** (Initialen, keine
  Klarnamen, keine Geburtsdaten).
- Genetik-Rohdaten (VCF) bleiben **lokal**, nur Ergebnisse fließen in die Akte.

**Datenschutz so weit wie möglich — entscheiden musst du.** Wenn du oder dein Kind
eine seltene Krankheit hat und du sie verstehen und Hilfe finden willst, solltest
du selbst abwägen, wie wichtig dir Datensicherheit ist gegenüber dem Wert, eine KI
mit den Daten arbeiten zu lassen. Das ist eine persönliche Entscheidung. Dieses
Werkzeug ist dafür gebaut, dir diese Wahl mit offenen Augen zu lassen, nicht so zu
tun, als gäbe es die Frage nicht.

**Zum Training:** Anthropic sagt selbst, dass über die **API** übertragene Daten
**nicht** zum Training der Modelle verwendet werden. Ob das auch für ein
**Claude-Abo** (Pro/Max) gilt, das du mit Claude Code nutzt, prüfst du am besten in
den aktuellen Anthropic-Bedingungen selbst — im Zweifel frag einfach die KI deiner
Wahl danach.

Vollständig: [docs/security.md](docs/security.md).

## Mitmachen / Lizenz

Open Source unter [GPL-3.0](LICENSE). Beiträge willkommen — siehe
[CONTRIBUTING.md](CONTRIBUTING.md). Die Daten-CLIs sind generisch nutzbar, nicht an
einen bestimmten Fall gebunden.

## Inspiration

RareDiseaseCompass steht auf den Schultern zweier Open-Source-Projekte:

- **[printing-press-library](https://github.com/mvanhorn/printing-press-library)** —
  die Idee **agenten-nativer CLIs**: knappe, kombinierbare Befehle mit lokaler
  History, gebaut für eine KI als Bediener. (RDC setzt das Muster framework-frei
  um, ohne Code-Abhängigkeit.)
- **[dex](https://github.com/davekilleen/dex)** — das Muster eines **lokalen,
  persönlichen Wissenssystems** in Claude Code: Skills, Persona, Session-Kontext und
  updatefeste Erweiterbarkeit. RDC überträgt das auf die medizinische Recherche.

Danke an beide Projekte für die Vorarbeit und die Ideen.
