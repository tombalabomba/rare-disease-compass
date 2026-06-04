"""Differentialdiagnose-Quelle: PubCaseFinder + Phen2Gene.

Zwei Typer-Subkommando-Gruppen, die sich über die Registry aus CLI-01 in
``rdc`` einhängen — der phänotyp-getriebene DDx-Kern:

- ``rdc pubcasefinder rank <HPO...>`` — schickt eine **Liste von HPO-IDs** an die
  PubCaseFinder-REST-API und liefert eine **gerankte Liste seltener Krankheiten**
  (Krankheit + OMIM/ORPHA-ID + Score/Rang).
- ``rdc phen2gene genes <HPO...>`` — schickt die HPO-Liste an die Phen2Gene-API und
  liefert **gerankte Kandidatengene** (Gen-Symbol + Score/Rang).

Aufbau-Disziplin:

- **HPO-Validierung als Single source of truth.** :func:`validate_hpo_terms` ist
  die **eine** reine Funktion, die das ``HP:nnnnnnn``-Format prüft. CLI-04 (Graph)
  serialisiert HPO-IDs nur, validiert sie bewusst nicht — die Validierung lebt
  hier. Ungültige Eingaben werden **vor** jedem HTTP-Call abgelehnt; es geht kein
  Müll an die APIs.
- **Kein eigener HTTP-Stack.** Aller Netzwerkverkehr läuft über den zentralen
  :class:`~rdc.http_client.HttpClient` (Cache, Rate-Limit, Retry, User-Agent).
- **Reine Funktionen** bilden Query-Params (``*_params``) und parsen Responses
  (``parse_*``) — beide ohne HTTP-Call, damit Tests sie ohne Netzwerk prüfen.
- **Defensiv lesen.** Beide APIs liefern leicht abweichende Feldnamen je nach
  Version; fehlende Schlüssel führen nie zum Crash, sondern zum Leerwert.
- **Kein Diagnose-Anspruch.** Ausgegeben werden nur Daten + Quellen-IDs und die
  von der API vorgegebene Reihenfolge; die klinische Einordnung bleibt beim
  Menschen.

PubCaseFinder und Phen2Gene sind ohne Auth über REST nutzbar — kein Secret nötig.
"""

from __future__ import annotations

import re
import sqlite3
from collections.abc import Iterable
from typing import Any

import typer

from .. import history
from ..http_client import HttpClient

# -- Endpunkte ------------------------------------------------------------

# PubCaseFinder: gerankte Krankheitsliste aus HPO-Profil (keine Auth).
PUBCASEFINDER_URL = "https://pubcasefinder.dbcls.jp/api/pcf_get_ranked_list"
# Ziel-Vokabular der Krankheits-IDs (OMIM-basiertes Ranking).
PUBCASEFINDER_TARGET = "omim"

# Phen2Gene: gerankte Kandidatengene aus HPO-Profil (keine Auth).
PHEN2GENE_URL = "https://phen2gene.wglab.org/api"

# Definierter Leerwert für fehlende Felder (statt None/Crash).
EMPTY = ""

# Default-Zahl ausgegebener Krankheiten/Gene.
DEFAULT_LIMIT = 20

# Offizielle HPO-ID-Form: Präfix ``HP:`` + sieben Ziffern.
HPO_PATTERN = re.compile(r"^HP:\d{7}$")

PUBCASEFINDER_HEADERS = ["rank", "id", "disease", "score"]
PHEN2GENE_HEADERS = ["rank", "gene", "gene_id", "score"]


# -- HPO-Validierung (reine Funktion, Single source of truth) -------------


def is_valid_hpo(term: str) -> bool:
    """Ob ``term`` eine wohlgeformte HPO-ID ist (``HP:nnnnnnn``)."""
    return bool(HPO_PATTERN.fullmatch((term or "").strip()))


def validate_hpo_terms(hpo_ids: Iterable[str]) -> list[str]:
    """Validiert und normalisiert eine HPO-Liste; lehnt Müll ab.

    Akzeptiert ausschließlich das Format ``HP:nnnnnnn``. Whitespace wird
    getrimmt, Duplikate ordnungserhaltend entfernt. **Jede** ungültige oder
    leere Eingabe (z. B. ``HP:123``, ``0001250``, ``foo``, ``""``) führt zu
    einem :class:`ValueError` mit klarer Meldung — bewusst **bevor** ein
    HTTP-Call gebaut wird, damit nie Müll an die APIs geht.
    """
    raw = list(hpo_ids)
    if not raw:
        raise ValueError("Keine HPO-IDs angegeben (erwartet: HP:nnnnnnn).")
    normalized: list[str] = []
    invalid: list[str] = []
    for term in raw:
        token = (term or "").strip()
        if not HPO_PATTERN.fullmatch(token):
            invalid.append(token if token else "(leer)")
            continue
        if token not in normalized:
            normalized.append(token)
    if invalid:
        raise ValueError(
            "Ungültige HPO-ID(s): "
            + ", ".join(invalid)
            + ". Erwartetes Format: HP:nnnnnnn (z. B. HP:0001250)."
        )
    return normalized


