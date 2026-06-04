---
id: GEN-01
title: Exomiser-Runner (Docker, lokal) + Konfig-Templates + Daten-Doku
status: todo
depends_on: []
stop_after: false
epic: genetics
commit_type: feat(genetics)
---

# GEN-01 — Exomiser-Runner (Docker, lokal) + Konfig-Templates + Daten-Doku

## Why
Exomiser ist der lokale Genetik-Priorisierer des Falls: ein Java-Tool, das als
Docker-Container gegen eine VCF und die HPO-Symptome läuft und die wahrscheinlich
krankheitsverursachenden Varianten/Gene/Krankheiten ranked. Ohne ein definiertes,
**lokales** Container-Setup plus Konfig-Templates hat GEN-02 (Wrapper) nichts zu
starten und GEN-03 (Konverter) kein Output-Format als Kontext. Der lokale Lauf ist
zudem die zentrale Datenschutz-Maßnahme (`docs/security.md`, `docs/architektur.md`):
Das Rohgenom verlässt den Rechner nie. Dieses Ticket legt die Container-Definition,
die Konfig-Templates und die Daten-Doku an — der eigentliche (große) Referenzdaten-
Download bleibt ein manueller Schritt.

## Scope
Vier Dateien anlegen — Container-Definition, zwei Konfig-Templates, Doku:

**1. `genetics/docker-compose.exomiser.yml`** — definiert einen einzelnen Service
`exomiser`, der das offizielle Exomiser-CLI-Image als Container lokal ausführt.
Bewusst **getrennt** vom Server-Compose (`epic-infra`), damit der lokale Genetik-Lauf
nie zusammen mit dem Server deployed wird. Eigenschaften:
- `image:` auf ein pinned Exomiser-CLI-Tag (Kommentar: bei Bedarf anpassen).
- Volumes (read-only wo möglich): Referenzdaten-Verzeichnis, Config-Verzeichnis
  (`./config`), VCF-Input-Verzeichnis und Output-Verzeichnis (`exomiser-results/`).
  Pfade über `${VAR:-default}`-Substitution, sodass GEN-02 sie setzen kann.
- **Keine** Ports nach außen, **kein** Server-Netz — reiner lokaler Batch-Lauf.
- Kommentare, die jeden Mount und seinen Zweck erklären (deutsch).

**2. `genetics/config/application.properties.template`** — Exomiser-Hauptkonfig als
Template (Java-`.properties`-Format): Pfade zum Referenzdaten-Verzeichnis
(`exomiser.data-directory`), Pfade/Versionen der Phenotype- und Variant-DB-Releases
(`exomiser.hg38.data-version` / `exomiser.hg19.data-version`,
`exomiser.phenotype.data-version`) als Platzhalter, Output-Format-Default
(`TSV_GENE,TSV_VARIANT,JSON,HTML`). Platzhalter klar als `__PLATZHALTER__` markiert.

**3. `genetics/config/analysis.template.yml`** — das Analysis-YAML als Template mit
**HPO-Platzhaltern**. Gültiges YAML mit den von Exomiser erwarteten Top-Level-Keys
(`analysis:` mit `genomeAssembly`, `vcf`, `proband`, `hpoIds`, `analysisMode`,
`frequencySources`, `pathogenicitySources`, `steps`). `hpoIds` ist ein
String-Platzhalter `__HPO_IDS__`, `vcf` ein Platzhalter `__VCF_PATH__` — beide
werden von GEN-02 ersetzt. YAML muss mit `yaml.safe_load` ladbar sein (Platzhalter
sind als Strings notiert, brechen das Parsen nicht).

**4. `docs/genetics-setup.md`** — Betreiber-Doku (deutsch):
- **Welche Referenzdaten** Exomiser braucht und **wo** sie herzuladen sind: die
  Exomiser-Datenbank-Releases (Phenotype-DB + Variant-DB pro Assembly hg19/hg38,
  optional CADD/REMM) von der offiziellen Exomiser-Datenquelle.
- **Speicherbedarf** (mehrere GB pro Release) als grobe Größenordnung.
- **Wohin** die Daten lokal gehören (das Verzeichnis, das das Compose-File mountet).
- Klarer Hinweis: **alles bleibt lokal** — Referenzdaten, VCF und Ergebnisse werden
  nicht ins Repo committet und nicht zum Server übertragen; nur die kuratierte
  Ergebnis-Zusammenfassung (GEN-03) wandert später in die Fallakte.
- Verweis auf GEN-02 (Wrapper, der den Lauf orchestriert).

## Files
```
genetics/docker-compose.exomiser.yml          (NEU)
genetics/config/application.properties.template (NEU)
genetics/config/analysis.template.yml          (NEU)
docs/genetics-setup.md                          (NEU)
```

