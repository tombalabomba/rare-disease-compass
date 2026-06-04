# Setup-Runbook (Betreiber/Kurator)

Diese Anleitung führt die **technische Rolle** — Betreiber bzw. Kurator — einmal
komplett durch die Einrichtung von RareDiseaseCompass auf **einer Maschine**. Es
gibt kein Deployment in der Cloud: alles läuft lokal. Du installierst die CLIs,
legst den Fallakten-Ordner an, validierst ihn und konfigurierst Claude Code, damit
der Assistent direkt im Fall-Ordner arbeitet.

Das Runbook ist ein **Verweis-Hub**: Die Tiefe steht in den verlinkten Dokumenten,
hier stehen die richtige **Reihenfolge** und das große Bild. Arbeite die Abschnitte
von oben nach unten ab — sie folgen dem realen Einrichtungsablauf.

> **Datenschutz zuerst.** Echte Patientendaten, Namen, Geburtsdaten, VCF-/Genom-
> Dateien oder Befund-PDFs gehören **niemals** ins Repo. Die Fallakte ist
> pseudonymisiert und HPO-codiert; Genetik-Rohdaten bleiben lokal. Siehe
> [`docs/architektur.md`](architektur.md) und [`docs/security.md`](security.md).

---

## Installation

Installiere die agenten-nativen CLIs auf der Maschine. Das geht über das
Installer-Skript [`scripts/install.sh`](../scripts/install.sh); die ausführliche
Anleitung inkl. Voraussetzungen steht in [`docs/install.md`](install.md).

Kurz die Voraussetzungen (Details **nicht** hier duplizieren — siehe
[`docs/install.md`](install.md)):

