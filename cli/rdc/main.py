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


def render(
    rows: list[dict[str, Any]],
    headers: list[str],
    *,
    json_override: bool = False,
    empty: str = "(keine Einträge)",
) -> None:
    """Rendert ``rows`` als Tabelle oder JSON-Lines.

    Single source of truth fürs Rendern: das globale ``--json``/``--format``
    bestimmt das Format; ein Quellen-Subkommando kann es per ``json_override``
    (sein lokales ``--json``) gezielt auf JSON-Lines zwingen.
    """
    fmt = OutputFormat.jsonl if json_override else _state["format"]
    if fmt is OutputFormat.jsonl:
        output.print_jsonl(rows)
        return
    if not rows:
        typer.echo(empty)
        return
    table_rows = [[row.get(header) for header in headers] for row in rows]
    output.print_table(table_rows, headers)


HISTORY_HEADERS = [
    "id",
    "timestamp",
    "source",
    "command",
    "result_count",
    "result_summary",
]


def _render(rows: list[dict[str, Any]]) -> None:
    render(rows, HISTORY_HEADERS)


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


# Quellen-Gruppen registrieren sich über die Registry. ``literature`` und
# ``compound`` importieren ``main`` nur lazy (in den Befehls-Funktionen), daher
# entsteht hier kein Import-Zyklus.
from . import compound  # noqa: E402
from .sources import community, ddx, graph, literature, variant  # noqa: E402

register(
    "pubmed",
    literature.pubmed_app,
    "PubMed-Literatursuche (NCBI E-utilities).",
)
register(
    "europepmc",
    literature.europepmc_app,
    "Europe-PMC-Literatursuche (REST).",
)
register(
    "variant",
    variant.variant_app,
    "Varianten-Bewertung (MyVariant.info: ClinVar + gnomAD).",
)
register(
    "monarch",
    graph.monarch_app,
    "Krankheits-Graph (Monarch): Phänotyp→Krankheit, Gen→Krankheit.",
)
register(
    "orphanet",
    graph.orphanet_app,
    "Orphanet/Orphadata: Eintrag per ORPHA-Code oder Name nachschlagen.",
)
register(
    "pubcasefinder",
    ddx.pubcasefinder_app,
    "Differentialdiagnose (PubCaseFinder): HPO-Profil → gerankte Krankheiten.",
)
register(
    "phen2gene",
    ddx.phen2gene_app,
    "Differentialdiagnose (Phen2Gene): HPO-Profil → gerankte Kandidatengene.",
)
register(
    "compound",
    compound.compound_app,
    "Compound Queries: quellenübergreifende Phänotyp-Abklärung (DDx + Graph).",
)
register(
    "community",
    community.community_app,
    "Community: Patientenorganisationen + RareConnect-Communities (Wegweiser).",
)


if __name__ == "__main__":
    app()
