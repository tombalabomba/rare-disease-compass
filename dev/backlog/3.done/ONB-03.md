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
Es werden besondere Kategorien personenbezogener Daten verarbeitet —
Gesundheitsdaten, möglicherweise eines Kindes (Art. 9 DSGVO, siehe
`docs/security.md`). Bevor eine Fallakte angelegt und über die Claude-API
verarbeitet wird, sollte eine **dokumentierte Einwilligung** vorliegen (bei Daten
eines Kindes durch die Sorgeberechtigten). Ohne eine vorgefertigte, verständliche
Vorlage müsste jeder Betreiber das selbst formulieren — fehleranfällig und
abschreckend. Diese Vorlage gibt einen klaren, anpassbaren Ausgangstext. Sie ist
ausdrücklich **keine Rechtsberatung**.

## Scope
Eine neue Datei `docs/consent-template.md` (deutsch) als **Vorlage** für eine
Einwilligungserklärung. Klar als Vorlage markiert, mit Platzhaltern (z. B.
`[Name des Betreuers]`, `[Initialen der betroffenen Person]`) — **keine** echten
Daten. Pflicht-Bausteine (als Markdown-Überschriften, damit per `grep` prüfbar):

1. **## Hinweis: Vorlage, keine Rechtsberatung** — ganz oben, deutlich: Dies ist
   eine unverbindliche Muster-Vorlage, **keine Rechtsberatung**; im Zweifel
   anwaltlich/Datenschutz-fachlich prüfen lassen und an die eigene Situation anpassen.
2. **## Zweck der Verarbeitung** — wofür die Daten verarbeitet werden: private
   medizinische Recherche-Unterstützung zu einem seltenen/komplexen Krankheitsfall,
   **keine Diagnose**, kein Medizinprodukt.
3. **## Welche Daten** — welche Daten gespeichert/verarbeitet werden: pseudonymisierte
   Krankengeschichte (HPO-codiert, Initialen statt Klarname, kein exaktes Geburtsdatum)
   und ggf. zusammengefasste Genetik-**Ergebnisse** (nicht das Rohgenom).
4. **## Wo gespeichert** — Speicherort: ein **lokaler bzw. geteilter, verschlüsselter
   Ordner** (z. B. verschlüsselte Dropbox), **KEIN Server**, keine Cloud-Datenbank.
   Genetik-Rohdaten (VCF) bleiben rein lokal auf dem Rechner.
5. **## Verarbeitung über die Claude-API** — ehrlich: Chat-Inhalte gehen zur
   Beantwortung transient an die Anthropic/Claude-API; Anthropic trainiert **nicht**
   auf API-Daten; durch die Pseudonymisierung enthalten die übertragenen Inhalte
   keinen Klarnamen (angelehnt an `docs/security.md`, ohne deren Server-Teil).
6. **## Pseudonymisierung** — wie pseudonymisiert wird (Initialen, Alter statt
   Geburtsdatum) und warum.
7. **## Rechte (Widerruf, Löschung)** — Recht auf Widerruf der Einwilligung
   jederzeit, Recht auf Löschung (Ordner/Akte löschen), Auskunft, Berichtigung.
8. **## Aufbewahrung** — wie lange die Akte aufbewahrt wird und dass sie bei Widerruf
   oder Wegfall des Zwecks gelöscht wird.

Am Ende ein Unterschriften-/Datums-Block mit Platzhaltern (Ort, Datum, Name der/des
Sorgeberechtigten, Unterschrift) — generisch, keine echten Personen.

## Files
```
docs/consent-template.md   (NEU)
```

## Reality Check (Pflicht — vor Promotion nach `2.ready/`)
- [x] **Files in `Scope`/`Files`**: `docs/consent-template.md` wird bewusst NEU
      angelegt. `ls docs/` zeigt aktuell `architektur.md mockups security.md` —
      `consent-template.md` existiert noch nicht. `docs/` existiert.
- [x] **`depends_on`-IDs**: keine. Reine Doku-Vorlage, unabhängig von Code. Inhaltlich
      konsistent mit `docs/security.md` (Pseudonymisierung, kein Training auf API-Daten),
      aber **ohne** deren Server-/Hetzner-Teil (siehe Notes).
- [x] **Externe Voraussetzungen**: keine. Kein Download, kein Secret, kein Server.
- [x] **Tooling**: `grep` für die Baustein- und Negativ-Checks verfügbar.
      `markdownlint` ist im Repo **nicht** installiert → markdownlint-Check ist
      „falls verfügbar".

