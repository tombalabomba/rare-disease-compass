# Genetik-Setup — Exomiser lokal einrichten

Diese Doku richtet sich an den **Betreiber/Kurator**, der den lokalen Genetik-Lauf
auf einer Maschine einrichtet. Exomiser priorisiert aus einer VCF plus den
HPO-Symptomen des Falls die wahrscheinlich krankheitsverursachenden
Varianten/Gene/Krankheiten. Der Lauf ist ein **lokaler Docker-Batch-Job** — er
verlässt die Maschine nie (siehe [security.md](security.md),
[architektur.md](architektur.md)).

## Überblick

Der Lauf besteht aus drei Teilen, die alle **lokal** bleiben:

1. **Referenzdaten** — die Exomiser-Datenbank-Releases (mehrere GB), einmalig
   manuell heruntergeladen (dieser Schritt, unten).
2. **Konfiguration** — aus den Templates in `genetics/config/` erzeugt
   (`application.properties`, `analysis.yml`). Das Befüllen orchestriert GEN-02.
3. **Lauf** — `genetics/docker-compose.exomiser.yml` startet das Exomiser-CLI als
   Container gegen VCF + Konfig. Output landet in `exomiser-results/`.

## Welche Referenzdaten Exomiser braucht

Exomiser arbeitet gegen **Datenbank-Releases**, die du von der offiziellen
Exomiser-Datenquelle herunterlädst (Exomiser-Doku / Monarch-Initiative-Daten-Index,
z. B. die `data`-Verzeichnisse der offiziellen Exomiser-Releases auf GitHub bzw.
dem Monarch-Datenserver). Benötigt werden:

| Datenbank-Release | Zweck | Pflicht |
|---|---|---|
| **Phenotype-DB** (`<version>_phenotype`) | HPO-/Orphanet-Mapping, Krankheits-Assoziationen | ja |
| **Variant-DB hg38** (`<version>_hg38`) | Varianten-/Frequenz-/Pathogenitäts-Daten, Assembly hg38 | ja (bei hg38-VCF) |
| **Variant-DB hg19** (`<version>_hg19`) | dieselbe DB für Assembly hg19 | nur bei hg19-VCF |
| **CADD / REMM** (optional) | zusätzliche Pathogenitäts-Scores | optional |

Jedes Release hat einen **Versions-Stand** im Format `JJMM` (z. B. `2402` für
Februar 2024). Diese Versionen trägst du in `application.properties` ein
(`exomiser.hg38.data-version`, `exomiser.hg19.data-version`,
`exomiser.phenotype.data-version`).

## Speicherbedarf

Grobe Größenordnung — die Releases sind groß:

- Phenotype-DB: ~1–2 GB
- Variant-DB pro Assembly (hg38 bzw. hg19): ~20–30 GB entpackt
- CADD/REMM (optional): zusätzlich mehrere GB

Plane **mehrere zehn GB** freien Plattenplatz pro Assembly ein. Die Releases
werden als ZIP geliefert und müssen lokal entpackt werden.

## Wohin die Daten lokal gehören

Lege die entpackten Release-Verzeichnisse in das Daten-Verzeichnis, das das
Compose-File mountet. Default ist `genetics/exomiser-data/` (überschreibbar über
die Env-Var `EXOMISER_DATA_DIR`). Struktur:

```
<EXOMISER_DATA_DIR>/
  2402_phenotype/
  2402_hg38/
  2402_hg19/          # nur falls hg19-VCFs verarbeitet werden
```

Der Pfad entspricht im Container `/exomiser-data` und ist in
`application.properties` als `exomiser.data-directory=/exomiser-data` gesetzt.

Die VCF legst du in das VCF-Input-Verzeichnis (Default `genetics/vcf-input/`,
Env-Var `EXOMISER_VCF_DIR`). Die Ergebnisse erscheinen in `genetics/exomiser-results/`
(Env-Var `EXOMISER_RESULTS_DIR`).

## Alles bleibt lokal

- **Referenzdaten, VCF und Ergebnisse werden nicht ins Repo committet** und nicht
  nach außen übertragen. Das Compose-File läuft mit `network_mode: none` und ohne
  Ports — der Container hat keine Netzverbindung.
- Die Verzeichnisse `exomiser-data/`, `vcf-input/` und `exomiser-results/` gehören
  **außerhalb** der Repo-Versionierung (gitignored). Das Rohgenom verlässt die
  Maschine nie.
- Nur die **kuratierte Ergebnis-Zusammenfassung** (erzeugt von GEN-03) wandert
  später in die Fallakte — keine Rohzeilen.

## Nächster Schritt

Den eigentlichen Lauf (Analysis-YAML aus dem Template erzeugen, HPO-Terme und
VCF-Pfad einsetzen, Container starten) orchestriert der Wrapper **GEN-02**. Das
Parsen des Outputs und die Markdown-Erzeugung für die Fallakte ist **GEN-03**.
