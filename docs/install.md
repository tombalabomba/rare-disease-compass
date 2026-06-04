# Installation der rdc-CLIs

Kurze Anleitung, um die RareDiseaseCompass-CLIs (Kommando `rdc`) einmalig auf
der lokalen Maschine lauffähig zu machen. **Kein Server, kein Deployment** — alles
läuft lokal.

## Voraussetzungen

- **Python ≥ 3.11** (Stack-Vorgabe). Prüfen mit `python3 --version`.
- Optional **`pipx`** für eine isolierte CLI-Installation. Fehlt `pipx`, fällt der
  Installer automatisch auf `pip --user` zurück.
- Für die Genetik (separater Schritt, nicht Teil dieses Skripts) zusätzlich
  **Docker** — siehe [`docs/genetics-setup.md`](genetics-setup.md).

## Installation ausführen

Aus dem Repo-Wurzelverzeichnis:

```bash
bash scripts/install.sh
```

Das Skript ist **idempotent** — mehrfaches Ausführen schadet nicht.

### Was das Skript tut

1. **Python-Version prüfen:** bricht mit klarer Meldung ab, wenn `python3` fehlt
   oder älter als 3.11 ist.
2. **CLI installieren:** installiert das `cli/`-Paket (Entry-Point `rdc`). Bevorzugt
   `pipx`, sonst `pip --user`. Ist `rdc` bereits installiert, wird die Installation
   übersprungen (Idempotenz); für ein Upgrade `pipx upgrade rdc` ausführen.
3. **Beispiel-Konfig anlegen:** legt — falls noch nicht vorhanden — eine
   Vorlage `~/.config/rdc/env.example` mit auskommentierten Platzhaltern an. Eine
   bestehende echte Konfig wird **nie** überschrieben.

Nach erfolgreicher Installation steht das Kommando `rdc` im `PATH` (ggf. neue Shell
öffnen oder das von `pipx`/`pip` gemeldete `bin`-Verzeichnis zum `PATH` hinzufügen).

## Optionale API-Keys (NCBI/Entrez)

Alle API-Keys sind **optional**. Die meisten Quellen funktionieren ohne Key; ein
NCBI/Entrez-Key (für PubMed) hebt lediglich das Rate-Limit an. Siehe
[`docs/architektur.md`](architektur.md).

So aktivierst du einen Key:

```bash
cp ~/.config/rdc/env.example ~/.config/rdc/env
# dann ~/.config/rdc/env öffnen und den Platzhalter durch deinen echten Key ersetzen:
#   NCBI_API_KEY=dein_echter_key
```

> **Datenschutz:** Echte Keys gehören **nur lokal** ins User-Home
> (`~/.config/rdc/`) und **niemals** ins Repo. `.env`/`*.key` sind ohnehin per
> `.gitignore` gesperrt; die Vorlage heißt bewusst `*.example`.

## Nächster Schritt

Fall-Ordner anlegen und Claude Code darin öffnen — die Ordner-Konvention steht in
[`docs/project-layout.md`](project-layout.md) (SET-01).
