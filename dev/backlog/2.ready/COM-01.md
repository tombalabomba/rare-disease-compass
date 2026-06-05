---
id: COM-01
title: rdc community — Patientenorganisationen + RareConnect-Communities
status: todo
depends_on: [CLI-01]
stop_after: false
epic: community
commit_type: feat(community)
---

# COM-01 — rdc community: Patientenorganisationen + RareConnect

## Why
Das stärkste Bedürfnis Betroffener ist, **andere mit derselben Erkrankung** zu
finden (siehe Recherche zu Patienten-Communities). Das deckt RDC bislang nicht ab.
Dieser Befehl schlägt aus einer Krankheit die menschlichen Anlaufstellen nach:
Patientenorganisationen und die passende RareConnect-Community.

## Scope
- Neue Quelle `cli/rdc/sources/community.py`, eingehängt über die Registry (CLI-01):
  - `rdc community orgs <disease|ORPHAcode|MONDO>` — **Patientenorganisationen** zur
    Krankheit. Quelle: Orphanet/Orphadata („rare diseases and associated
    organisations"). Ausgabe: Name, Land, anklickbarer Link (Website/Orphanet).
  - `rdc community rareconnect <disease|ORPHAcode>` — die passende
    **RareConnect**-Community (EURORDIS). RareConnect hat **keine Daten-API** →
    deshalb als anklickbarer **Wegweiser**: direkte Community-URL falls per
    Slug/kuratierter Liste auflösbar, sonst eine RareConnect-Such-/Browse-URL für
    die Krankheit. Nie behaupten, eine Community existiere, ohne den Link zu liefern.
- Knappe, agenten-freundliche Ausgabe; jede Zeile mit klickbarem Link; Eintrag in
  die SQLite-History wie bei den anderen Quellen.

## Files
```
cli/rdc/sources/community.py   (NEU)
cli/rdc/main.py                (erweitert: community-Subapp registrieren)
cli/tests/test_community.py    (NEU)
```

## Reality Check
- [x] CLI-Kern + Registry existieren (CLI-01 in `3.done/`); neue Quelle hängt sich
      analog zu `sources/graph.py`/`orphanet` ein.
- [x] Orphanet ist bereits angebunden (`rdc orphanet`, `sources/graph.py`) — die
      Organisations-Daten kommen aus derselben Orphanet/Orphadata-Familie; exakter
      Endpoint/Datensatz wird beim Bau gegen die Live-API verifiziert (wie bei den
      anderen CLI-Quellen).
- [x] Externe Voraussetzungen: keine Secrets. RareConnect ohne Auth (nur Links).

## Acceptance
- [ ] `ruff check cli/` grün; `python -m py_compile`; `rdc community --help` listet
      `orgs` und `rareconnect`.
- [ ] `pytest cli/tests/test_community.py` grün — mit **gemocktem HTTP**
      (`httpx.MockTransport`), kein echter Call im Test.
- [ ] Test belegt: jede Ergebniszeile enthält einen vollständigen `http(s)://`-Link
      (keine nackten IDs); RareConnect-Befehl liefert immer eine URL.
- [ ] Negativ-Check: keine Patientendaten in Code/Test; History speichert nur die
      Abfrage (Krankheit), keine PII.

## Out of scope
- Genetisches Matching (Matchmaker Exchange / MyGene2) → COM-03.
- Klinische Studien → COM-02.
- Die zusammenführende Skill `/finde-deine-leute` → COM-04.

## Notes
RareConnect-Community-Liste ist klein und stabil; falls eine kuratierte
Slug-Zuordnung sinnvoll ist, als kleine Datendatei im Paket ablegen (öffentliche
Community-Liste, **keine** Patientendaten). Beim Bau kurz prüfen, ob Orphanet die
Organisationen über den bereits genutzten Zugang liefert oder ein eigener
Orphadata-Datensatz nötig ist.
