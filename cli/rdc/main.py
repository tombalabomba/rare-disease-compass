"""Top-Level-Typer-App ``rdc`` mit Subkommando-Registry.

CLI-01 legt den framework-freien Kern an: die App, **eine** Registry, über die
Folge-Tickets (CLI-02…06) ihre Quellen-Gruppen anhängen, und die eingebaute
``history``-Gruppe auf der lokalen SQLite-History.

Quellen-Gruppen werden hier noch **keine** registriert — sie kommen in den
Folge-Tickets dazu und hängen sich über :func:`register` an.
"""

from __future__ import annotations

import enum
from typing import Any

import typer

from . import __version__, history, output

app = typer.Typer(
    name="rdc",
    help="RareDiseaseCompass — Recherche-CLIs für seltene Erkrankungen.",
    no_args_is_help=True,
    add_completion=False,
)


class OutputFormat(enum.StrEnum):
    """Ausgabeformat der Ergebnisse."""

    table = "table"
    jsonl = "jsonl"


# Single source of truth für das gewählte Ausgabeformat.
_state: dict[str, OutputFormat] = {"format": OutputFormat.table}

# Single source of truth für registrierte Quellen-Gruppen.
_registered: list[str] = []


def register(name: str, sub: typer.Typer, help: str) -> None:
    """Hängt eine Quellen-Subkommando-Gruppe an die Top-Level-App.

    Der **eine** Mechanismus, über den CLI-02…06 ihre Gruppe registrieren —
    keine zweite Parallel-Registry anlegen (Single source of truth).
    """
    app.add_typer(sub, name=name, help=help)
    _registered.append(name)


def registered_groups() -> list[str]:
    """Namen der bisher registrierten Quellen-Gruppen (für Tests/Introspektion)."""
    return list(_registered)


@app.callback()
def _main(
    output_format: OutputFormat = typer.Option(
        OutputFormat.table,
        "--format",
        "-f",
        help="Ausgabeformat: table oder jsonl.",
    ),
    json_: bool = typer.Option(
        False,
        "--json",
        help="Kurzform für --format jsonl.",
    ),
) -> None:
    """Globale Optionen, die für alle Subkommandos gelten."""
    _state["format"] = OutputFormat.jsonl if json_ else output_format


def _render(rows: list[dict[str, Any]]) -> None:
    if _state["format"] is OutputFormat.jsonl:
        output.print_jsonl(rows)
        return
    if not rows:
        typer.echo("(keine Einträge)")
        return
    headers = [
        "id",
        "timestamp",
        "source",
        "command",
        "result_count",
        "result_summary",
    ]
    table_rows = [[row.get(header) for header in headers] for row in rows]
    output.print_table(table_rows, headers)


history_app = typer.Typer(
    help="Lokale, durchsuchbare Recherche-History (SQLite).",
    no_args_is_help=True,
)


@history_app.command("list")
def history_list(
    limit: int = typer.Option(20, "--limit", "-n", help="Maximale Anzahl Einträge."),
    source: str | None = typer.Option(
        None, "--source", "-s", help="Nur Einträge dieser Quelle."
    ),
) -> None:
    """Listet die jüngsten Abfragen (neueste zuerst)."""
    conn = history.connect(history.default_db_path())
    _render(history.list_queries(conn, limit=limit, source=source))


@history_app.command("search")
def history_search(
    term: str = typer.Argument(..., help="Suchbegriff (LIKE über Quelle/Command/…)."),
    limit: int = typer.Option(50, "--limit", "-n", help="Maximale Anzahl Treffer."),
) -> None:
    """Durchsucht die History über Quelle, Command, Params und Summary."""
    conn = history.connect(history.default_db_path())
    _render(history.search_queries(conn, term, limit=limit))


@app.command("version")
def version() -> None:
    """Zeigt die installierte rdc-Version."""
    typer.echo(__version__)


app.add_typer(history_app, name="history")


if __name__ == "__main__":
    app()