## Reality Check (Pflicht — vor Promotion nach `2.ready/`)
- [x] **Files in `Scope`/`Files`**: alle vier werden bewusst NEU angelegt. `genetics/`
      existiert noch nicht (`ls` zeigt nur `backlog/ docs/ scripts/` im Repo-Root) —
      wird neu erstellt. `docs/` existiert bereits.
- [x] **`depends_on`-IDs**: keine — GEN-01 ist die Wurzel des Epics.
- [x] **Externe Voraussetzungen**: Referenzdaten-Download (mehrere GB) ist **manuell**
      und groß — bewusst **kein** Teil der Acceptance, in `## Notes` als manueller
      Schritt benannt. Das offizielle Exomiser-Image wird hier nur im Compose
      referenziert, nicht gepullt (Pull = Smoke-Test).
- [x] **Tooling**: `docker compose ... config` validiert das Compose-File ohne
      Image-Pull; `python -c "import yaml"` (PyYAML) lädt die YAML-Templates. Beide
      Befehle laufen ohne Referenzdaten und ohne laufenden Container.

## Acceptance
- [ ] `docker compose -f genetics/docker-compose.exomiser.yml config` validiert ohne
      Fehler (Syntax + Variablen-Substitution; `${VAR:-default}` hat Defaults, sodass
      kein gesetztes Env nötig ist).
- [ ] Compose exponiert **keine** Ports nach außen:
      `! grep -qE '^\s*-\s*"?[0-9]+:[0-9]+' genetics/docker-compose.exomiser.yml`
- [ ] Beide YAML-Templates laden mit `yaml.safe_load` ohne Exception:
      `python -c "import yaml,sys; [yaml.safe_load(open(p)) for p in ['genetics/docker-compose.exomiser.yml','genetics/config/analysis.template.yml']]"`
- [ ] `analysis.template.yml` enthält die HPO- und VCF-Platzhalter, die GEN-02 ersetzt:
      `grep -q '__HPO_IDS__' genetics/config/analysis.template.yml && grep -q '__VCF_PATH__' genetics/config/analysis.template.yml`
- [ ] `analysis.template.yml` hat den `hpoIds`-Key (Exomiser-Pflichtfeld):
      `grep -qE '^\s*hpoIds:' genetics/config/analysis.template.yml`
- [ ] `application.properties.template` benennt das Daten-Verzeichnis:
      `grep -q 'exomiser.data-directory' genetics/config/application.properties.template`
- [ ] `docs/genetics-setup.md` benennt die nötigen Daten-Downloads und den
      Lokal-Hinweis:
      `grep -qiE 'referenzdaten|data-version|datenbank-release' docs/genetics-setup.md && grep -qiE 'lokal' docs/genetics-setup.md`
- [ ] **Negativ-Check (Datenschutz):** keine echte VCF, kein Genom-Schnipsel, keine
      realen Patientendaten in den vier Dateien — Templates enthalten nur Platzhalter
      und Pfade.

## Out of scope
- **Referenzdaten-Download/-Versionierung:** Die mehreren GB Exomiser-DB-Releases
  werden **nicht** geladen, nicht versioniert, nicht ins Repo gelegt. Nur die Doku
  beschreibt den manuellen Download (siehe `## Notes`).
- **Wrapper-Logik (VCF/HPO → Lauf):** Das Skript, das das Analysis-YAML aus dem
  Template generiert und den Container startet, ist GEN-02.
- **Output → Akte:** Das Parsen des Exomiser-Ergebnisses und die Markdown-Erzeugung
  sind GEN-03.
- **Echter Container-Lauf:** Image-Pull und tatsächliche Auswertung sind Smoke-Test
  (Mensch, lokal, mit Referenzdaten).

## Notes
- **Referenzdaten = manueller Schritt (groß).** Exomiser braucht die offiziellen
  Datenbank-Releases (Phenotype-DB + Variant-DB je Assembly, mehrere GB). Diese lädt
  der Mensch lokal herunter und legt sie in das vom Compose gemountete Daten-
  Verzeichnis. `docs/genetics-setup.md` beschreibt das Wo/Wieviel. Der Download ist
  bewusst nicht Teil der Acceptance.
- **`.properties` ist kein YAML.** `application.properties.template` ist im Java-
  Properties-Format (`key=value`) — wird **nicht** mit `yaml.safe_load` geprüft, nur
  per `grep`. Nur das Compose-File und das Analysis-YAML sind YAML.
- **Compose getrennt halten.** Dieses File ist der **lokale** Genetik-Lauf und gehört
  nicht in den Server-Stack aus `epic-infra`. Niemals zusammenführen — das wäre ein
  Bruch der Datensparsamkeits-Architektur (`docs/architektur.md`).
- **Exomiser-Image-Tag.** Im Compose ein konkretes, gepinntes Tag setzen und per
  Kommentar als „bei Bedarf auf aktuelle Version anpassen" markieren. `docker compose
  config` validiert ohne Pull, daher blockiert ein evtl. veraltetes Tag die
  Acceptance nicht.
