---
name: skill-erstellen
description: Geführte Erstellung einer eigenen RDC-Skill — legt updatefest einen neuen Ordner skills/<name>-custom/SKILL.md mit Frontmatter-Gerüst an und erklärt die -custom-Konvention, damit ein künftiges Update die Skill nie überschreibt.
---

# skill-erstellen

Hilft Nutzern und Community, **eigene Skills** für RDC zu bauen — für andere
Krankheitsbilder, andere Fragestellungen oder zusätzliche Datenquellen — ohne
dass ein späteres RDC-Update die eigene Arbeit überschreibt. Das `-custom`-Suffix
folgt einem bewährten, vertrauten Konventions-Muster und macht eigene Skills
robust gegen Updates.

## Haltung
Diese Skill folgt `config/assistant-instructions.md`: **keine Diagnose**, keine
Therapieempfehlung, Quellen pflichtig, Unsicherheit explizit. Eine neu erstellte
Skill erbt diese Regeln — sie werden im erzeugten Gerüst direkt als Verweis
verankert. Ton/Register nach `config/case-profile.yaml`.

## Die `-custom`-Update-Regel (Kern dieser Skill)
- **Eigene Skills tragen immer das Suffix `-custom`:** der Ordner heißt
  `skills/<name>-custom/`, niemals nur `skills/<name>/`.
- **Ein künftiger RDC-Update-/Installer-Mechanismus überschreibt ausschließlich
  Skills *ohne* `-custom`-Suffix.** Alles, was auf `-custom` endet, gilt als
  Eigentum des Betreibers und bleibt unangetastet.
- Mitgelieferte Skills (`skills/differential/`, `skills/fall-anlegen/` usw.)
  tragen **kein** `-custom` und können bei einem Update ersetzt werden. Wer eine
  mitgelieferte Skill anpassen will, **kopiert** sie nach `<name>-custom/` und
  ändert die Kopie — so überlebt die Änderung jedes Update.

## Ablauf
1. **Name und Zweck klären.** Kurzer, sprechender Slug in Kleinbuchstaben mit
   Bindestrichen (z. B. `epilepsie-verlauf`). Der Ordnername bekommt automatisch
   das Suffix: `skills/epilepsie-verlauf-custom/`.
2. **Beschreibung formulieren.** Ein Satz, der sagt, *wann* die Skill greift und
   *was* sie tut — das ist das `description`-Feld im Frontmatter.
3. **Gerüst anlegen.** Datei `skills/<name>-custom/SKILL.md` mit dem Frontmatter
   (`name`, `description`) und den Pflicht-Sektionen erstellen. Vorlage:

   ```markdown
   ---
   name: <name>-custom
   description: <ein Satz: wann greift die Skill, was tut sie>
   ---

   # <name>-custom

   Kurzbeschreibung, was diese Skill für den Nutzer erledigt.

   ## Haltung
   Diese Skill folgt `config/assistant-instructions.md`: **keine Diagnose**,
   keine Therapieempfehlung, Quellen pflichtig, Unsicherheit explizit.
   Ton/Register nach `config/case-profile.yaml`.

   ## Voraussetzung
   Installierte `rdc`-CLI (siehe Setup-Runbook), falls die Skill CLIs nutzt.

   ## Ablauf
   1. <Schritt 1 — z. B. relevante Daten aus der Fallakte sammeln>
   2. <Schritt 2 — z. B. konkreter `rdc`-Aufruf>

   ## Output
   - <Was der Nutzer am Ende bekommt>
   - Hinweis: keine Diagnose; ärztliche Bewertung erforderlich.
   ```

4. **Inhalt füllen.** Den `## Ablauf` mit den konkreten Schritten und — falls die
   Skill Daten braucht — mit echten `rdc`-Befehlen ausschreiben. Eine neue
   Datenquelle hängt sich nicht in die Skill, sondern in die CLI ein (siehe
   `docs/extending.md`, Abschnitt „eigene Quelle").
5. **Prüfen.** Frontmatter vollständig (`name`, `description`), `name` endet auf
   `-custom`, der Disclaimer-Verweis steht drin. Datenschutz: **keine echten
   Patientendaten** in der Skill — Beispiele sind erfunden und synthetisch.

## Output
- Ein neuer Ordner `skills/<name>-custom/SKILL.md` mit gültigem Frontmatter und
  ausgefülltem Ablauf.
- Die Gewissheit, dass ein künftiges RDC-Update diese Skill nicht überschreibt
  (`-custom`-Schutz).
- Hinweis: keine Diagnose; eine Skill ist Recherche-Werkzeug, keine ärztliche
  Bewertung.
