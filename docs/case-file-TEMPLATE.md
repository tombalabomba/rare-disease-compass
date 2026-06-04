# Fallakte — Template

<!--
  Verbindliches Schema für eine pseudonymisierte, HPO-codierte Fallakte.
  Claude Code liest diese Datei als Klartext. Die HPO-IDs (Format HP:0000000)
  sind der Verbindungsschlüssel zu den öffentlichen Datenbanken (PubCaseFinder,
  Phen2Gene, Monarch).

  DATENSCHUTZ (siehe docs/security.md):
  - KEIN Klarname. Nur Initialen (z. B. "M. M.").
  - KEIN exaktes Geburtsdatum. Nur Alter in Jahren.
  - Niemals VCF-/Genom-Dateien oder Befund-PDFs hier einbetten.

  Die Überschriften (## ...) sind verbindlich und werden maschinell geprüft
  (KB-03 Ordner-Validierung, GEN-03 füllt ## Genetik-Zusammenfassung). Nicht
  umbenennen — sonst brechen die abhängigen Tickets.

  Echte Fallakten heißen `case-file-<kürzel>.md` und sind per .gitignore
  gesperrt. Nur dieses Template und synthetische Fixtures sind erlaubt.
-->

## Stammdaten

<!--
  Pseudonymisiert. KEIN Klarname, KEIN exaktes Geburtsdatum (docs/security.md).
  Nur Initialen, Alter in Jahren, Geschlecht.
-->

- **Initialen:** _z. B. M. M._
- **Alter:** _in Jahren, z. B. 7 Jahre_
- **Geschlecht:** _männlich / weiblich / divers_

## Zeitleiste

<!-- Chronologischer Verlauf der Krankengeschichte (älteste zuerst). -->

- _Jahr/Alter — Ereignis (Erstsymptom, Vorstellung, Klinikaufenthalt …)_

## Symptome

<!--
  Symptome als HPO-Tabelle. Jede Zeile braucht eine gültige HPO-ID
  (Format HP: gefolgt von 7 Ziffern). HPO-Vokabular nachschlagen via CLI.
  "seit wann" als Alter oder relativer Zeitpunkt.
-->

| Symptom | HPO-ID | seit wann |
|---|---|---|
| _z. B. Chronischer Durchfall_ | HP:0002028 | _z. B. seit 2. Lebensjahr_ |

## Befunde

<!-- Endoskopie / Histologie / Labor. Untergliederung nach Bedarf. -->

- **Endoskopie:** _Befund_
- **Histologie:** _Befund_
- **Labor:** _Befund_

## Ausgeschlossenes

<!-- Bereits ausgeschlossene Diagnosen/Differentialdiagnosen (mit Begründung). -->

- _z. B. Zöliakie ausgeschlossen (Serologie negativ, Histologie unauffällig)_

## Genetik-Zusammenfassung

<!--
  Platzhalter. Diese Sektion wird von `rdc` (GEN-03) aus dem Exomiser-Ergebnis
  automatisch erzeugt und hier eingesetzt. Überschrift exakt so belassen —
  GEN-03 produziert denselben String, um die Sektion an der richtigen Stelle
  einzufügen. Manuell nichts eintragen.
-->

_Wird von `rdc`/GEN-03 aus dem Exomiser-Ergebnis erzeugt._

## Offene Fragen

<!-- Offene Fragen und Arbeitshypothesen. -->

- _z. B. Monogene Ursache vs. polygen? Nächster diagnostischer Schritt?_

## Medikation

<!-- Aktuelle und frühere Medikation / Therapie-Verlauf. -->

- _Wirkstoff — Dosis — Zeitraum — Ansprechen_
