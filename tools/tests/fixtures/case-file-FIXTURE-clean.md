# Fallakte — FIXTURE CLEAN (synthetisch, sauber)

<!--
  SYNTHETISCHE, saubere Test-Fixture für KB-02 (PII-Guard).
  Erfundenes Kind, keine reale Person. Enthält BEWUSST kein PII:
  nur Initialen, Alter (keine Geburtsdaten), HPO-Symptome und medizinische
  Eigennamen (z. B. „Morbus Crohn"), die KEINEN Klarnamen-Alarm auslösen dürfen.
-->

## Stammdaten

- **Initialen:** L. K.
- **Alter:** 6 Jahre
- **Geschlecht:** weiblich

## Zeitleiste

- Säuglingsalter (ca. 8 Monate) — wiederkehrende wässrige Durchfälle, Gedeihstörung.
- 4. Lebensjahr — rezidivierende Fieberschübe, Vorstellung in der Gastroenterologie.
- 6. Lebensjahr (aktuell) — Aufnahme in die Spezialambulanz für seltene Erkrankungen.

## Symptome

| Symptom | HPO-ID | seit wann |
|---|---|---|
| Chronischer Durchfall | HP:0002028 | seit Säuglingsalter |
| Gedeihstörung | HP:0001508 | seit Säuglingsalter |
| Rezidivierendes Fieber | HP:0001954 | seit 4. Lebensjahr |

## Befunde

- **Endoskopie:** Koloskopie mit fleckförmigen Ulzerationen im terminalen Ileum.
- **Histologie:** Chronisch-aktive Entzündung, vereinzelt Granulome.
- **Labor:** CRP erhöht, Hypalbuminämie, Calprotectin im Stuhl deutlich erhöht.

## Ausgeschlossenes

- Morbus Crohn als klassische Verlaufsform bislang nicht bestätigt.
- Marfan-Syndrom klinisch unwahrscheinlich (keine skelettalen Auffälligkeiten).
- Zöliakie ausgeschlossen (Transglutaminase-Serologie negativ).

## Genetik-Zusammenfassung

_Wird von `rdc`/GEN-03 aus dem Exomiser-Ergebnis erzeugt._

## Offene Fragen

- Monogene Form einer sehr früh beginnenden chronisch-entzündlichen Darmerkrankung?
- Lohnt eine gezielte Panel-Diagnostik vor der Exom-Auswertung?
