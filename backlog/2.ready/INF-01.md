---
id: INF-01
title: Docker-Compose-Stack (LibreChat + MongoDB + Meilisearch + pgvector + rag_api)
status: todo
depends_on: []
stop_after: false
epic: infra
commit_type: feat(infra)
---

# INF-01 — Docker-Compose-Stack (LibreChat + MongoDB + Meilisearch + pgvector + rag_api)

## Why
Ohne lauffähigen Stack gibt es keinen Assistenten. LibreChat braucht zwingend
einen `api`-Service plus MongoDB (App-Daten: User, Chats, Agents), Meilisearch
(Volltext-Suche) und für RAG einen `rag_api`-Service mit einer pgvector-Datenbank
(`vectordb`). Dieses Ticket legt das Fundament, auf dem alle weiteren Infra-Tickets
(Caddy, librechat.yaml, Backup) und sämtliche anderen Epics aufsetzen. Fehlt es,
steht das gesamte Projekt.

## Scope
- `docker-compose.yml` mit allen Services:
  - `api` — LibreChat-Frontend/-Backend, **einziger** Service, der später hinter
    den Proxy kommt (in diesem Ticket noch **kein** Port-Mapping nach außen; das
    übernimmt Caddy in INF-02). Interner Port 3080.
  - `mongodb` — App-Datenbank, nur intern, eigenes Volume.
  - `meilisearch` — Suche, nur intern, eigenes Volume, `MEILI_NO_ANALYTICS=true`.
  - `vectordb` — Postgres mit pgvector-Image, nur intern, eigenes Volume.
  - `rag_api` — LibreChat-RAG-API, spricht `vectordb`, nur intern.
- **Healthchecks** für `mongodb`, `meilisearch`, `vectordb`, `rag_api` und `api`.
- **Internes Netz** (`bridge`), in dem alle Services hängen; `depends_on` mit
  `condition: service_healthy` für die richtige Startreihenfolge.
- **Benannte Volumes** für Mongo-Daten, Meili-Daten, Postgres-Daten, LibreChat-
  Uploads/Logs.
- `.env.example` mit **allen** in der Compose referenzierten Variablen als
  **Platzhalter** (kein echter Wert): `ANTHROPIC_API_KEY`, `JWT_SECRET`,
  `JWT_REFRESH_SECRET`, `CREDS_KEY`, `CREDS_IV`, `MONGO_URI`, `MEILI_MASTER_KEY`,
  `MEILI_HOST`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `RAG_PORT`,
  `RAG_API_URL`, `EMBEDDINGS_PROVIDER`, `DOMAIN_CLIENT`, `DOMAIN_SERVER`.
- Sicherstellen, dass `.env` gitignored ist (Eintrag prüfen/ergänzen; Drive-by
  ≤ 10 Zeilen, falls Eintrag fehlt).

## Files
```
docker-compose.yml   (NEU)
.env.example         (NEU)
```

## Reality Check (Pflicht — vor Promotion nach `2.ready/`)

- [x] **Files in `Scope`/`Files`**: `docker-compose.yml` und `.env.example`
      existieren noch nicht (`ls docker-compose.yml .env.example` → not found),
      werden bewusst NEU angelegt.
- [x] **`depends_on`-IDs**: keine — INF-01 ist das Wurzel-Ticket des Epics
      (siehe README-Graph). Nichts vorausgesetzt.
- [x] **Externe Voraussetzungen**: keine für das Schreiben/Validieren der Files.
      Echte Secret-Werte und der laufende Server sind **nicht** Teil dieses
      Tickets (`.env.example` enthält nur Platzhalter). Hinweis im `## Notes`.
- [x] **Tooling**: `docker compose ... config` validiert ohne laufenden Daemon
      (reine Config-Validierung). Docker-CLI als Standard-Tooling angenommen
      (CLAUDE.md Tech-Stack).

## Acceptance
- [ ] `docker compose -f docker-compose.yml config` validiert ohne Fehler.
- [ ] `.env.example` enthält **jede** in `docker-compose.yml` per `${VAR}`
      referenzierte Variable (Abgleich: jede referenzierte Variable taucht als
      Key in `.env.example` auf — per `grep -oE '\$\{[A-Z_]+' docker-compose.yml`
      gegen die Keys in `.env.example`).
- [ ] Services `api`, `mongodb`, `meilisearch`, `vectordb`, `rag_api` sind in der
      Config vorhanden (`docker compose -f docker-compose.yml config --services`).
- [ ] Jeder Service außer `api` hat einen `healthcheck`-Block (grep).
- [ ] **Negativ-Check**: kein echter Secret-Wert im Diff — alle Werte in
      `.env.example` sind Platzhalter (z. B. `changeme`, `replace-me`,
      `<your-...>`), kein `sk-ant-`-Prefix, keine echten Passwörter
      (`grep -E 'sk-ant-|BEGIN.*PRIVATE' .env.example` liefert nichts).
- [ ] **Negativ-Check**: außer dem (in INF-02 hinzukommenden) Proxy exponiert
      kein Service Ports nach außen — in diesem Ticket gibt es **keinen**
      `ports:`-Eintrag in `docker-compose.yml` (`grep -E '^\s*ports:' docker-compose.yml`
      liefert nichts).

## Out of scope
- Caddy / Port-Mapping nach außen → INF-02 (Defense-in-Depth: hier bewusst noch
  kein `ports:`).
- Inhaltliche LibreChat-Config (Endpoints, Registrierung, RAG-Feinheiten) →
  INF-03 (`librechat.yaml`).
- Backup, Provisioning → INF-05, INF-04.
- Echte Secret-Befüllung und Deployment → manuell auf dem Server.

## Notes
- `.env.example` ist die **dokumentierte** Vorlage und gehört ins Repo; die echte
  `.env` ist gitignored und wird auf dem Server befüllt (siehe docs/security.md
  „Wo welche Daten liegen"). Platzhalter müssen klar als solche erkennbar sein.
- LibreChat erwartet `MONGO_URI`, `MEILI_*`, `RAG_*` als Umgebung; die genauen
  Image-Tags (`librechat`, `mongo`, `meilisearch`, `pgvector`, `librechat-rag-api`)
  beim Bau gegen die aktuelle LibreChat-Doku gegenprüfen, Versionen pinnen (kein
  `:latest`).
- Healthcheck-Hosts: `mongodb` per `mongosh --eval`, `meilisearch` per
  `/health`-Endpoint, `vectordb` per `pg_isready`, `rag_api` per HTTP-Health.
