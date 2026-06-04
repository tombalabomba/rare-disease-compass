---
id: ONB-03
title: Einwilligungs- & Datenschutz-Vorlage
status: todo
depends_on: []
stop_after: false
epic: onboarding
commit_type: docs(onboarding)
---

# ONB-03 — Einwilligungs- & Datenschutz-Vorlage

## Why
Es geht um besondere Kategorien personenbezogener Daten — Gesundheitsdaten eines
Kindes (Art. 9 DSGVO). Die Verarbeitung braucht eine dokumentierte Einwilligung
des Sorgeberechtigten (Matze), inklusive der ehrlichen Offenlegung, dass Chat-
Inhalte zur Inferenz an die Anthropic-API gehen. `docs/security.md` verweist für
genau diese Vorlage explizit auf `epic-onboarding` / ONB-03. Ohne sie fehlt die
rechtliche und organisatorische Grundlage, das System überhaupt zu betreiben.
Dieses Ticket liefert eine **Vorlage** (kein Rechtsrat), die Matze und Thomas
ausfüllen und unterschreiben können, plus eine Checkliste der abzuschließenden
Verträge.

## Scope
**`docs/consent-template.md`** — Einwilligungs- und Datenschutz-Vorlage für den
Sorgeberechtigten. Klar **als Vorlage markiert** (Titel/Hinweis-Box), mit dem
ausdrücklichen Satz, dass dies **keine Rechtsberatung** ist. Pflicht-Bausteine
(als `##`-Überschriften, exakt so benannt, damit die Acceptance per `grep` greift):

- **`## Zweck`** — wofür die Daten verarbeitet werden: Recherche- und
  Entscheidungsunterstützung zu einem komplexen pädiatrischen Krankheitsfall;
  ausdrücklich **keine Diagnose, kein Medizinprodukt**.
- **`## Welche Daten`** — was verarbeitet wird: pseudonymisierte Fallakte
  (Arztbriefe, Befunde, Laborwerte, HPO-codierter Symptomverlauf,
  Genetik-Zusammenfassung), Chat-Inhalte. Klarstellung, dass Genetik-**Rohdaten**
  (VCF) **nur lokal** ausgewertet werden und den Rechner nicht verlassen.
- **`## Wo gespeichert`** — Hetzner-Server in der EU, verschlüsselt
  (Disk-/Volume-Encryption, Login, verschlüsselte Backups); öffentliche Datenbanken
  werden nur **abgefragt**, nie befüllt.
- **`## Anthropic-API`** — ehrlicher Punkt: Chat-Inhalte gehen zur Verarbeitung an
  die Anthropic-API. Anthropic trainiert **nicht** auf API-Daten; ein **DPA /
  Auftragsverarbeitungsvertrag** wird abgeschlossen; die Fallakte ist
  pseudonymisiert, sodass übertragene Inhalte keinen Klarnamen enthalten.
- **`## Pseudonymisierung`** — in der Akte stehen Initialen, kein Klarname, kein
  exaktes Geburtsdatum (nur Alter / Monat-Jahr wo nötig).
- **`## Rechte`** — Rechte des Sorgeberechtigten: jederzeitiger **Widerruf** der
  Einwilligung, **Löschung** der Daten, Auskunft; Folge eines Widerrufs (Verarbeitung
  endet, Daten werden gelöscht).
- **`## Aufbewahrung`** — wie lange Daten aufbewahrt werden und dass sie nach
  Widerruf/Zweckende gelöscht werden (Platzhalter für die konkrete Frist).
- **`## Vertrags-Checkliste`** — abzuschließende Verträge als Checkliste:
  - [ ] **Hetzner AVV** (Auftragsverarbeitungsvertrag) im Konto aktivieren,
    EU-Rechenzentrum gewählt (z. B. Nürnberg/Falkenstein).
  - [ ] **Anthropic DPA** abschließen.
