# RareDiseaseCompass

**English** · [Deutsch](README.de.md)

A local, privacy-friendly AI research assistant for complex and rare disease
cases. Like a personal knowledge system for a single case: it connects a
**private, structured case file** (a local folder) with the **publicly available
medical knowledge** (literature, rare-disease databases, genetics) through
agent-native CLIs that you use directly in **Claude Code**.

> **Not a medical device. Not medical advice. Not a diagnosis.**
> This open-source tool is research and decision *support*. Every medical
> conclusion belongs in the hands of qualified physicians. Use at your own risk.

## The idea in one sentence

Claude Code + a set of CLIs over public medical APIs + a local folder with the
case file = a personal research assistant that always filters the world's
knowledge through your specific case. No server, no cloud infrastructure, no
installation for non-technical users beyond a one-time setup.

```
                 ┌─────────────────────────────┐
   Case file ───▶│         Claude Code         │
  (local folder) │   reads file · calls CLIs   │────▶ Answer with sources
                 └──────────────┬──────────────┘      + questions for the doctor
                                │ calls
   ┌────────────────────────────┼─────────────────────────────┐
   ▼            ▼               ▼              ▼               ▼
 PubMed     ClinVar/gnomAD   Monarch/Orphanet  PubCaseFinder  Exomiser
(literature)(variants)      (disease graph)   (DDx, HPO)     (local, genetics)
```

Each CLI is built **agent-native**: concise, composable commands with a local
SQLite history (you build up a searchable research store over time) and compound
queries that a raw API cannot answer directly.

## Components

| Area | What | Epic |
|---|---|---|
| Setup | Local project layout, installer, Claude Code configuration | `setup` |
| Data CLIs | Agent-native CLIs: PubMed, ClinVar/gnomAD, Monarch, Orphanet, Europe PMC, PubCaseFinder, Phen2Gene | `cli` |
| Knowledge base | HPO-coded case-file structure, PII guard, assistant instructions | `knowledge` |
| Genetics | Exomiser locally: VCF + HPO → prioritized candidates | `genetics` |
| Experience | Companion persona, tone adaptation, skills layer, onboarding flow | `experience` |
| Onboarding | Setup runbook, user guide, consent/privacy template | `onboarding` |

## Connected databases

All public sources are **queried live** (never copied, never filled with patient
data). Each query is also stored in a local SQLite history that powers the
"new since your last session" hint.

| Database | For | Command | Auth |
|---|---|---|---|
| **PubMed** (NCBI E-utilities) | scientific literature | `rdc pubmed` | optional API key |
| **Europe PMC** | literature incl. full text/preprints | `rdc europepmc` | none |
| **ClinVar / gnomAD / MyVariant** | meaning of a gene variant + population frequency | `rdc variant` | optional API key |
| **Monarch Initiative** | disease graph (phenotype ↔ gene ↔ disease); integrates OMIM, Orphanet, GARD, NORD | `rdc monarch` | none |
| **Orphanet** | reference for rare diseases (genes, inheritance) | `rdc orphanet` | none |
| **PubCaseFinder** | phenotype-driven differential diagnosis: HPO symptoms → ranked diseases | `rdc pubcasefinder` | none |
| **Phen2Gene** | HPO symptoms → candidate genes | `rdc phen2gene` | none |
| **Exomiser** | genetics **locally**: VCF + HPO → prioritized variants/diseases | `genetics/` (Docker) | local |

The commands can be combined (`rdc compound`), and Claude Code calls them on its
own during the conversation, depending on the question. Details:
[docs/architektur.md](docs/architektur.md).

## Repo structure: product vs. build tooling

Clearly separated so you immediately see what you need as a user and what only
serves development:

```
RareDiseaseCompass/
├── cli/          ← PRODUCT: the installable data CLIs (rdc)
├── skills/       ← PRODUCT: the /workflows (erklär-mir, differential, …)
├── config/       ← PRODUCT: assistant persona + tone adaptation
├── tools/        ← PRODUCT: PII guard, case-folder validation
├── genetics/     ← PRODUCT: Exomiser runner (local)
├── docs/         ← PRODUCT: user docs, templates, runbook
├── README · LICENSE · CONTRIBUTING · CLAUDE.md · AGENTS.md
└── dev/          ← BUILD TOOLING ONLY (irrelevant for users)
    ├── backlog/      tickets + planning
    └── agent-loop.sh autonomous build loop
```

**As a user you never need `dev/`.** You install the CLI (`pipx install ./cli`)
and copy `skills/`, `config/` and the templates. The `dev/` directory is the
workshop where the project is built — transparent in the repo, but not part of
the usable product.

## Getting started

```bash
# 1. Install the CLIs
pipx install ./cli        # or the bundled scripts/install.sh

# 2. Create a case file (from docs/case-file-TEMPLATE.md), keep it local/private
# 3. Open Claude Code in the project folder and ask, e.g.:
#    "Which rare diseases match these HPO symptoms?"
```

The whole project is planned as a backlog and built autonomously, ticket by
ticket: [dev/backlog/PLAN.md](dev/backlog/PLAN.md), `bash dev/agent-loop.sh`.

## Privacy at a glance

- Patient data is **never** in the repo (see [.gitignore](.gitignore)) and never
  sent to public databases — those are only queried.
- The case file lives in a **local folder** (optionally shared if needed, e.g.
  an encrypted Dropbox/Nextcloud), pseudonymized (initials).
- Genetic raw data (VCF) is processed **locally**; only results flow into the case file.
- Claude Code runs locally as a tool, but the AI model does **not**: inference
  happens on Anthropic's servers. Your inputs and the case-file content that
  Claude reads are therefore transmitted to Anthropic for processing (depending
  on your login: Anthropic API, Claude subscription, or cloud provider). Whether
  data is used for training depends on the applicable Anthropic terms for your
  login method — check before using real data.
- Full details: [docs/security.md](docs/security.md).

## Contributing / License

Open source under [GPL-3.0](LICENSE). Contributions welcome — see
[CONTRIBUTING.md](CONTRIBUTING.md). The data CLIs are usable generically, not tied
to any specific case.

## Inspiration

RareDiseaseCompass stands on the shoulders of two open-source projects:

- **[printing-press-library](https://github.com/mvanhorn/printing-press-library)** —
  the idea of **agent-native CLIs**: concise, composable commands with a local
  history, built for an AI as the operator. (RDC implements the pattern
  framework-free, without a code dependency.)
- **[dex](https://github.com/davekilleen/dex)** — the pattern of a **local,
  personal knowledge system** in Claude Code: skills, persona, session context,
  and update-safe extensibility. RDC carries this over to medical research.

Thanks to both projects for the groundwork and ideas.
