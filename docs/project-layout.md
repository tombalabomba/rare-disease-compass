# Projekt-Layout & Fallakten-Ablage

Diese Datei ist die **verbindliche** Konvention dafür, **wo** die Fallakte liegt
und **wie** Claude Code darauf zeigt. Sie ist die *single source of truth* für die
Ablage-Trennung; andere Docs ([case-folder.md](case-folder.md), das Runbook
ONB-01) verweisen hierher, statt die Konvention zu duplizieren.

Der Grundsatz in einem Satz: **Software lebt im Repo, Patientendaten leben strikt
außerhalb des Repos.** Das Repo ist (oder wird) öffentlich — die Fallakte und erst
recht die Genetik-Rohdaten sind es nie. Hintergrund und Pflicht-Grundsätze:
[security.md](security.md), [architektur.md](architektur.md).

> Hinweis: `docs/security.md` enthält noch eine ältere Server-/Postgres-Tabelle aus
> der Zeit vor dem Architektur-Pivot. Sie beschreibt **nicht** die aktuelle,
> server-lose Architektur. Maßgeblich für die Ablage ist diese Datei plus
> [architektur.md](architektur.md).

## Fallakten-Ablage

Die Fallakte liegt in einem **eigenen Top-Level-Ordner außerhalb des Repos** auf
dem Rechner des Kurators. Empfohlen ist ein klar benannter Ordner direkt im
Home-Verzeichnis, z. B. `~/rdc-fall-<kürzel>/`.

Verbindlich:

- Der Fall-Ordner ist **niemals** ein Unterordner des geklonten Repos. Er steht
  daneben, auf gleicher oder höherer Ebene.
- Begründung: Das Repo ist öffentlich und wird gepusht. Alles, was darunter liegt,
  kann versehentlich committet werden. Pseudonymisierte Krankengeschichten und
  Genom-Rohdaten dürfen das nie (PII-Leck, [security.md](security.md)).
- Das `<kürzel>` ist ein frei gewähltes Pseudonym/Initialen-Kürzel, **kein**
  Klarname. Pseudonymisierung regelt [security.md](security.md).

So liegen Repo und Fall-Ordner getrennt, und der öffentliche Code kann nie
Patientendaten mitschleppen.

## Datentrennung (lokal & optional geteilt)

Standardfall ist **rein lokal**: ein Kurator, ein Rechner, ein lokaler Fall-Ordner.

Bei **Zwei-Rollen-Nutzung** (einer kuratiert, einer liest mit) darf die
**pseudonymisierte** Fallakte (Markdown) optional in einem **geteilten,
verschlüsselten** Ordner liegen (z. B. Dropbox/Nextcloud). Das ist eine Option,
keine Pflicht.

Was geteilt werden darf und was strikt privat-lokal bleibt:

| Daten | Ablage | Teilen erlaubt? |
|---|---|---|
| Fallakte `case-file-<kürzel>.md` (pseudonymisiert, HPO-codiert) | Fall-Ordner | ja — optional im geteilten, verschlüsselten Ordner |
| Kuratierte Genetik-Zusammenfassung (GEN-03, Teil der Akte) | Fall-Ordner, als Akten-Sektion | ja — wie die Akte |
| Genetik-**Rohdaten** (VCF, Rohgenom) | nur lokal, separater Pfad | **nein** |
| Befund-PDFs, Original-Arztbriefe | nur lokal | **nein** |
| CLI-SQLite-History (`*.db`) | nur lokal, gitignored | **nein** (kann fallbezogene Suchen enthalten) |
| Secrets / API-Keys | lokale Konfig, gitignored | **nein** |

Faustregel: In den geteilten Ordner wandert ausschließlich die kuratierte,
pseudonymisierte Akte. Rohdaten und akkumulierte Recherche-Spuren bleiben auf der
Maschine des Kurators.

## Genetik lokal

Die VCF-/Rohgenom-Dateien liegen **ausschließlich lokal** auf dem Rechner des
Kurators — außerhalb eines etwaigen geteilten Ordners und außerhalb des Repos.
Sie verlassen die Maschine nicht.

- Empfohlen ein separater, **nicht** geteilter Pfad, z. B. `~/rdc-genetik/`,
  getrennt vom (eventuell geteilten) Fall-Ordner.
- Exomiser läuft als lokaler Docker-Batch-Job gegen diese VCF
  ([genetics-setup.md](genetics-setup.md)). Auch die Ergebnis-Rohausgabe bleibt
  zunächst lokal.
- In die Fallakte wandert **nur** die kuratierte Ergebnis-Zusammenfassung (GEN-03),
  niemals die VCF oder Exomiser-Rohzeilen. Datensparsamkeit, siehe
  [security.md](security.md).

## Claude-Code-Konfig

Claude Code arbeitet **im Fall-Ordner**, nicht im Repo:

- Claude Code wird **im Fall-Ordner** gestartet — oder der Fall-Ordner wird als
  zusätzliches Arbeitsverzeichnis aufgenommen. Der Assistent liest die Akte direkt
  als Dateien (kein Server, keine Ingestion, kein Index — siehe
  [case-folder.md](case-folder.md)).
- Eine **`CLAUDE.md` im Fall-Ordner** lädt die Assistenten-Persona. Ihr Inhalt
  stammt aus KB-04 (`config/assistant-instructions.md`) — diese Datei in den
  Fall-Ordner als `CLAUDE.md` übernehmen, nicht neu erfinden.
- Die installierten **`rdc`-CLIs** sind nach der Installation (SET-02) global auf
  der Maschine verfügbar und werden vom Assistenten über die Shell aufgerufen
  (`rdc …`). Sie müssen **nicht** in den Fall-Ordner kopiert werden.

So bleibt die Trennung sauber: Der Code (`rdc`-CLIs, Repo) ist global bzw.
öffentlich, der Fall-Ordner enthält nur die Akte plus die persona-`CLAUDE.md`.

## Beispiel-Layout

Repo und Fall-Ordner liegen **nebeneinander**, der Fall-Ordner sichtbar außerhalb
des Repos:

```text
~/
├── code/
│   └── rare-disease-compass/        # das geklonte, öffentliche Repo
│       ├── cli/                     #   rdc-CLI-Quellcode
│       ├── config/
│       │   └── assistant-instructions.md   # Persona-Quelle (KB-04)
│       ├── docs/
│       ├── genetics/                #   Exomiser-Templates (kein VCF!)
│       └── tools/
│
├── rdc-fall-<kürzel>/               # FALL-ORDNER — außerhalb des Repos
│   ├── CLAUDE.md                    #   Persona, kopiert aus config/assistant-instructions.md
│   └── case-file-<kürzel>.md        #   pseudonymisierte, HPO-codierte Akte
│                                    #   (optional in geteilter, verschlüsselter Dropbox)
│
└── rdc-genetik/                     # NUR LOKAL, nie geteilt, nie im Repo
    ├── probe-<kürzel>.vcf.gz        #   Genetik-Rohdaten
    └── exomiser-results/            #   lokale Roh-Ergebnisse
```

Der Baum macht sichtbar: Das Repo enthält ausschließlich Software, Templates und
Doku. Die Akte liegt in `~/rdc-fall-<kürzel>/` (außerhalb des Repos, optional
geteilt), die Genetik-Rohdaten in `~/rdc-genetik/` (nur lokal). Kein Pfad mit
echten Patientendaten liegt jemals unter dem Repo.
