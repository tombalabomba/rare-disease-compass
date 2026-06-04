# RDC erweitern

RareDiseaseCompass ist als **Plattform** gedacht, nicht als geschlossenes
Einzelwerkzeug. Du kannst es an dein Krankheitsbild, deine Fragestellungen und
deine Datenquellen anpassen — und zwar **updatefest**: ein künftiger
RDC-Update-Mechanismus überschreibt nur die mitgelieferten Bausteine, niemals
deine eigenen.

Es gibt zwei Erweiterungspunkte:

1. **Eigene Skill** — ein neuer menschlicher Workflow über den bestehenden CLIs.
2. **Eigene Quelle** — eine neue Daten-/API-Anbindung in der `rdc`-CLI.

---

## 1. Eigene Skill schreiben

Eine Skill ist ein Ordner `skills/<name>/SKILL.md` mit YAML-Frontmatter
(`name`, `description`) und einer Markdown-Anleitung, die die `rdc`-CLIs zu einem
besprechbaren Workflow bündelt (Konvention aus EXP-02).

**Der schnellste Weg ist die geführte Skill `skill-erstellen`** — sie legt das
Gerüst an und verankert die Konvention direkt. Wer von Hand arbeitet, folgt
denselben Regeln:

- Ordner: `skills/<name>-custom/SKILL.md` (zur `-custom`-Regel siehe unten).
- Frontmatter mit `name:` und `description:` (ein Satz: wann greift die Skill).
- Sektion `## Haltung` mit Verweis auf `config/assistant-instructions.md`
  (keine Diagnose, Quellen pflichtig).
- Konkrete `rdc`-Befehle im `## Ablauf`, falls die Skill Daten braucht.
- **Keine echten Patientendaten** — Beispiele sind synthetisch.

---

## 2. Eigene Quelle ergänzen

Eine neue Datenquelle (eine weitere Medizin-API) gehört **nicht** in eine Skill,
sondern in die CLI unter `cli/rdc/sources/`. So bleibt die Skill schlank und die
Quelle ist für alle Skills, Compound-Queries und die History nutzbar.

Vorgehen (Muster aus CLI-02..06):

1. **Modul anlegen:** eine neue Datei `cli/rdc/sources/<quelle>.py`.
2. **Kein eigener HTTP-Stack:** allen Netzwerkverkehr über den zentralen
   `rdc.http_client.HttpClient` leiten (Cache, Rate-Limit, Retry, User-Agent).
3. **Reine Funktionen** für Query-Bau (`*_params`) und Response-Parsing
   (`parse_*`) trennen — beide ohne HTTP-Call, damit Tests sie ohne Netzwerk
   prüfen (`MockTransport`, in-memory-History).
4. **Typer-Subkommando-Gruppe** definieren und in `cli/rdc/main.py` über
   `register(<name>, <app>, <help>)` an die Top-Level-`rdc`-App hängen.
5. **History schreiben:** jede Suche/jeder Fetch erzeugt einen Eintrag in der
   SQLite-History (auch bei 0 Treffern).
6. **Secrets nie loggen:** optionale API-Keys nur als Query-Param anhängen, nie
   in Logs oder History speichern.

Damit erscheint die Quelle automatisch als `rdc <name> ...`-Befehlsgruppe.

---

## 3. Die `-custom`-Update-Regel (updatefest bleiben)

RDC unterscheidet **mitgelieferte** von **eigenen** Skills am Namen:

| Art | Ordner | Update-Verhalten |
|---|---|---|
| Mitgeliefert | `skills/<name>/` | kann von einem Update **ersetzt** werden |
| Eigen | `skills/<name>-custom/` | bleibt **unangetastet** |

- **Eigene Skills tragen immer das Suffix `-custom`.** Ein künftiger
  RDC-Update-/Installer-Mechanismus überschreibt ausschließlich Skills *ohne*
  dieses Suffix.
- Willst du eine mitgelieferte Skill anpassen, **kopiere** sie nach
  `skills/<name>-custom/` und ändere die Kopie. Die Änderung überlebt dann jedes
  Update.
- Dieselbe Vertrautheit wie bei Dex' `create-skill` + `-custom`-Schutz — bewusst
  identisch, damit das Muster robust und wiedererkennbar ist.

> Der eigentliche Update-/Installer-Mechanismus von RDC ist ein eigenes, späteres
> Ticket. Diese Regel legt nur die Konvention fest, an die er sich halten wird.

---

## Siehe auch
- `skills/skill-erstellen/SKILL.md` — die geführte Erstellung einer eigenen Skill.
- `docs/architektur.md` — Gesamtbild (Claude Code + CLIs + Fallakte).
- `config/assistant-instructions.md` — die Kernregeln, die jede Skill erbt.