# -- Query-Param-Bildung (reine Funktionen, ohne HTTP) --------------------


def pubcasefinder_params(
    hpo_ids: Iterable[str],
    *,
    target: str = PUBCASEFINDER_TARGET,
) -> dict[str, object]:
    """Params für die PubCaseFinder-Rangliste (HPO-Liste komma-separiert)."""
    return {
        "target": target,
        "format": "json",
        "hpo_id": ",".join(hpo_ids),
    }


def phen2gene_params(hpo_ids: Iterable[str]) -> dict[str, object]:
    """Params für Phen2Gene (HPO-Liste semikolon-separiert)."""
    return {"HPO_list": ";".join(hpo_ids)}


# -- Response-Parsing (reine Funktionen, ohne HTTP) -----------------------


def _items(data: object, key: str) -> list[dict[str, Any]]:
    """Holt die Ergebnisliste — direkt als Liste **oder** unter ``key``."""
    if isinstance(data, list):
        candidate = data
    elif isinstance(data, dict):
        candidate = data.get(key)
    else:
        candidate = None
    if not isinstance(candidate, list):
        return []
    return [item for item in candidate if isinstance(item, dict)]


def _first(item: dict[str, Any], keys: tuple[str, ...]) -> str:
    """Erster nicht-leerer Wert unter ``keys`` (sonst Leerwert)."""
    for key in keys:
        value = item.get(key)
        if value not in (None, ""):
            return str(value)
    return EMPTY


def _rank(item: dict[str, Any], index: int) -> int:
    """Rang aus der Response oder — fehlt er — die API-Position (1-basiert)."""
    for key in ("rank", "Rank"):
        value = item.get(key)
        try:
            return int(value)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            continue
    return index + 1


def parse_pubcasefinder(
    data: object,
    *,
    limit: int | None = None,
) -> list[dict[str, object]]:
    """Gerankte Krankheits-Records aus einer PubCaseFinder-Response.

    Behält die API-Reihenfolge (gerankt) bei; ``limit`` schneidet ab. Der
    Score wird nur durchgereicht, wenn vorhanden.
    """
    records: list[dict[str, object]] = []
    for index, item in enumerate(_items(data, "results")):
        disease_id = _first(item, ("id", "disease_id", "omim_id", "orphanet_id"))
        name = _first(
            item,
            (
                "omim_disease_name_en",
                "orphanet_disease_name_en",
                "disease_name_en",
                "disease_name",
                "name",
                "label",
            ),
        )
        records.append(
            {
                "rank": _rank(item, index),
                "id": disease_id,
                "disease": name,
                "score": item.get("score", EMPTY),
            }
        )
    if limit is not None:
        records = records[:limit]
    return records


def parse_phen2gene(
    data: object,
    *,
    limit: int | None = None,
) -> list[dict[str, object]]:
    """Gerankte Gen-Records aus einer Phen2Gene-Response.

    Behält die API-Reihenfolge (gerankt) bei; ``limit`` schneidet ab. Der
    Score wird nur durchgereicht, wenn vorhanden.
    """
    records: list[dict[str, object]] = []
    for index, item in enumerate(_items(data, "results")):
        gene = _first(item, ("Gene", "gene", "Gene Symbol", "symbol"))
        if not gene:
            continue
        gene_id = _first(item, ("Gene ID", "ID", "id", "gene_id"))
        records.append(
            {
                "rank": _rank(item, index),
                "gene": gene,
                "gene_id": gene_id,
                "score": item.get("Score", item.get("score", EMPTY)),
            }
        )
    if limit is not None:
        records = records[:limit]
    return records


# -- Kernlogik (Client + Connection injiziert) ----------------------------


