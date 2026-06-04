---
id: INF-02
title: Caddy Reverse Proxy + HTTPS + Security-Header
status: todo
depends_on: [INF-01]
stop_after: false
epic: infra
commit_type: feat(infra)
---

# INF-02 — Caddy Reverse Proxy + HTTPS + Security-Header

## Why
Der `api`-Service darf nicht nackt im Internet hängen. Caddy terminiert TLS
(automatisches Let's-Encrypt), erzwingt HTTPS und setzt Security-Header. Das ist
die einzige nach außen offene Schicht (Defense-in-Depth: App-Auth UND Proxy).
Ohne diesen Proxy gibt es kein verschlüsseltes, gehärtetes Frontend — bei
Gesundheitsdaten eines Kindes nicht verhandelbar.

## Scope
- `Caddyfile`:
  - Site-Block auf den (per Umgebung/Platzhalter konfigurierten) Domainnamen.
  - Automatisches TLS (Let's Encrypt) — Caddy-Default, kein manuelles Zertifikat.
  - HTTP→HTTPS-Redirect (Caddy-Standardverhalten bei gesetzter Domain; explizit
    sicherstellen, keine Klartext-Auslieferung).
  - `reverse_proxy` auf den internen `api`-Service (`api:3080`).
  - Security-Header per `header`-Direktive:
    - `Strict-Transport-Security` (HSTS, mit `max-age` und `includeSubDomains`)
    - `X-Content-Type-Options: nosniff`
    - `Referrer-Policy` (z. B. `strict-origin-when-cross-origin`)
    - `X-Frame-Options: DENY`
- `docker-compose.yml` erweitern: `caddy`-Service.
  - Einziger Service mit `ports:` — `80:80` und `443:443`.
  - Bindet `Caddyfile` ein, eigene Volumes für Caddy-Daten und -Config
    (Zertifikats-Persistenz).
  - Hängt im internen Netz, `depends_on: api`.

## Files
```
Caddyfile            (NEU)
docker-compose.yml   (erweitert: caddy-Service + ports + volumes)
```

## Reality Check (Pflicht — vor Promotion nach `2.ready/`)

- [x] **Files in `Scope`/`Files`**: `Caddyfile` wird NEU angelegt.
      `docker-compose.yml` wird erweitert — es existiert nach INF-01 (dort als NEU
      angelegt). Vor Implementierung mit `ls docker-compose.yml` verifizieren.
- [x] **`depends_on`-IDs**: INF-01 liefert `docker-compose.yml` mit dem
      `api`-Service auf 3080 ohne externes Port-Mapping — genau die Vorbedingung,
      die dieses Ticket braucht (Caddy übernimmt die Exponierung).
- [x] **Externe Voraussetzungen**: echte Domain + DNS-A-Record auf den Server
      sind nötig, damit Let's Encrypt im Live-Betrieb greift — das ist ein
      **manueller** Schritt nach dem Epic, **nicht** Teil der Acceptance. Im
      `Caddyfile` als Platzhalter-Domain bzw. Umgebungsvariable. Hinweis in `## Notes`.
- [x] **Tooling**: `caddy validate` ist Caddy-CLI; falls lokal nicht installiert,
      Fallback `docker run --rm -v $PWD/Caddyfile:/etc/caddy/Caddyfile caddy
      caddy validate --config /etc/caddy/Caddyfile --adapter caddyfile`.

## Acceptance
- [ ] `caddy validate --config Caddyfile --adapter caddyfile` läuft fehlerfrei —
      **oder** (falls Caddy lokal fehlt) der Docker-Fallback
      `docker run --rm -v "$PWD/Caddyfile":/etc/caddy/Caddyfile caddy caddy
      validate --config /etc/caddy/Caddyfile --adapter caddyfile`.
- [ ] Alle vier Security-Header-Direktiven sind im `Caddyfile` vorhanden:
      `grep -E 'Strict-Transport-Security|X-Content-Type-Options|Referrer-Policy|X-Frame-Options' Caddyfile`
      liefert vier Treffer.
- [ ] `reverse_proxy` zeigt auf `api` (`grep -E 'reverse_proxy.*api' Caddyfile`).
- [ ] `docker compose -f docker-compose.yml config` validiert weiterhin.
- [ ] `caddy`-Service ist in der Compose-Config vorhanden
      (`docker compose -f docker-compose.yml config --services` enthält `caddy`).
- [ ] **Negativ-Check**: nur `caddy` hat ein `ports:`-Mapping nach außen; kein
      anderer Service exponiert Ports (`grep -B5 -E '^\s*ports:' docker-compose.yml`
      zeigt ausschließlich den `caddy`-Block).

## Out of scope
- Live-Ausstellung des Zertifikats / DNS-Konfiguration → manueller Deploy-Schritt.
- WAF, Rate-Limiting, IP-Allowlisting → ggf. späteres Ticket, nicht hier.
- Server-Firewall (ufw 80/443) → INF-04.

## Notes
- Domain als Platzhalter (z. B. `assistant.example.org`) oder per Caddy-Env
  (`{$DOMAIN}`); echte Domain wird beim Deploy gesetzt. Let's-Encrypt-Ausstellung
  funktioniert erst, wenn DNS auf den Server zeigt und 80/443 erreichbar sind —
  das ist Deploy-Zeit, nicht Build-Zeit.
- HSTS erst aktivieren, wenn TLS sicher steht (sonst Lockout bei Fehlkonfig).
  `max-age` konservativ wählen, `includeSubDomains` nur wenn alle Subdomains TLS
  können.
- `caddy validate` braucht keinen laufenden Server und keine echte Domain — reine
  Syntax-/Adapter-Prüfung, daher als Acceptance geeignet.
