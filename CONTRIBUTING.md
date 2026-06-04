# Contributing

Danke für dein Interesse. Dieses Projekt ist ein lokaler, datenschutzfreundlicher
Recherche-Assistent für seltene Krankheitsfälle. Beiträge sind willkommen.

## Goldene Regel: keine echten Patientendaten

Niemals echte Gesundheitsdaten, Namen, Geburtsdaten, VCF-/Genom-Dateien oder
Befunde committen. Tests und Beispiele verwenden ausschließlich **synthetische,
erfundene** Fixtures. Siehe [.gitignore](.gitignore) und [docs/security.md](docs/security.md).

## Kein Medizinprodukt

Dieses Werkzeug ist Recherche-Unterstützung, keine medizinische Beratung. Beiträge,
die diesen Charakter verändern würden (z. B. Funktionen, die Diagnosen aussprechen),
werden nicht angenommen. Outputs nennen Quellen und überlassen die Bewertung
qualifizierten Ärztinnen und Ärzten.

## Arbeitsweise

Das Projekt wird über ein Ticket-Backlog gebaut. Siehe
[dev/backlog/README.md](dev/backlog/README.md) und [dev/backlog/PLAN.md](dev/backlog/PLAN.md).

- Neue Idee → Ticket in `dev/backlog/1.planning/` nach `dev/backlog/TICKET-TEMPLATE.md`.
- Baufertig → nach `dev/backlog/2.ready/` (Reality-Check ausgefüllt).
- Ein Commit pro Ticket, Conventional-Commit-Prefix.

## Qualität

- Python: `ruff check` + `ruff format`, `pytest`, Typannotationen.
- Shell: `shellcheck`-clean, `set -euo pipefail`.
- Öffentliche APIs höflich behandeln: Cache + Rate-Limit nutzen (CLI-Kern).

## Lizenz

Mit dem Beitrag stimmst du zu, dass dein Code unter der [MIT-Lizenz](LICENSE)
veröffentlicht wird.