- **Python 3.11** für die Daten-CLIs.
- **Docker**, aber nur für die Genetik (Exomiser) — siehe Abschnitt
  [Genetik](#genetik-exomiser-lokal). Für reine Literatur-/Phänotyp-Recherche
  brauchst du Docker nicht.

```bash
bash scripts/install.sh
```

Danach prüfen, dass die CLI im `PATH` liegt (siehe
[Troubleshooting](#troubleshooting), falls nicht).

## API-Keys

API-Keys sind **optional**. Die meisten Quellen funktionieren ganz ohne Key; ein
NCBI/Entrez-Key (für PubMed) hebt lediglich das Rate-Limit an. Welche Quelle
welchen Key braucht, steht in [`docs/architektur.md`](architektur.md).

Wenn du einen Key hinterlegen willst: Er gehört in eine **lokale, gitignored**
Konfigurationsdatei im User-Home (`~/.config/rdc/env`) — **nie** ins Repo. Die
genauen Schritte (Vorlage kopieren, Platzhalter ersetzen) stehen unter „Optionale
API-Keys" in [`docs/install.md`](install.md).

> Echte Keys nur lokal. `.env`/`*.key` sind per `.gitignore` gesperrt; die Vorlage
> heißt bewusst `*.example`.

## Akte anlegen und validieren

1. **Fall-Ordner anlegen.** Lege einen Ordner für die Fallakte an. Die
   Ordner-Konvention (welche Dateien, welche Struktur) steht in
   [`docs/project-layout.md`](project-layout.md).
2. **Akte aus der Vorlage befüllen.** Nutze die Fallakten-Vorlage
   [`docs/case-file-TEMPLATE.md`](case-file-TEMPLATE.md) als Ausgangspunkt. Pflege
   den Fall **HPO-codiert** (Phänotypen als HPO-Terme) und **pseudonymisiert**
   (keine Klarnamen, keine Geburtsdaten — nur ein Pseudonym/Fall-Kürzel).
3. **Validieren.** Prüfe den Ordner lokal und offline mit dem Validator
   [`tools/validate_case_folder.py`](../tools/validate_case_folder.py). Er prüft
   Pflichtsektionen, HPO-Format und meldet potenzielle PII. Aufruf:

   ```bash
   python tools/validate_case_folder.py <pfad-zum-fall-ordner>
   ```

   Exit-Code `0` = sauber. Bei Befunden (PII oder Schema-Fehler) ist der Exit-Code
   `!= 0` und der Report nennt die betroffenen Stellen — zuerst beheben, dann erneut
   validieren. Mehr Hintergrund in [`docs/case-folder.md`](case-folder.md).

## Claude-Code-Konfiguration

Öffne Claude Code **im Fall-Ordner** (VS Code/Codium oder Terminal). Damit der
Assistent Persona und Regeln übernimmt — keine Diagnose stellen, immer Quellen
nennen, konkrete Fragen an die behandelnden Ärzt:innen formulieren — kopierst du die
Assistenten-Instruktionen
[`config/assistant-instructions.md`](../config/assistant-instructions.md) als
`CLAUDE.md` **in den Fall-Ordner**:

```bash
cp config/assistant-instructions.md <pfad-zum-fall-ordner>/CLAUDE.md
```

Diese `CLAUDE.md` liegt im (ggf. geteilten) Fall-Ordner, nicht im Software-Repo.
Sie steuert das Verhalten des Assistenten für genau diesen Fall.

## Zwei-Rollen-Nutzung (optional)

Sollen **zwei Personen** denselben Fall nutzen, lege den Fall-Ordner in einen
**geteilten, verschlüsselten Ordner** (z. B. Dropbox oder Nextcloud):

- **Kurator** (technische Rolle): pflegt und validiert die Akte.
- **Endnutzer**: liest die Akte und chattet mit dem Assistenten. Der zugehörige
  Ablauf steht im Nutzer-Guide [`docs/user-guide.md`](user-guide.md).

**Wichtig:** Die Genetik-**Rohdaten** (VCF) gehören **nicht** in den geteilten
Ordner. Sie bleiben **lokal außerhalb** davon auf der Maschine, auf der Exomiser
läuft. Begründung und Grenzen siehe [`docs/architektur.md`](architektur.md) und
[`docs/security.md`](security.md).

## Genetik (Exomiser lokal)

Die Genetik-Auswertung läuft **lokal** über Exomiser (Docker), die VCF verlässt die
Maschine nie. Mache Exomiser **einmalig** lauffähig — Referenzdaten-Download und
Docker-Lauf sind in [`docs/genetics-setup.md`](genetics-setup.md) beschrieben. Hier
nur verlinken, nicht duplizieren.

Dieser Abschnitt ist optional: Ohne Genetik-Auswertung funktioniert die
Literatur- und Phänotyp-Recherche weiterhin.

## Troubleshooting

Die häufigsten Stolpersteine:

- **CLI nicht im `PATH`.** Nach der Installation neue Shell öffnen oder das
  Profil neu laden. Prüfe, ob das Bin-Verzeichnis aus [`docs/install.md`](install.md)
  im `PATH` steht.
- **API-Key-Format falsch / wird ignoriert.** Liegt der Key wirklich in
  `~/.config/rdc/env` und nicht im Repo? Zeile im Format `NCBI_API_KEY=…`, keine
  Anführungszeichen, kein Leerraum. Keys sind optional — ohne Key läuft alles, nur
  mit niedrigerem Rate-Limit.
- **Validator meldet PII oder Schema-Fehler.** Der Report von
  [`tools/validate_case_folder.py`](../tools/validate_case_folder.py) nennt die
  Stelle. PII (Klarname, Geburtsdatum) entfernen bzw. pseudonymisieren,
  Pflichtsektionen ergänzen, HPO-Terme ins korrekte Format bringen — dann erneut
  validieren.
- **Docker nicht gestartet.** Für Exomiser muss Docker laufen. Docker Desktop
  starten und mit `docker info` prüfen, dann den Lauf aus
  [`docs/genetics-setup.md`](genetics-setup.md) wiederholen.
- **Geteilter Ordner synchronisiert nicht.** Prüfe, ob der Sync-Client (Dropbox/
  Nextcloud) läuft und der Ordner vollständig synchronisiert ist, bevor die andere
  Rolle darauf zugreift. VCF-Rohdaten gehören ohnehin **nicht** in den geteilten
  Ordner (siehe [Zwei-Rollen-Nutzung](#zwei-rollen-nutzung-optional)).
