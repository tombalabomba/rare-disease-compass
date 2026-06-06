---
id: COM-02
title: rdc trials — klinische Studien (ClinicalTrials.gov)
status: done
depends_on: [CLI-01]
stop_after: false
epic: community
commit_type: feat(community)
---

# COM-02 — rdc trials: ClinicalTrials.gov

## Why
Rekrutierende Studien sind ein doppelter Hebel: ein Weg zu **spezialisierten
Zentren** und zu **anderen Betroffenen**, und manchmal die einzige Chance auf eine
neue Therapie. Eine offene, gut abfragbare Quelle dafür fehlt RDC noch.

## Scope
- Neue Quelle `cli/rdc/sources/trials.py`, eingehängt über die Registry (CLI-01):
  - `rdc trials search <begriff>` — Studien zu einer Krankheit/einem Gen über die
    **ClinicalTrials.gov API v2** (`https://clinicaltrials.gov/api/v2/studies`,
    JSON, keine Auth).
  - Optionen: `--recruiting` (nur aktiv rekrutierende), `--country <land>`,
    `--limit`.
  - Ausgabe pro Studie: NCT-ID (als Link `https://clinicaltrials.gov/study/<NCT>`),
    Titel, Status, Phase, Orte/Land. Eintrag in die SQLite-History.

## Files
```
cli/rdc/sources/trials.py     (NEU)
cli/rdc/main.py               (erweitert: trials-Subapp registrieren)
cli/tests/test_trials.py      (NEU)
```

## Reality Check
- [x] CLI-Kern + Registry existieren (CLI-01 in `3.done/`); Einbindung analog zu
      den bestehenden `sources/*.py`.
- [x] ClinicalTrials.gov API v2 ist öffentlich und ohne Key; exakte Query-Parameter
      (z. B. `query.cond`, `filter.overallStatus=RECRUITING`, `pageSize`) werden
      beim Bau gegen die Live-API verifiziert (wie bei den anderen CLI-Quellen).
- [x] Externe Voraussetzungen: keine Secrets.

## Acceptance
- [ ] `ruff check cli/` grün; `python -m py_compile`; `rdc trials --help` vorhanden.
- [ ] `pytest cli/tests/test_trials.py` grün — **gemocktes HTTP**, kein echter Call.
- [ ] Test belegt: NCT-ID wird zu vollständigem `clinicaltrials.gov/study/<NCT>`-Link;
      `--recruiting` setzt den Status-Filter korrekt.
- [ ] Negativ-Check: keine Patientendaten in die Abfrage; History speichert nur den
      Suchbegriff.

## Out of scope
- Patientenorganisationen/RareConnect → COM-01.
- Matchmaking → COM-03.
- Die zusammenführende Skill → COM-04.

## Notes
ClinicalTrials.gov v2 ist gut dokumentiert; bei der Ortsausgabe knapp halten
(Land + ggf. erste 1-2 Standorte), nicht die volle Standortliste, sonst wird die
Tabelle unübersichtlich.
