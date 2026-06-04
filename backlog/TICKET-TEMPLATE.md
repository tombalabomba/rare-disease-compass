---
id: XX-NN
title: Kurztitel (eine Zeile, was getan wird)
status: todo                  # todo | in_progress | blocked | done
depends_on: []                # IDs anderer Tickets, z. B. [INF-01, MCP-02]
stop_after: false             # default false. true nur bei echten Cliffs (Server, Secret)
epic: ""                      # Short-Slug, z. B. infra. "" wenn standalone
commit_type: feat(scope)      # Conventional-Commit-Prefix, z. B. feat(infra), chore(mcp)
---

# XX-NN — <Titel>

## Why
Ein bis drei Sätze: warum existiert dieses Ticket, was passiert wenn wir es
**nicht** machen, an welches Epic/Problem hängt es?

## Scope
Was genau gebaut wird. Konkrete Dateien, Funktionen, Endpoints, Configs. Liste
oder Tabelle. Was passiert hier ja — nicht was wir weglassen (das gehört unter
„Out of scope").

## Files
```
pfad/zu/neuer-datei.py          (NEU)
pfad/zu/bestehender-datei.yaml  (erweitert: Abschnitt XY)
```

## Reality Check (Pflicht — vor Promotion nach `2.ready/`)
**Bevor das Ticket promotet wird, muss diese Sektion ausgefüllt und alle Items
mit `[x]` markiert sein.** Eine ungeklärte Annahme = Ticket bleibt in `1.planning/`.

Verifiziere jede Annahme im Scope/Acceptance/Files mit konkretem **Repo-Pfad : Zeile**
oder **Befehl + Output**. Keine Worte wie „existiert vermutlich".

- [ ] **Files in `Scope`/`Files`**: existieren schon (für „erweitern", mit `ls`
      verifiziert) oder werden bewusst NEU angelegt.
- [ ] **`depends_on`-IDs**: Tickets existieren; vorausgesetzte Funktionalität ist
      nach deren `done` wirklich vorhanden.
- [ ] **Externe Voraussetzungen**: Secrets, Server, Account-Setups, herunterzuladende
      Daten — entweder erledigt ODER als Hinweis im `## Notes` + ggf. `stop_after: true`.
- [ ] **Tooling**: benötigte CLIs/Libs (`docker`, `python`, `ruff`, `shellcheck`)
      sind verfügbar oder im Ticket als Installationsschritt benannt.

Annahme nicht haltbar → `⚠ OPEN: <was fehlt + Vorschlag>` listen, Ticket in
`1.planning/` belassen.

## Acceptance
Konkrete, **maschinell prüfbare** Checks. Keine Browser-/Live-Server-Tests hier
(die wandern in `2.ready/<epic>/SMOKE-TEST.md`). Beispiele:
- [ ] `docker compose -f <file> config` validiert ohne Fehler
- [ ] `ruff check .` und `pytest` grün
- [ ] `shellcheck <script>` ohne Findings
- [ ] YAML/JSON-Schema valide (`python -c "import yaml,sys; yaml.safe_load(...)"`)
- [ ] Negativ-Check (z. B. keine echten Daten / kein Secret im Diff)

## Out of scope
Was bewusst draußen bleibt, mit kurzer Begründung. Verhindert Scope-Creep.

## Notes
Optional. Vorabklärungen, Tool-Quirks, Konventionen, externe Setups, die der Agent
vor Implementation kennen muss.

## Stop-Gate (nur wenn `stop_after: true`)
Was der Mensch nach diesem Ticket manuell tut, bevor das nächste starten darf
(z. B. Server provisionieren, Secret in den Store legen, VCF lokal bereitstellen).
