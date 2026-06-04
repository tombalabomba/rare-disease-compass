---
id: INF-03
title: LibreChat librechat.yaml (Anthropic, Registrierung aus, RAG, Agents, mcpServers-Platzhalter)
status: todo
depends_on: [INF-01]
stop_after: false
epic: infra
commit_type: feat(infra)
---

# INF-03 — LibreChat `librechat.yaml` (Anthropic, Registrierung aus, RAG, Agents, mcpServers-Platzhalter)

## Why
Der Compose-Stack startet LibreChat, aber ohne App-Config verhält es sich falsch:
offene Registrierung, kein Anthropic-Endpoint, kein RAG, keine Agents. Diese Datei
konfiguriert LibreChat genau so, wie das Projekt es braucht — Claude als einziges
Modell, Selbstregistrierung aus (User manuell), RAG/File-Handling an, Agents an,
und ein dokumentierter `mcpServers`-Platzhalter, den `epic-mcp` (MCP-01/MCP-06)
später füllt. Ohne sie ist die App entweder unsicher oder unbrauchbar.

## Scope
- `librechat.yaml` mit:
  - `version` und Grundgerüst gemäß LibreChat-Config-Schema.
  - **Anthropic-Endpoint** unter `endpoints`: Modell `claude-opus-4-8` als
    verfügbares (und default) Modell; API-Key über Umgebungsreferenz
    (`${ANTHROPIC_API_KEY}`), **kein** Klartext-Key.
  - **Registrierung deaktiviert**: `registration: { socialLogins: [], allowedDomains: [] }`
    und Self-Registration aus (kein E-Mail-Signup). User werden manuell angelegt
    (docs/security.md).
  - **RAG / fileConfig aktiviert**: File-Uploads/Endpoints so konfiguriert, dass
    die RAG-API (aus INF-01) genutzt wird.
  - **Agents-Endpoint** aktiviert.
  - **`mcpServers`**-Block als **dokumentierter Platzhalter**: vorhanden, leer
    bzw. mit Kommentar „wird in epic-mcp (MCP-01/MCP-06) gefüllt". Kein
    funktionsloser Stub-Server, sondern ein leerer, kommentierter Map-Key.

## Files
```
librechat.yaml   (NEU)
```

## Reality Check (Pflicht — vor Promotion nach `2.ready/`)

- [x] **Files in `Scope`/`Files`**: `librechat.yaml` existiert noch nicht
      (`ls librechat.yaml` → not found), wird NEU angelegt.
- [x] **`depends_on`-IDs**: INF-01 stellt den `api`-Service (LibreChat) und den
      `rag_api`-Service bereit, auf die diese Config sich bezieht. `ANTHROPIC_API_KEY`
      ist in INF-01s `.env.example` als Variable bereits referenziert.
- [x] **Externe Voraussetzungen**: echter Anthropic-API-Key wird erst zur Laufzeit
      via `.env` gesetzt (nicht in dieser Datei). Kein Server, kein Live-Test nötig,
      um die YAML zu validieren. Hinweis in `## Notes`.
- [x] **Tooling**: `python` mit `yaml`-Modul (PyYAML) für `yaml.safe_load` —
      Standard-Python-Tooling (CLAUDE.md). Kein laufender LibreChat nötig.

## Acceptance
- [ ] YAML lädt fehlerfrei:
      `python -c "import yaml; yaml.safe_load(open('librechat.yaml'))"` ohne Exception.
- [ ] Registrierung nachweislich deaktiviert: Self-Registration ist aus
      (Prüfung im geladenen YAML, dass `registration.socialLogins == []` und
      `registration.allowedDomains == []` bzw. das Signup-Flag falsch/leer ist) —
      per `python`-Assertion auf das geladene Dict.
- [ ] `mcpServers`-Key existiert auf Top-Level (`python`-Assertion `'mcpServers' in cfg`).
- [ ] Modell `claude-opus-4-8` ist im Anthropic-Endpoint hinterlegt
      (`grep -F 'claude-opus-4-8' librechat.yaml`).
- [ ] **Negativ-Check**: kein echter API-Key im File — der Anthropic-Key kommt als
      Umgebungsreferenz, nicht als Literal (`grep -E 'sk-ant-' librechat.yaml`
      liefert nichts).

## Out of scope
- Tatsächliche MCP-Server-Einträge im `mcpServers`-Block → `epic-mcp` (MCP-01/MCP-06).
- Anlegen konkreter User → manueller Betreiber-Schritt (epic-onboarding).
- Endpoint-Feintuning (Token-Limits, weitere Modelle) → nur falls später nötig.

## Notes
- Der API-Key steht **niemals** in `librechat.yaml`, sondern in `.env`
  (gitignored) als `ANTHROPIC_API_KEY` und wird per `${ANTHROPIC_API_KEY}`
  referenziert (docs/security.md).
- LibreChat-Config-Schema beim Bau gegen die aktuelle Doku gegenprüfen
  (Schlüsselnamen für `endpoints`, `registration`, `fileConfig`, `mcpServers`
  ändern sich versionsweise). Versionsfeld auf die im INF-01 gepinnte
  LibreChat-Version abstimmen.
- `mcpServers` als leeren Map-Key mit erklärendem Kommentar hinterlegen — das ist
  ein bewusster, dokumentierter Anker, kein verbotener Stub.
