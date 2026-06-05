# Genetisches Matching — Wegweiser, kein Auto-Submit

> **Stand: 2026-06-06** (Plattform-Links beim Schreiben geprüft). Diese Seite ist ein
> **Wegweiser**. RareDiseaseCompass (RDC) **reicht nichts ein** und überträgt **keine
> Daten** an die hier genannten Netze. Jede Einreichung ist eine bewusste,
> dokumentierte Entscheidung — siehe [Einwilligung](consent-template.md) und
> [Datenschutz](security.md).

## Worum es geht

Manchmal ist die wichtigste Frage: *„Gibt es irgendwo auf der Welt noch ein Kind mit
**genau derselben** Genvariante?"* Ein einziger weiterer Fall kann aus einer
„Variante unklarer Bedeutung" eine Diagnose machen. Dafür gibt es spezialisierte
**Matching-Netze**. Sie sind mächtig — aber sie funktionieren, indem die genetischen
und Symptom-Daten einer Person (hier: oft eines Kindes) in ein Netzwerk **eingereicht**
werden. Das ist eine ernste Einwilligungs-Entscheidung und gehört in ärztliche Hände.

**RDC stellt diese Wege nur dar.** Es ruft die Netze nicht ab, reicht nichts ein und
steuert sie nicht automatisch an. Den Schritt gehen Sie (die Sorgeberechtigten)
gemeinsam mit der Humangenetik bzw. der behandelnden Klinik.

## Weg 1 — über die Humangenetik / behandelnde Klinik (üblicher Weg)

Der reguläre Weg läuft über das **Matchmaker Exchange** (MME), einen Verbund mehrerer
Matching-Datenbanken, die über eine gemeinsame Schnittstelle miteinander suchen.
Teilnehmende Knoten sind u. a. **GeneMatcher**, **DECIPHER**, **PhenomeCentral**,
**MyGene2**, RD-Connect, Monarch Initiative und PubCaseFinder.

- **Matchmaker Exchange** — Überblick & Funktionsweise:
  <https://www.matchmakerexchange.org/>
- **Teilnehmende Knoten** (welche Datenbank wofür):
  <https://www.matchmakerexchange.org/participants.html>
- **GeneMatcher** — gen-basiertes Matching. Die **Einreichung erfolgt durch
  Ärzt:innen / Forschende** (Zugang ist auf Kliniker:innen und Forschende
  beschränkt): <https://genematcher.org/>

**Was Sie tun können:** Bringen Sie das Thema im nächsten Termin in der Humangenetik
auf. Eine konkrete, vorlesbare Frage: *„Wäre eine Einreichung über GeneMatcher /
Matchmaker Exchange für die bei uns gefundene Variante sinnvoll — und würden Sie das
für uns übernehmen?"*

## Weg 2 — Familien, die selbst offen teilen wollen: MyGene2

**MyGene2** ist darauf ausgelegt, dass **Familien selbst** ihre genetischen und
gesundheitlichen Informationen offen teilen, um andere Familien, Kliniker:innen und
Forschende mit demselben Gen zu finden.

- **MyGene2**: <https://www.mygene2.org/>

Das ist eine bewusst **offene** Form des Teilens. Sie kann verbinden, bedeutet aber
auch, dass Sie selbst entscheiden, welche Daten eines Kindes öffentlich werden. Lesen
Sie die Hinweise der Plattform und besprechen Sie es vorab mit der Humangenetik.

## Einwilligung & Datenschutz — bitte vor jeder Einreichung lesen

- **Was eingereicht würde:** genetische Befunde (Variante/Gen) und phänotypische
  Merkmale (Symptome, oft HPO-codiert) — also sensible **Gesundheitsdaten**.
- **Wessen Daten:** in aller Regel die **Daten eines Kindes**. Die Entscheidung
  treffen die **Sorgeberechtigten**, idealerweise gemeinsam mit der behandelnden
  Humangenetik.
- **Bewusste, dokumentierte Entscheidung:** eine Einreichung ist nicht rückgängig zu
  machen, sobald Daten geteilt wurden. Halten Sie die **Einwilligung** schriftlich
  fest — Vorlage: [consent-template.md](consent-template.md). Hintergrund zum
  Umgang mit sensiblen Daten: [security.md](security.md).
- **RDC reicht nichts ein.** Es gibt in RDC **keinen** Code-Pfad, der Daten an
  Matchmaker Exchange, GeneMatcher oder MyGene2 überträgt. Der CLI-Befehl
  `rdc community matchmaking` gibt **ausschließlich** diese Wegweiser und Links aus —
  vollständig offline.

## CLI

```
rdc community matchmaking          # gibt die Wegweiser + Links aus (offline)
rdc community matchmaking --json   # dieselben Zeilen als JSON-Lines
```

Der Befehl macht **keinen** Netzwerk-Aufruf und überträgt **keine** Daten. Er ist ein
reiner Informations-/Wegweiser-Befehl.