## Acceptance
- [ ] Datei existiert: `test -f docs/consent-template.md`
- [ ] Alle Pflicht-Bausteine vorhanden, per `grep`:
      `grep -qiE 'keine Rechtsberatung' docs/consent-template.md &&
       grep -qiE 'Zweck' docs/consent-template.md &&
       grep -qiE '(welche Daten|gespeicherte Daten|verarbeitete Daten)' docs/consent-template.md &&
       grep -qiE '(lokal|geteilt).*(verschlüsselt|Ordner)|verschlüsselt' docs/consent-template.md &&
       grep -qiE 'Claude-API|Anthropic' docs/consent-template.md &&
       grep -qiE 'Pseudonymisierung' docs/consent-template.md &&
       grep -qiE 'Widerruf' docs/consent-template.md &&
       grep -qiE 'Löschung' docs/consent-template.md &&
       grep -qiE 'Aufbewahrung' docs/consent-template.md`
- [ ] Als Vorlage markiert (Platzhalter vorhanden), z. B.:
      `grep -qE '\[[^]]+\]' docs/consent-template.md`
- [ ] Keine offensichtlich kaputten relativen Links (jedes `](…)`-Ziel auf eine
      Repo-Datei existiert).
- [ ] markdownlint-sauber, **falls verfügbar**:
      `command -v markdownlint >/dev/null && markdownlint docs/consent-template.md || true`
- [ ] **Negativ-Check (Architektur):** erwähnt KEINEN Server/Hetzner/AVV — der Ort ist
      lokal/verschlüsselt, es gibt keinen Auftragsverarbeiter-Server:
      `! grep -qiE 'hetzner|librechat|\bserver\b|server-deployment|\bAVV\b|auftragsverarbeit|postgres' docs/consent-template.md`
- [ ] **Negativ-Check (Datenschutz):** keine echten Patientendaten, Namen oder
      Geburtsdaten — nur Platzhalter wie `[Name]`, `[Initialen]`, `[Datum]`.

## Out of scope
- **DPA/AVV mit Anthropic:** Ein Auftragsverarbeitungsvertrag mit Anthropic ist ein
  organisatorischer Schritt des Betreibers, nicht Teil dieser Einwilligungs-Vorlage.
  Die Vorlage **erwähnt** die API-Verarbeitung, regelt aber keinen Vertrag.
- **Server-/Hosting-Datenschutz:** Es gibt keinen Server und keinen Hosting-AVV in
  dieser Architektur (lokal, optional geteilt). Die alte `docs/security.md`-Tabelle nennt noch
  Hetzner — das gehört **nicht** in die Vorlage (siehe Notes).
- **Rechtsgültige Endfassung:** Die Vorlage ist ein Muster; die fallspezifische,
  rechtsgeprüfte Fassung erstellt der Betreiber selbst.

## Notes
- **„Keine Rechtsberatung" ist Pflicht.** Der Disclaimer steht ganz oben und ist
  Acceptance-relevant. Die Vorlage darf nicht den Eindruck einer fertigen,
  rechtsgeprüften Erklärung erwecken.
- **Kein Server, kein AVV-Server.** In dieser Architektur liegen die Daten lokal bzw.
  in einem lokalen, optional geteilten Ordner — es gibt keinen Hetzner-Server und
  keinen serverseitigen Auftragsverarbeiter. `docs/security.md` enthält noch Alt-
  Referenzen (Hetzner, Postgres, AVV) aus der verworfenen Server-Architektur (siehe
  `AGENTS.md`, 2026-06-04 Architektur-Pivot) — **nicht** in die Vorlage übernehmen.
  Der Negativ-Check erzwingt das. Die Bereinigung von `security.md` ist nicht Scope
  dieses Tickets.
- **Konsistenz mit security.md, selektiv.** Übernehmbar sind die *inhaltlichen*
  Aussagen: Pseudonymisierung (Initialen, kein Geburtsdatum), „Anthropic trainiert
  nicht auf API-Daten", Datensparsamkeit, VCF bleibt lokal. Nicht übernehmbar ist
  alles Serverbezogene.
- **Platzhalter statt Daten.** Überall `[Platzhalter]` verwenden. Niemals einen echten
  Namen, kein echtes Geburtsdatum, keine echten Initialen einer realen Person.
