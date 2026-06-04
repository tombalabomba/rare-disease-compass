# Fallakte — FIXTURE (synthetisch)

<!--
  SYNTHETISCHES Beispiel. Erfundenes Kind, keine reale Person.
  Dient als Test-Fixture (KB-02 PII-Guard, KB-03 Ordner-Validierung) und als
  Anschauungsbeispiel. Folgt exakt docs/case-file-TEMPLATE.md.

  Person erfunden. HPO-IDs sind real existierende öffentliche Codes — die
  ZUORDNUNG zu dieser erfundenen Person ist frei erfunden.
-->

## Stammdaten

- **Initialen:** L. K.
- **Alter:** 6 Jahre
- **Geschlecht:** weiblich

## Zeitleiste

- Säuglingsalter (ca. 8 Monate) — wiederkehrende wässrige Durchfälle, Gedeihstörung.
- 2. Lebensjahr — erste stationäre Abklärung, Verdacht auf Nahrungsmittelallergie.
- 4. Lebensjahr — rezidivierende Fieberschübe, Vorstellung in der pädiatrischen Gastroenterologie.
- 6. Lebensjahr (aktuell) — Aufnahme in die Spezialambulanz für seltene Erkrankungen.

## Symptome

| Symptom | HPO-ID | seit wann |
|---|---|---|
| Chronischer Durchfall | HP:0002028 | seit Säuglingsalter |
| Gedeihstörung | HP:0001508 | seit Säuglingsalter |
| Rezidivierendes Fieber | HP:0001954 | seit 4. Lebensjahr |
| Orale Aphthen | HP:0000155 | seit 5. Lebensjahr |

## Befunde

- **Endoskopie:** Koloskopie mit fleckförmigen Ulzerationen im terminalen Ileum.
- **Histologie:** Chronisch-aktive Entzündung, vereinzelt Granulome.
- **Labor:** CRP erhöht, Hypalbuminämie, Calprotectin im Stuhl deutlich erhöht.

## Ausgeschlossenes

- Zöliakie ausgeschlossen (Transglutaminase-Serologie negativ, Duodenalbiopsie unauffällig).
- Klassische Nahrungsmittelallergie ausgeschlossen (Eliminationsdiät ohne Effekt).
- Infektiöse Genese ausgeschlossen (Stuhlkulturen wiederholt negativ).

## Genetik-Zusammenfassung

_Wird von `rdc`/GEN-03 aus dem Exomiser-Ergebnis erzeugt._

## Offene Fragen

- Monogene Form einer sehr früh beginnenden chronisch-entzündlichen Darmerkrankung (VEO-IBD)?
- Lohnt eine gezielte Panel-Diagnostik vor der Exom-Auswertung?
- Familienanamnese bislang unauffällig — De-novo-Variante plausibel?

## Medikation

- Mesalazin — gewichtsadaptiert — seit 4. Lebensjahr — partielles Ansprechen.
- Eisensubstitution oral — seit 5. Lebensjahr — bei Eisenmangelanämie.
