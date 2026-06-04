# Agent-Ticket — universell, ein Ticket pro Session

Operating-Anweisung für die manuelle Bearbeitung **genau eines** namentlich
benannten Tickets. Nach Commit STOP — kein automatisches Springen zum nächsten.

Single-Ticket-Variante von `backlog/AGENT-LOOP.md`. Disziplinen, Bug-/Lern-Regeln,
Commit-Format sind identisch — siehe dort.

## Trigger
- „Bitte arbeite INF-01 nach `backlog/AGENT-TICKET.md` ab."
- „Bitte mach das nächste Ticket aus `epic-cli` (Loop-Modus aus)."

Wenn keine ID übergeben: prüfe, ob genau **ein** Ticket in `backlog/2.ready/`
(rekursiv) `status: in_progress` hat. Wenn ja: das. Wenn null oder mehrere:
**STOP**, frag welches.

## Bearbeitung
Identische Schritte wie AGENT-LOOP.md §1–§8, mit zwei Unterschieden:
1. **Kein Auto-Pick** — ID kommt vom User. Nicht in `2.ready/` zu finden? STOP,
   melde wo das Ticket liegt (`1.planning/`? schon `done/`?).
2. **Stop-Gate-Marker nicht nötig** — diese Variante stoppt sowieso nach jedem
   Ticket. Aber `stop_after: true` ernst nehmen: den manuellen Check-Hinweis im
   finalen Output erwähnen.

## Finaler Output (immer)
- Ticket-ID + Titel
- Was gemacht wurde (1–3 Zeilen)
- Acceptance-Status (alle ✓ oder welcher Punkt geblockt)
- Manuelle Folgeaufgaben (z. B. API-Key hinterlegen, Referenzdaten herunterladen)
- Welches Ticket laut `depends_on`-Graph als nächstes käme

**STOP.** Niemals automatisch zum nächsten Ticket springen.
