# dev/ — Bau-Werkzeug

Dieses Verzeichnis ist die **Werkstatt**, nicht das Produkt. Wer RareDiseaseCompass
nur **nutzen** will, braucht hier nichts (siehe Haupt-[README](../README.md),
Abschnitt „Repo-Struktur"). Hier liegt nur, womit das Projekt **gebaut** wird.

## Inhalt

```
dev/
├── agent-loop.sh     # autonome Build-Loop: baut Ticket für Ticket aus backlog/2.ready/
└── backlog/          # Tickets + Planung
    ├── PLAN.md          # Projekt-Übersicht: Ziele, Modul-Karte, Abhängigkeitsgraph
    ├── README.md        # Backlog-Konventionen
    ├── AGENT-LOOP.md    # Operating-Manual für eine autonome Loop-Iteration
    ├── AGENT-TICKET.md  # Operating-Manual für genau ein Ticket
    ├── TICKET-TEMPLATE.md
    ├── 1.planning/      # noch nicht baufertige Ideen
    ├── 2.ready/         # baufertige Tickets (der Loop greift hier zu)
    └── 3.done/          # erledigte Tickets (Historie)
```

## Bauen

```bash
# Aus dem Repo-Root:
bash dev/agent-loop.sh status     # Überblick über alle Tickets
bash dev/agent-loop.sh            # autonom abarbeiten (frische Session pro Ticket)
```

Die Loop läuft aus dem Repo-Root, damit Produkt-Pfade (`cli/`, `skills/`, …) korrekt
aufgelöst werden. Details: [backlog/AGENT-LOOP.md](backlog/AGENT-LOOP.md).

## Warum im Repo?

Transparenz: Wer will, sieht genau, wie und mit welcher Planung RareDiseaseCompass
entstanden ist, und kann eigene Tickets beitragen (siehe
[../CONTRIBUTING.md](../CONTRIBUTING.md)). Das Verzeichnis schadet Nutzern nicht — es
ist nur nicht Teil des installierbaren Produkts.
