# Security & Datenschutz

Es geht um **besondere Kategorien personenbezogener Daten** (Gesundheitsdaten,
ggf. eines Kindes, Art. 9 DSGVO). Diese Datei ist verbindlich.

## Grundprinzipien

1. **Lokal zuerst.** Es gibt keinen Server. Die Fallakte lebt in einem lokalen
   Ordner (für die Zwei-Rollen-Nutzung in einer verschlüsselten, geteilten
   Dropbox). Genetik-Rohdaten (VCF) bleiben rein lokal, außerhalb des geteilten
   Ordners.
2. **Datensparsamkeit.** Nur was gebraucht wird. Aus der Genetik fließt nur die
   kuratierte Ergebnis-Zusammenfassung weiter, keine Rohzeilen.
3. **Pseudonymisierung.** In der Fallakte stehen Initialen, kein Klarname, kein
   exaktes Geburtsdatum (nur Alter / Monat-Jahr wo nötig).
4. **Privacy by default.** Das Repo enthält nie echte Daten (siehe `.gitignore`).
   Öffentliche Datenbanken werden nur abgefragt, nie befüllt.
5. **Einwilligung.** Dokumentierte Einwilligung des/der Sorgeberechtigten,
   inklusive Verarbeitung über die Claude-API. Vorlage: `docs/consent-template.md`.

## Wo welche Daten liegen

| Daten | Ort | Schutz |
|---|---|---|
| Fallakte (pseudonymisiert) | lokaler / geteilter Ordner (verschlüsselte Dropbox) | Festplatten-/Ordner-Verschlüsselung, Zugriff nur für Berechtigte |
| Genetik-Rohdaten (VCF) | **nur lokal**, nicht im geteilten Ordner | verlässt die Maschine nicht |
| Exomiser-Ergebnis | als Teil der Fallakte (kuratiert) | wie Fallakte |
| CLI-History (SQLite) | lokal, gitignored | kann fallbezogene Suchen enthalten → nicht teilen |
| Chat-Inhalte (Inferenz) | transient an die Claude-API | kein Training auf API-Daten |
| Secrets / API-Keys | lokale Konfig, gitignored | nie im Repo |

## Maschinen-Härtung (Mindeststandard)

- Festplatten-Verschlüsselung (FileVault / LUKS) auf jeder Maschine, die die Akte hält.
- Bildschirmsperre, starkes Login.
- Geteilter Akte-Ordner nur für die berechtigten Personen freigegeben.
- Genetik-Rohdaten in einem separaten, **nicht** geteilten Pfad.

## Der ehrliche Punkt: Claude-API

Chat-Inhalte gehen zur Verarbeitung an die Claude-API. Das ist bei jedem
Claude-System so, auch lokal. Mitigationen:
- Anthropic trainiert **nicht** auf API-Daten (Standard).
- Fallakte pseudonymisiert → übertragene Inhalte enthalten keinen Klarnamen.
- Wer **null** externe Verarbeitung will, müsste ein lokales Open-Weight-Modell
  fahren — deutlich schwächere Qualität. Bewusste Entscheidung dagegen.

## Incident-Regel

PII-Leck entdeckt (echte Daten im Repo, in einem Log, in der CLI-History eines
geteilten Ordners, in einem öffentlichen Call)? → sofort stoppen, `status: blocked`,
Leck-Pfad benennen, nicht committen/pushen.
