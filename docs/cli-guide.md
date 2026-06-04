# CLI-Guide — `rdc` für Claude Code

Zentrale Referenz, **welcher `rdc`-Befehl für welche Recherche-Frage** gedacht
ist. Claude Code ruft die CLIs über die Shell auf, liest die Tabellen-/JSONL-
Ausgabe und führt die **Quellen-IDs** (PMID, RCV, OMIM/ORPHA/MONDO …) immer mit.

> Die Ausgabe ist **Recherche-Hilfe, keine Diagnose.** Jede Aussage gehört an die
> Quelle gebunden (ID mitführen). Die klinische Einordnung bleibt beim Menschen.
> Persona und Verhaltensregeln des Assistenten liegen — sofern vorhanden — in
> [`config/assistant-instructions.md`](../config/assistant-instructions.md).

Globale Optionen (vor dem Subkommando): `--format table|jsonl` bzw. `--json`
als Kurzform. Die meisten Subkommandos haben zusätzlich ein lokales `--json`.

## Frage → Befehl

| Recherche-Frage | Befehl |
|---|---|
| Literatur zu einem Stichwort / einer Krankheit finden | `rdc pubmed search`, `rdc europepmc search` |
| Volltext-/Abstract-Details zu bekannten PMIDs holen | `rdc pubmed fetch` |
| Eine konkrete Variante bewerten (Pathogenität, Frequenz) | `rdc variant lookup`, `rdc variant clinvar` |
| Aus einem Phänotyp-Profil Krankheiten ableiten (Graph) | `rdc monarch diseases-by-phenotypes` |
| Zu einem Gen assoziierte Krankheiten finden | `rdc monarch gene-to-diseases` |
| Orphanet-Eintrag samt Querverweisen nachschlagen | `rdc orphanet lookup` |
| Differentialdiagnose aus HPO-Profil (gerankte Krankheiten/Gene) | `rdc pubcasefinder rank`, `rdc phen2gene genes` |
| **Kombinierte Abklärung** aus einem HPO-Profil (DDx + Graph + Literatur) | `rdc compound phenotype-workup` |
| Was wurde bisher recherchiert? | `rdc history list`, `rdc history search` |

## Alle Subkommandos

### Literatur

**`rdc pubmed search "<query>"`** — sucht in PubMed (NCBI E-utilities) und liefert
Treffer mit PMID, Jahr, Autoren, Journal, Titel, DOI.

```
rdc pubmed search "Marfan syndrome aortic root" --retmax 10
```

**`rdc pubmed fetch <PMID...>`** — holt Metadaten **und Abstracts** zu einer oder
mehreren PMIDs.

```
rdc pubmed fetch 34567890 33445566
```

**`rdc europepmc search "<query>"`** — Europe-PMC-Suche; Treffer mit PMID, PMCID,
DOI, Jahr, Quelle und Titel (gute Ergänzung/Alternative zu PubMed).

```
rdc europepmc search "Loeys-Dietz syndrome" --page-size 25
```

### Varianten

**`rdc variant lookup <HGVS|rsID>`** — kombinierte Variant-Sicht aus
MyVariant.info: ClinVar-Pathogenität **und** gnomAD-Allelfrequenz.

```
rdc variant lookup rs113488022
```

**`rdc variant clinvar <HGVS|rsID>`** — fokussierte ClinVar-Sicht: klinische
Signifikanz, Review-Status, Condition(s) und RCV-IDs.

```
rdc variant clinvar chr7:g.140453136A>T
```

### Krankheits-Graph

**`rdc monarch diseases-by-phenotypes <HPO...>`** — leitet aus einer HPO-Liste die
am besten passenden Krankheiten ab (MONDO/OMIM/ORPHA-ID + Name, Score = Zahl der
getroffenen Phänotypen).

```
rdc monarch diseases-by-phenotypes HP:0001166 HP:0001083 HP:0004933
```

**`rdc monarch gene-to-diseases <gene>`** — zu einem Gen (Symbol oder CURIE)
assoziierte Krankheiten aus dem Monarch-Graphen.

```
rdc monarch gene-to-diseases FBN1
```

**`rdc orphanet lookup <ORPHA-Code|Name>`** — Orphanet/Orphadata-Eintrag: Name,
ORPHA-Code, OMIM- und weitere Querverweise.

```
rdc orphanet lookup "Marfan syndrome"
rdc orphanet lookup ORPHA:558
```

### Differentialdiagnose (HPO-getrieben)

**`rdc pubcasefinder rank <HPO...>`** — schickt das HPO-Profil an PubCaseFinder und
liefert eine **gerankte Liste seltener Krankheiten** (Krankheit + OMIM/ORPHA-ID +
Score/Rang).

```
rdc pubcasefinder rank HP:0001166 HP:0001083 --limit 20
```

**`rdc phen2gene genes <HPO...>`** — schickt das HPO-Profil an Phen2Gene und liefert
**gerankte Kandidatengene** (Gen-Symbol + Score/Rang).

```
rdc phen2gene genes HP:0001166 HP:0001083
```

### Kombinierte Abklärung

**`rdc compound phenotype-workup <HPO...>`** — orchestriert in **einem** Schritt
DDx (PubCaseFinder + Phen2Gene), Krankheits-Graph (Monarch) und — optional —
eine PubMed-Suche zum Top-Kandidaten. Führt gleiche Krankheiten über die
Quellen-IDs (OMIM/ORPHA/MONDO) und gleiche Gene über das Symbol zusammen und
rankt nach einem transparenten **Konsens-Score** (in wie vielen Quellen ein
Kandidat auftaucht, plus dessen bester Rang). Ausgabe: drei Abschnitte
(Krankheiten, Kandidatengene, Literatur), jede Zeile mit den stützenden Quellen.

```
rdc compound phenotype-workup HP:0001166 HP:0001083 HP:0004933 --limit 15
rdc compound phenotype-workup HP:0001166 HP:0001083 --no-literature --json
```

Optionen: `--limit/-n` (Kandidaten je Liste), `--with-literature/--no-literature`,
`--json`.

## Recherche-Speicher (History)

Jeder Quellen-Aufruf — und jede Compound-Abklärung — wird in einer lokalen
SQLite-History protokolliert (außerhalb des Repos, gitignored). So lässt sich der
gesammelte Verlauf später auflisten und durchsuchen.

```
rdc history list --limit 20
rdc history list --source compound
rdc history search "Marfan"
```

## Aktuell halten

`docs/cli-guide.md` ist die zentrale Referenz für Claude Code. Kommen später
Subkommandos dazu, gehört dieser Guide mit aktualisiert (Doku-Sync, siehe
`CLAUDE.md`).
