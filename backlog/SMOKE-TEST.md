# Smoke-Test (manuell, beim Deployment)

Checks, die einen laufenden Server brauchen und deshalb NICHT Teil der
Ticket-Acceptance der Bau-Phase sind. Beim Deployment (DEP-04/DEP-05) abarbeiten.

## TLS & Proxy
- [ ] `https://<host>` lädt mit gültigem Zertifikat.
- [ ] `http://<host>` leitet auf `https` um.
- [ ] Security-Header gesetzt (`curl -sI https://<host>` zeigt HSTS etc.).

## Container
- [ ] `docker compose ps` — alle Services `healthy`.
- [ ] `docker compose logs --tail=50` ohne Fehlerschleifen.

## Chat & RAG
- [ ] Login funktioniert (Thomas + Matze, mit 2FA).
- [ ] Frage mit Akten-Bezug liefert Antwort, die die Akte zitiert.

## MCP-Tools (Live-Datenanbindung)
- [ ] Eine Frage löst einen PubMed-Call aus (BioMCP).
- [ ] Eine Symptom-Frage löst einen PubCaseFinder- oder Monarch-Call aus (eigener MCP).
- [ ] Antworten nennen Quellen.

## Datenschutz
- [ ] `mcp-server` nicht von außen erreichbar (nur internes Docker-Netz).
- [ ] Keine echten Patientendaten in Logs.
