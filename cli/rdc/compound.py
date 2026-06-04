"""Compound Queries — quellenübergreifende Phänotyp-Abklärung.

Der eigentliche Mehrwert gegenüber rohen APIs: aus **einem** HPO-Profil in einem
Schritt Differentialdiagnose (PubCaseFinder/Phen2Gene), Krankheits-Graph
(Monarch) und — optional — Literatur (PubMed) kombinieren, Duplikate über die
Quellen hinweg zusammenführen und nach einem transparenten Konsens-Score ranken.

- ``rdc compound phenotype-workup <HPO...>`` — orchestriert die volle Abklärung.

Aufbau-Disziplin:

- **Wiederverwendung statt Neu-Implementierung.** Diese Gruppe ruft ausschließlich
  die bestehenden ``run_*``-Kernfunktionen aus ``sources/ddx.py``,
  ``sources/graph.py`` und ``sources/literature.py`` auf — **kein** zweiter
  HTTP-Pfad, keine Parsing-Duplikate (Single source of truth). Der gesamte
  Netzwerkverkehr bleibt beim zentralen :class:`~rdc.http_client.HttpClient`.
- **Reine Dedup-/Rank-Funktionen** (:func:`merge_disease_candidates`,
  :func:`merge_gene_candidates`) arbeiten ohne HTTP und sind direkt mit Fixtures
  testbar.
- **History als Speicher.** ``phenotype-workup`` schreibt einen eigenen
  ``compound``-Eintrag; die zugrundeliegenden Quellen-Aufrufe protokollieren
  weiterhin ihre Einzel-Einträge.
- **HPO-Validierung** über den CLI-05-Helper (:func:`ddx.validate_hpo_terms`) —
  kein Müll-Input, bevor eine Quelle angefasst wird.
- **Kein Diagnose-Anspruch.** Ausgegeben werden Daten + Quellen-IDs und ein
  regelbasierter Konsens-Score; die klinische Einordnung bleibt beim Menschen.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Iterable, Mapping, Sequence
from typing import Any

import typer

from . import history
from .http_client import HttpClient
from .sources import ddx, graph, literature

# Definierter Leerwert für fehlende Felder (statt None/Crash).
EMPTY = ""

# Default-Zahl ausgegebener Kandidaten je Liste.
DEFAULT_LIMIT = 20
# Default-Trefferzahl der optionalen Literatur-Suche zu den Top-Kandidaten.
LITERATURE_LIMIT = 5

# Feldnamen, unter denen die Quellen Krankheitsname bzw. Gen-Symbol ablegen.
_DISEASE_NAME_KEYS = ("disease", "name", "label", "disease_name")
_DISEASE_ID_KEYS = ("id", "disease_id")
_GENE_KEYS = ("gene", "symbol", "gene_symbol")
_GENE_ID_KEYS = ("gene_id", "id", "gene_ID")

# ID-Präfix-Synonyme → kanonische Form (Dedup über IDs, nicht über Namen).
_ID_PREFIX_ALIASES = {"ORPHANET": "ORPHA", "ORPHACODE": "ORPHA", "MIM": "OMIM"}

DISEASE_HEADERS = ["consensus", "best_rank", "id", "disease", "sources"]
GENE_HEADERS = ["consensus", "best_rank", "gene", "gene_id", "sources"]


# -- Normalisierung + Dedup/Ranking (reine Funktionen, ohne HTTP) ----------


def normalize_disease_id(raw: str) -> str:
    """Kanonisiert eine Krankheits-ID für die quellenübergreifende Dedup.

    Krankheiten heißen je nach Quelle leicht anders; zusammengeführt wird über
    die stabilen IDs (OMIM/ORPHA/MONDO). Das Präfix wird großgeschrieben und auf
    eine kanonische Form gebracht (``ORPHANET`` → ``ORPHA``, ``MIM`` → ``OMIM``),
    der Rest bleibt unverändert. IDs ohne ``:`` werden nur großgeschrieben.
    """
    token = (raw or "").strip()
    if not token:
        return EMPTY
    if ":" not in token:
        return token.upper()
    prefix, _, rest = token.partition(":")
    prefix = prefix.strip().upper()
    prefix = _ID_PREFIX_ALIASES.get(prefix, prefix)
    return f"{prefix}:{rest.strip()}"


def _rank_of(record: Mapping[str, Any], index: int) -> int:
    """Rang aus dem Record oder — fehlt er — die Quellen-Position (1-basiert)."""
    value = record.get("rank")
    try:
        return int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return index + 1


def _value_of(record: Mapping[str, Any], keys: tuple[str, ...]) -> str:
    """Erster nicht-leerer Wert unter ``keys`` (sonst Leerwert)."""
    for key in keys:
        value = record.get(key)
        if value not in (None, ""):
            return str(value)
    return EMPTY


def _merge_candidates(
    sources: Mapping[str, Sequence[Mapping[str, Any]]],
    *,
    key_of: Any,
    label_keys: tuple[str, ...],
    id_field: str,
    label_field: str,
    extra_keys: tuple[str, ...] | None = None,
) -> list[dict[str, object]]:
    """Führt gleiche Kandidaten über Quellen zusammen und rankt nach Konsens.

    ``key_of`` bildet aus einem Record den Dedup-Schlüssel (None = überspringen).
    Pro Quelle wird der **beste** (kleinste) Rang behalten. Der Konsens-Score ist
    die Zahl der stützenden Quellen; sortiert wird nach Konsens absteigend, dann
    bestem Rang, dann Schlüssel.
    """
    merged: dict[str, dict[str, Any]] = {}
    for source_name, records in sources.items():
        for index, record in enumerate(records):
            if not isinstance(record, Mapping):
                continue
            key = key_of(record)
            if not key:
                continue
            entry = merged.setdefault(
                key,
                {id_field: key, label_field: EMPTY, "ranks": {}},
            )
            label = _value_of(record, label_keys)
            if label and not entry[label_field]:
                entry[label_field] = label
            if extra_keys:
                extra = _value_of(record, extra_keys)
                if extra and not entry.get("_extra"):
                    entry["_extra"] = extra
            rank = _rank_of(record, index)
            previous = entry["ranks"].get(source_name)
            if previous is None or rank < previous:
                entry["ranks"][source_name] = rank

    rows: list[dict[str, object]] = []
    for entry in merged.values():
        ranks: dict[str, int] = entry["ranks"]
        supporting = sorted(ranks)
        row: dict[str, object] = {
            "consensus": len(supporting),
            "best_rank": min(ranks.values()) if ranks else 0,
            id_field: entry[id_field],
            label_field: entry[label_field],
            "sources": "; ".join(supporting),
        }
        if extra_keys is not None:
            row["_extra"] = entry.get("_extra", EMPTY)
        rows.append(row)
    rows.sort(
        key=lambda r: (
            -int(r["consensus"]),  # type: ignore[arg-type]
            int(r["best_rank"]),  # type: ignore[arg-type]
            str(r[id_field]),
        )
    )
    return rows


def merge_disease_candidates(
    sources: Mapping[str, Sequence[Mapping[str, Any]]],
) -> list[dict[str, object]]:
    """Krankheits-Kandidaten aus mehreren Quellen dedupen und ranken.

    Dedup über die normalisierte Krankheits-ID (OMIM/ORPHA/MONDO), **nicht** über
    den Freitext-Namen. Liefert je Krankheit einen Eintrag mit Konsens-Score
    (Zahl der stützenden Quellen), bestem Rang und der Quellen-Liste.
    """

    def key_of(record: Mapping[str, Any]) -> str:
        return normalize_disease_id(_value_of(record, _DISEASE_ID_KEYS))

    return _merge_candidates(
        sources,
        key_of=key_of,
        label_keys=_DISEASE_NAME_KEYS,
        id_field="id",
        label_field="disease",
    )


def merge_gene_candidates(
    sources: Mapping[str, Sequence[Mapping[str, Any]]],
) -> list[dict[str, object]]:
    """Gen-Kandidaten aus mehreren Quellen dedupen und ranken.

    Dedup über das normalisierte Gen-Symbol (Großschreibung). Liefert je Gen
    einen Eintrag mit Konsens-Score, bestem Rang, Gen-ID und Quellen-Liste.
    """

    def key_of(record: Mapping[str, Any]) -> str:
        return _value_of(record, _GENE_KEYS).strip().upper()

    rows = _merge_candidates(
        sources,
        key_of=key_of,
        label_keys=_GENE_KEYS,
        id_field="gene",
        label_field="_label",
        extra_keys=_GENE_ID_KEYS,
    )
    # Symbol als ``gene`` ausgeben (nicht den großgeschriebenen Dedup-Key) und
    # die mitgeführte Gen-ID in das öffentliche Feld heben.
    result: list[dict[str, object]] = []
    for row in rows:
        result.append(
            {
                "consensus": row["consensus"],
                "best_rank": row["best_rank"],
                "gene": row["_label"] or row["gene"],
                "gene_id": row.get("_extra", EMPTY),
                "sources": row["sources"],
            }
        )
    return result


def literature_query(
    diseases: Sequence[Mapping[str, Any]],
    genes: Sequence[Mapping[str, Any]],
) -> str:
    """Baut den Literatur-Suchbegriff aus dem Top-Kandidaten.

    Bevorzugt den Namen der bestplatzierten Krankheit (sonst deren ID); fällt auf
    das bestplatzierte Gen zurück. Leerer String, wenn nichts vorliegt.
    """
    for candidate in diseases:
        name = candidate.get("disease") or candidate.get("id")
        if name:
            return str(name)
    for candidate in genes:
        gene = candidate.get("gene")
        if gene:
            return str(gene)
    return EMPTY


# -- Kernlogik (Client + Connection injiziert) ----------------------------


def run_phenotype_workup(
    client: HttpClient,
    conn: sqlite3.Connection,
    *,
    hpo_ids: Iterable[str],
    limit: int = DEFAULT_LIMIT,
    with_literature: bool = True,
    literature_limit: int = LITERATURE_LIMIT,
) -> dict[str, object]:
    """HPO-Profil → kombinierte, gerankte Abklärung; protokolliert den Lauf.

    Ruft die bestehenden Quellen-Kernfunktionen (DDx, Graph, optional Literatur)
    auf, führt Krankheiten und Gene quellenübergreifend zusammen und schreibt
    einen ``compound``-History-Eintrag. :func:`ddx.validate_hpo_terms` läuft
    **zuerst**; bei ungültiger Eingabe wird ein :class:`ValueError` geworfen,
    bevor eine Quelle angefasst wird.
    """
    terms = ddx.validate_hpo_terms(hpo_ids)

    pubcasefinder = ddx.run_pubcasefinder_rank(
        client, conn, hpo_ids=terms, limit=limit
    )
    monarch = graph.run_diseases_by_phenotypes(
        client, conn, hpo_ids=terms, limit=limit
    )
    phen2gene = ddx.run_phen2gene_genes(client, conn, hpo_ids=terms, limit=limit)

    diseases = merge_disease_candidates(
        {"pubcasefinder": pubcasefinder, "monarch": monarch}
    )[:limit]
    genes = merge_gene_candidates({"phen2gene": phen2gene})[:limit]

    lit_records: list[dict[str, object]] = []
    query = literature_query(diseases, genes) if with_literature else EMPTY
    if query:
        lit_records = list(
            literature.run_pubmed_search(
                client, conn, term=query, retmax=literature_limit
            )
        )

    top = diseases[0]["disease"] or diseases[0]["id"] if diseases else "kein Treffer"
    history.save_query(
        conn,
        source="compound",
        command="phenotype-workup",
        params={
            "hpo": terms,
            "limit": limit,
            "with_literature": with_literature,
            "literature_query": query,
        },
        result_summary=f"{len(diseases)} Krankheiten / {len(genes)} Gene aus "
        f"{len(terms)} Phänotyp(en); Top: {top}",
        result_count=len(diseases),
        raw={"diseases": diseases, "genes": genes, "literature": lit_records},
    )
    return {
        "hpo": terms,
        "diseases": diseases,
        "genes": genes,
        "literature": lit_records,
    }


# -- Typer-Befehle (verdrahten Client/History und rendern) ----------------

compound_app = typer.Typer(
    help="Compound Queries: quellenübergreifende Phänotyp-Abklärung.",
    no_args_is_help=True,
)


def _render_workup(result: Mapping[str, Any], *, json_: bool) -> None:
    """Rendert die drei Abschnitte (Krankheiten, Gene, Literatur).

    Liest das effektive Ausgabeformat aus der **einen** Quelle der Wahrheit
    (:data:`rdc.main._state`); im JSON-Lines-Modus entfallen die Abschnitts-
    Überschriften, damit der Stream gültiges JSONL bleibt.
    """
    from rdc import main

    as_json = json_ or main._state["format"] is main.OutputFormat.jsonl

    if not as_json:
        typer.echo("# Differentialdiagnosen (Konsens über DDx + Graph)")
    main.render(
        list(result["diseases"]),
        DISEASE_HEADERS,
        json_override=json_,
        empty="(keine passende Krankheit)",
    )

    if not as_json:
        typer.echo("\n# Kandidatengene")
    main.render(
        list(result["genes"]),
        GENE_HEADERS,
        json_override=json_,
        empty="(kein Kandidatengen)",
    )

    if result["literature"]:
        if not as_json:
            typer.echo("\n# Literatur (Top-Kandidat)")
        main.render(
            list(result["literature"]),
            literature.PUBMED_HEADERS,
            json_override=json_,
            empty="(keine Treffer)",
        )


@compound_app.command("phenotype-workup")
def phenotype_workup(
    hpo: list[str] = typer.Argument(
        ..., help="HPO-IDs, z. B. HP:0001250 HP:0001263."
    ),
    limit: int = typer.Option(
        DEFAULT_LIMIT, "--limit", "-n", help="Maximale Anzahl je Kandidatenliste."
    ),
    with_literature: bool = typer.Option(
        True,
        "--with-literature/--no-literature",
        help="Zusätzlich PubMed zum Top-Kandidaten durchsuchen.",
    ),
    json_: bool = typer.Option(False, "--json", help="Ausgabe als JSON-Lines."),
) -> None:
    """Volle Phänotyp-Abklärung: DDx + Graph + Literatur, dedupliziert & gerankt."""
    with HttpClient() as client:
        conn = history.connect(history.default_db_path())
        try:
            result = run_phenotype_workup(
                client,
                conn,
                hpo_ids=hpo,
                limit=limit,
                with_literature=with_literature,
            )
        except ValueError as exc:
            typer.echo(f"Fehler: {exc}", err=True)
            raise typer.Exit(code=2) from exc
    _render_workup(result, json_=json_)