def run_pubcasefinder_rank(
    client: HttpClient,
    conn: sqlite3.Connection,
    *,
    hpo_ids: Iterable[str],
    target: str = PUBCASEFINDER_TARGET,
    limit: int = DEFAULT_LIMIT,
) -> list[dict[str, object]]:
    """HPO-Profil → gerankte Krankheiten und protokolliert die Abfrage.

    :func:`validate_hpo_terms` läuft **zuerst**; bei ungültiger Eingabe wird
    ein :class:`ValueError` geworfen, bevor ``client`` überhaupt angefasst wird.
    """
    terms = validate_hpo_terms(hpo_ids)
    response = client.get(
        PUBCASEFINDER_URL, params=pubcasefinder_params(terms, target=target)
    )
    records = parse_pubcasefinder(response.json(), limit=limit)
    top = (records[0]["disease"] or records[0]["id"]) if records else "kein Treffer"
    history.save_query(
        conn,
        source="pubcasefinder",
        command="rank",
        params={"hpo": terms, "target": target, "limit": limit},
        result_summary=f"{len(records)} Krankheiten für "
        f"{len(terms)} Phänotyp(en); Top: {top}",
        result_count=len(records),
        raw=records,
    )
    return records


def run_phen2gene_genes(
    client: HttpClient,
    conn: sqlite3.Connection,
    *,
    hpo_ids: Iterable[str],
    limit: int = DEFAULT_LIMIT,
) -> list[dict[str, object]]:
    """HPO-Profil → gerankte Kandidatengene und protokolliert die Abfrage.

    :func:`validate_hpo_terms` läuft **zuerst**; bei ungültiger Eingabe wird
    ein :class:`ValueError` geworfen, bevor ``client`` überhaupt angefasst wird.
    """
    terms = validate_hpo_terms(hpo_ids)
    response = client.get(PHEN2GENE_URL, params=phen2gene_params(terms))
    records = parse_phen2gene(response.json(), limit=limit)
    top = records[0]["gene"] if records else "kein Treffer"
    history.save_query(
        conn,
        source="phen2gene",
        command="genes",
        params={"hpo": terms, "limit": limit},
        result_summary=f"{len(records)} Kandidatengene für "
        f"{len(terms)} Phänotyp(en); Top: {top}",
        result_count=len(records),
        raw=records,
    )
    return records


# -- Typer-Befehle (verdrahten Client/History und rendern) ----------------

pubcasefinder_app = typer.Typer(
    help="PubCaseFinder: gerankte seltene Krankheiten zu einem HPO-Profil.",
    no_args_is_help=True,
)
phen2gene_app = typer.Typer(
    help="Phen2Gene: gerankte Kandidatengene zu einem HPO-Profil.",
    no_args_is_help=True,
)


@pubcasefinder_app.command("rank")
def pubcasefinder_rank(
    hpo: list[str] = typer.Argument(
        ..., help="HPO-IDs, z. B. HP:0001250 HP:0001263."
    ),
    limit: int = typer.Option(
        DEFAULT_LIMIT, "--limit", "-n", help="Maximale Anzahl Krankheiten."
    ),
    json_: bool = typer.Option(False, "--json", help="Ausgabe als JSON-Lines."),
) -> None:
    """Gerankte Kandidaten-Krankheiten zu einem Phänotyp-Profil (HPO-Liste)."""
    from rdc import main

    with HttpClient() as client:
        conn = history.connect(history.default_db_path())
        try:
            records = run_pubcasefinder_rank(client, conn, hpo_ids=hpo, limit=limit)
        except ValueError as exc:
            typer.echo(f"Fehler: {exc}", err=True)
            raise typer.Exit(code=2) from exc
    main.render(
        records,
        PUBCASEFINDER_HEADERS,
        json_override=json_,
        empty="(keine passende Krankheit)",
    )


@phen2gene_app.command("genes")
def phen2gene_genes(
    hpo: list[str] = typer.Argument(
        ..., help="HPO-IDs, z. B. HP:0001250 HP:0001263."
    ),
    limit: int = typer.Option(
        DEFAULT_LIMIT, "--limit", "-n", help="Maximale Anzahl Gene."
    ),
    json_: bool = typer.Option(False, "--json", help="Ausgabe als JSON-Lines."),
) -> None:
    """Gerankte Kandidatengene zu einem Phänotyp-Profil (HPO-Liste)."""
    from rdc import main

    with HttpClient() as client:
        conn = history.connect(history.default_db_path())
        try:
            records = run_phen2gene_genes(client, conn, hpo_ids=hpo, limit=limit)
        except ValueError as exc:
            typer.echo(f"Fehler: {exc}", err=True)
            raise typer.Exit(code=2) from exc
    main.render(
        records,
        PHEN2GENE_HEADERS,
        json_override=json_,
        empty="(kein Kandidatengen)",
    )
