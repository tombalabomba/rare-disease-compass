# Security & Datenschutz

Es geht um **besondere Kategorien personenbezogener Daten** (Gesundheitsdaten
eines Kindes, Art. 9 DSGVO). Diese Datei ist verbindlich.

## Grundprinzipien

1. **Datensparsamkeit.** Nur was gebraucht wird. Genetik-Rohdaten (VCF) werden
   lokal ausgewertet, nur Ergebnisse fließen weiter.
2. **Pseudonymisierung.** In der Fallakte stehen Initialen, kein Klarname, kein
   exaktes Geburtsdatum (nur Alter / Monat-Jahr wo nötig).
3. **Privacy by default.** Repo enthält nie echte Daten (siehe `.gitignore`).
   Öffentliche Datenbanken werden nur abgefragt, nie befüllt.
4. **Einwilligung.** Dokumentierte Einwilligung des Sorgeberechtigten (Matze),
   inklusive Verarbeitung über die Anthropic-API. Vorlage: `epic-onboarding` / ONB-03.

## Wo welche Daten liegen

| Daten | Ort | Schutz |
|---|---|---|
| Fallakte (pseudonymisiert) | Hetzner-Server EU, Postgres-Volume | Disk-Encryption, Login, Backup verschlüsselt |
| Genetik-Rohdaten (VCF) | **nur lokal** auf Thomas' Rechner | verlässt den Rechner nicht |
| Exomiser-Ergebnis | Server (als Teil der Akte) | wie Fallakte |
| Chat-Inhalte (Inferenz) | transient an Anthropic-API | DPA, kein Training auf API-Daten |
| Secrets / API-Keys | `.env` (lokal/gitignored) + Server-Secret-Store | nie im Repo |

## Server-Härtung (Mindeststandard, siehe INF-04)

- Non-root-User, SSH nur per Key, Passwort-Login aus.
- Firewall (ufw): nur 22 (SSH, idealerweise IP-beschränkt), 80/443 (Caddy).
- `fail2ban`, automatische Sicherheitsupdates.
- Festplatten-/Volume-Verschlüsselung.
- Nur HTTPS exponiert; alles andere intern im Docker-Netz.

## App-Härtung

- LibreChat-Registrierung **deaktiviert**; User werden manuell angelegt.
- Zwei-Faktor für alle Konten.
- Starke, einzigartige Secrets (`JWT_SECRET`, `CREDS_KEY`, DB-Passwörter).

## Der ehrliche Punkt: Anthropic-API

Chat-Inhalte gehen zur Verarbeitung an die Anthropic-API. Das ist bei jedem
Claude-System so. Mitigationen:
- Anthropic trainiert **nicht** auf API-Daten (Standard).
- DPA / Auftragsverarbeitung mit Anthropic abschließen.
- Fallakte pseudonymisiert → selbst die übertragenen Inhalte enthalten keinen Klarnamen.
- Wer **null** externe Verarbeitung will, müsste ein lokales Open-Weight-Modell
  fahren — deutlich schwächere Qualität. Bewusste Entscheidung gegen diesen Weg.

## Auftragsverarbeiter (AVV/DPA)

- **Hetzner**: AVV im Konto aktivieren (EU-Rechenzentrum wählen, z. B. Nürnberg/Falkenstein).
- **Anthropic**: DPA abschließen.

## Incident-Regel

PII-Leck entdeckt (echte Daten im Repo, in einem Log, in einem öffentlichen Call)?
→ sofort stoppen, `status: blocked`, Leck-Pfad benennen, nicht committen/pushen.
