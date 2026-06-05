# Security & Datenschutz

Es geht um **besondere Kategorien personenbezogener Daten** (Gesundheitsdaten,
ggf. eines Kindes, Art. 9 DSGVO). Diese Datei ist verbindlich.

## Grundprinzipien

1. **Lokal zuerst.** Es gibt keinen Server. Die Fallakte lebt in einem lokalen
   Ordner. Sollen zwei Personen ihn teilen, optional über einen geteilten,
   verschlüsselten Ordner (z. B. Dropbox/Nextcloud). Genetik-Rohdaten (VCF) bleiben
   rein lokal, außerhalb eines etwaigen geteilten Ordners.
2. **Datensparsamkeit.** Nur was gebraucht wird. Aus der Genetik fließt nur die
   kuratierte Ergebnis-Zusammenfassung weiter, keine Rohzeilen.
3. **Pseudonymisierung.** In der Fallakte stehen Initialen, kein Klarname, kein
   exaktes Geburtsdatum (nur Alter / Monat-Jahr wo nötig).
4. **Privacy by default.** Das Repo enthält nie echte Daten (siehe `.gitignore`).
   Öffentliche Datenbanken werden nur abgefragt, nie befüllt.
5. **Einwilligung.** Dokumentierte Einwilligung des/der Sorgeberechtigten,
   inklusive der Verarbeitung in Anthropics Cloud (Claude Code rechnet nicht
   lokal). Vorlage: `docs/consent-template.md`.

## Wo welche Daten liegen

| Daten | Ort | Schutz |
|---|---|---|
| Fallakte (pseudonymisiert) | lokaler Ordner (optional geteilt, z. B. verschlüsselte Dropbox) | Festplatten-/Ordner-Verschlüsselung, Zugriff nur für Berechtigte |
| Genetik-Rohdaten (VCF) | **nur lokal**, nicht im geteilten Ordner | verlässt die Maschine nicht |
| Exomiser-Ergebnis | als Teil der Fallakte (kuratiert) | wie Fallakte |
| CLI-History (SQLite) | lokal, gitignored | kann fallbezogene Suchen enthalten → nicht teilen |
| Chat-Inhalte (Inferenz) | transient an Anthropics Server (API/Abo/Cloud-Provider) | Training je nach Anmeldeart — Bedingungen prüfen |
| Secrets / API-Keys | lokale Konfig, gitignored | nie im Repo |

## Maschinen-Härtung (Mindeststandard)

- Festplatten-Verschlüsselung (FileVault / LUKS) auf jeder Maschine, die die Akte hält.
- Bildschirmsperre, starkes Login.
- Geteilter Akte-Ordner nur für die berechtigten Personen freigegeben.
- Genetik-Rohdaten in einem separaten, **nicht** geteilten Pfad.

## Der ehrliche Punkt: die Inferenz läuft in der Cloud

**Claude Code ist ein lokales Werkzeug, aber kein lokales Modell.** Der Agent läuft
auf deinem Rechner, die eigentliche KI-Rechenleistung (Inferenz) jedoch auf
Anthropics Servern. Deine Fragen und die Aktendaten, die Claude zum Beantworten
liest, werden also an Anthropic übertragen — das ist bei jedem Claude-System so
(Claude Code, API, Web), nicht umgehbar, solange man Claude nutzt.

Was genau dahinter steht, hängt von der **Anmeldeart** ab (Anthropic-API,
Claude-Abo Pro/Max oder Cloud-Provider wie Bedrock/Vertex). Die Bedingungen zur
Datennutzung und insbesondere zum **Training** unterscheiden sich danach. Über die
**Anthropic-API** werden Inhalte standardmäßig nicht zum Training genutzt; für
Abo-/Consumer-Kanäle gelten andere, 2025 geänderte Regeln. **Vor dem Einsatz mit
echten Gesundheitsdaten die für deine Anmeldeart geltenden Anthropic-Bedingungen
prüfen** — hier wird bewusst nichts pauschal versprochen.

Mitigationen:
- Fallakte pseudonymisiert → übertragene Inhalte enthalten keinen Klarnamen.
- Genetik-Rohdaten (VCF) bleiben lokal, werden nie übertragen.
- Wer **null** externe Verarbeitung will, müsste ein lokales Open-Weight-Modell
  fahren — deutlich schwächere Qualität. Bewusste Entscheidung dagegen.

## Incident-Regel

PII-Leck entdeckt (echte Daten im Repo, in einem Log, in der CLI-History eines
geteilten Ordners, in einem öffentlichen Call)? → sofort stoppen, `status: blocked`,
Leck-Pfad benennen, nicht committen/pushen.
