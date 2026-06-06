---
id: COM-03
title: Wegweiser zu genetischem Matching (Matchmaker Exchange / MyGene2) — kein Auto-Submit
status: done
depends_on: [CLI-01]
stop_after: false
epic: community
commit_type: feat(community)
---

# COM-03 — Genetisches Matching: Wegweiser statt Auto-Submit

## Why
Für „finde jemanden mit **genau derselben Genvariante**" gibt es Matchmaker
Exchange (MME) und MyGene2. Das ist mächtig, aber heikel: Zugang ist gated
(Kliniker/Forscher), und man würde die Gen-/Symptomdaten eines Kindes in ein
Matching-Netz **einreichen** — eine ernste Einwilligungs-Entscheidung. RDC darf das
**niemals automatisch** tun. Stattdessen: klarer, einwilligungs-gegateter Wegweiser.

## Scope
- `docs/connect-genetic-matching.md` — erklärt in einfacher Sprache:
  - **Matchmaker Exchange** (Verbund: GeneMatcher, DECIPHER, PhenomeCentral, MyGene2 …):
    der Weg läuft über die **Humangenetik/behandelnde Klinik** (z. B. GeneMatcher-
    Einreichung durch Ärzt:innen) — mit Link.
  - **MyGene2**: der Weg für **Familien, die selbst offen teilen wollen** — mit Link.
  - **Starke Einwilligungs-/Datenschutz-Hinweise**: was eingereicht würde, dass es
    Daten eines Kindes sind, dass dies eine bewusste, dokumentierte Entscheidung der
    Sorgeberechtigten ist (Verweis `docs/consent-template.md`, `docs/security.md`).
  - Klarstellung: **RDC reicht nichts ein und überträgt keine Daten an diese Netze.**
- `rdc community matchmaking` — ein **reiner Info-Befehl**: gibt diese Wegweiser +
  Links aus (statisch, kein Netzwerk, keine Datenübertragung).
- **Pointer-Prinzip festschreiben:** In `config/assistant-instructions.md` einen Satz
  ergänzen — relevante Ressourcen, die RDC **nicht** direkt abfragt (Matching-Netze,
  Register o. Ä.), immer als anklickbaren **Wegweiser** nennen, nie verschweigen und
  nie automatisch ansteuern.

## Files
```
docs/connect-genetic-matching.md   (NEU)
cli/rdc/sources/community.py        (erweitert: matchmaking-Info-Befehl)  [falls COM-01 schon da; sonst eigenständig in main.py]
config/assistant-instructions.md    (erweitert: Pointer-Prinzip, 1 Satz)
cli/tests/test_community_matchmaking.py (NEU)
```

## Reality Check
- [x] `config/assistant-instructions.md` existiert (KB-04 in `3.done/`).
- [x] Reiner Info-/Doku-Befehl ohne externe API → kein Live-Verify nötig; nur Links
      werden ausgegeben.
- [x] Externe Voraussetzungen: keine. (Aktueller Status der Plattformen wird beim
      Schreiben der Doku kurz geprüft und der Stand datiert vermerkt.)

## Acceptance
- [ ] `docs/connect-genetic-matching.md` enthält per grep: `Matchmaker`, `MyGene2`,
      `GeneMatcher`, „Einwilligung", „RDC reicht nichts ein" (oder gleichbedeutend).
- [ ] `rdc community matchmaking` läuft **offline** und gibt die Links/Hinweise aus
      (Test: kein HTTP-Aufruf, Ausgabe enthält die erwarteten URLs).
- [ ] `config/assistant-instructions.md` enthält das Pointer-Prinzip (grep
      „Wegweiser" + „nicht direkt").
- [ ] Negativ-Check: **kein** Code-Pfad überträgt Daten an MME/MyGene2/GeneMatcher
      (grep: keine POST-/Submit-Calls an diese Hosts).

## Out of scope
- Eine echte, automatisierte MME-Abfrage/-Einreichung — bewusst ausgeschlossen.

## Notes
Ton behutsam und ermächtigend (Persona EXP-01): die Option benennen, die Kontrolle
bei der Familie lassen, und klar sagen, dass der übliche Weg über die Humangenetik
führt.