- **`## Einwilligung`** — die eigentliche Vorlage zum Ausfüllen: Felder für Name
  des Sorgeberechtigten, Datum, Unterschrift, Bestätigungssätze („Ich willige ein,
  dass …"). **Platzhalter**, keine echten Namen/Daten.

Ganz oben ein **Vorlage-Hinweis**: „Dies ist eine Vorlage, keine Rechtsberatung.
Vor Verwendung ggf. juristisch prüfen lassen." Verweis-Link auf `docs/security.md`.

## Files
```
docs/consent-template.md   (NEU)
```

## Reality Check (Pflicht — vor Promotion nach `2.ready/`)
- [x] **Files in `Scope`/`Files`**: `docs/consent-template.md` ist **NEU** —
      verifiziert, existiert noch nicht (`ls docs/` zeigt nur `architektur.md`,
      `security.md`).
- [x] **`depends_on`-IDs**: keine. Die Vorlage stützt sich inhaltlich auf
      `docs/security.md` (bereits vorhanden: AVV/DPA, Pseudonymisierung,
      Anthropic-API-Punkt), nicht auf andere Tickets.
- [x] **Externe Voraussetzungen**: keine technische. Der **Abschluss** von AVV/DPA
      ist ein realer organisatorischer Schritt des Menschen — hier nur als
      Checkliste dokumentiert, nicht als Acceptance.
- [x] **Tooling**: nur ein Texteditor. Acceptance über `grep`/`test`; `markdownlint`
      falls verfügbar.

## Acceptance
- [ ] Datei existiert: `test -f docs/consent-template.md`.
- [ ] Pflicht-Bausteine vorhanden:
      `grep -q '## Zweck' docs/consent-template.md`,
      `grep -q '## Welche Daten' docs/consent-template.md`,
      `grep -q '## Anthropic-API' docs/consent-template.md`,
      `grep -q '## Pseudonymisierung' docs/consent-template.md`,
      `grep -q '## Rechte' docs/consent-template.md`,
      `grep -q '## Vertrags-Checkliste' docs/consent-template.md`.
- [ ] DPA und Widerruf/Löschung benannt:
      `grep -qi 'DPA\|Auftragsverarbeitung' docs/consent-template.md`,
      `grep -qi 'Widerruf' docs/consent-template.md`,
      `grep -qi 'Löschung' docs/consent-template.md`.
- [ ] AVV-Checkliste vorhanden:
      `grep -qi 'AVV\|Hetzner' docs/consent-template.md` und mindestens zwei
      Checklisten-Items (`grep -c '^- \[ \]' docs/consent-template.md` ≥ 2).
- [ ] „keine Rechtsberatung"-Hinweis vorhanden:
      `grep -qi 'keine Rechtsberatung\|kein Rechtsrat\|keine Rechtsberatung\|Vorlage' docs/consent-template.md`
      (Vorlage-Hinweis + Rechtsberatungs-Disclaimer; Sichtprüfung beider).
- [ ] **Negativ-Check (Datenschutz):** keine echten Namen, Geburtsdaten oder
      Befunde — nur Platzhalter (Sichtprüfung des Diffs).
- [ ] Markdown-Links nicht offensichtlich kaputt: keine leeren Linkziele
      (`grep -nE '\]\(\s*\)' docs/consent-template.md` findet nichts).
- [ ] `markdownlint docs/consent-template.md` ohne Findings (falls Tool verfügbar;
      sonst manuelle Prüfung).

## Out of scope
- Rechtsverbindliche Beratung oder ein anwaltlich geprüftes Dokument — dies ist
  bewusst eine **Vorlage**.
- Der tatsächliche Abschluss von Hetzner-AVV und Anthropic-DPA — organisatorischer
  Schritt des Menschen, hier nur als Checkliste.
- Betreiber- und Nutzer-Anleitung — ONB-01 bzw. ONB-02.

## Notes
- Inhaltlich konsistent mit `docs/security.md` halten (gleiche Aussagen zu AVV/DPA,
  Pseudonymisierung, „kein Training auf API-Daten", VCF nur lokal). Weicht die
  Vorlage von `security.md` ab, ist das eine Doku-Inkonsistenz → in der
  Commit-Message als zweite Zeile vermerken.
- Felder im `## Einwilligung`-Block als sichtbare Platzhalter (`__________` /
  `[Name]`), damit klar ist, dass nichts vorausgefüllt ist und keine realen Daten
  im Repo landen.
