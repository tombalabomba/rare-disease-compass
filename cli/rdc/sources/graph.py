"""Krankheits-Graph-Quelle: Monarch Initiative (v3) + Orphanet/Orphadata.

Eine Typer-Subkommando-Gruppe je Quelle, die sich über die Registry aus CLI-01
in ``rdc`` einhängt:

- ``rdc monarch diseases-by-phenotypes <HPO...>`` — leitet aus einer **Liste von
  HPO-IDs** die am besten passenden Krankheiten ab (MONDO/OMIM/ORPHA-IDs + Name,
  Score = Zahl der getroffenen Phänotypen).
- ``rdc monarch gene-to-diseases <gene>`` — liefert die zu einem Gen
  (Symbol oder CURIE) assoziierten Krankheiten aus dem Monarch-Graphen.
- ``rdc orphanet lookup <term-or-id>`` — schlägt einen Orphanet-Eintrag nach
  (ORPHA-Code oder Suchbegriff) und liefert Name, ORPHA-Code, OMIM/Querverweise.

Aufbau-Disziplin:

- **Kein eigener HTTP-Stack.** Aller Netzwerkverkehr läuft über den zentralen
  :class:`~rdc.http_client.HttpClient` (Cache, Rate-Limit, Retry, User-Agent).
- **Reine Funktionen** bilden Query-Params (``*_params``, ``serialize_hpo_terms``)
  und parsen Responses (``parse_*``) — beide ohne HTTP-Call, damit Tests sie
  ohne Netzwerk prüfen.
- **Defensiv lesen.** Die Monarch-Association- und Orphadata-Responses haben sich
  über Versionen geändt; fehlende Schlüssel führen nie zum Crash.
- **Quellen-IDs ausgeben** (MONDO/OMIM/ORPHA) — die klinische Einordnung bleibt
  beim Menschen.

Monarch v3 und der Orphadata-``rd-cross-referencing``-Pfad sind ohne Auth nutzbar.
Ein optionaler ``ORPHANET_API_KEY`` (Env) wird nur als Query-Param angehängt —
**nie** geloggt oder in der History gespeichert.
"""

from __future__ import annotations

import os
import sqlite3
from collections.abc import Iterable
from typing import Any

import typer

from .. import history
from ..http_client import HttpClient

# -- Endpunkte ------------------------------------------------------------

# Monarch v3 REST (BioLink-Assoziationen + Entitäts-Suche), keine Auth.
MONARCH_ASSOCIATION_URL = "https://api-v3.monarchinitiative.org/v3/api/association"
MONARCH_SEARCH_URL = "https://api-v3.monarchinitiative.org/v3/api/search"

# Assoziations-Kategorien im BioLink-Vokabular.
DISEASE_PHENOTYPE_CATEGORY = "biolink:DiseaseToPhenotypicFeatureAssociation"
GENE_DISEASE_CATEGORY = "biolink:CausalGeneToDiseaseAssociation"
GENE_CATEGORY = "biolink:Gene"

# Orphadata REST (frei zugänglicher rd-cross-referencing-Pfad), keine Auth.
ORPHANET_CODE_URL = "https://api.orphadata.com/rd-cross-referencing/orphacodes"
ORPHANET_NAME_URL = "https://api.orphadata.com/rd-cross-referencing/orphacodes/names"
ORPHANET_API_KEY_ENV = "ORPHANET_API_KEY"

# Definierter Leerwert für fehlende Felder (statt None/Crash).
EMPTY = ""

# Default-Zahl ausgegebener Krankheiten/Treffer.
DEFAULT_LIMIT = 20
# Wie viele Assoziations-Zeilen für die Phänotyp-Aggregation geholt werden.
# Höher als DEFAULT_LIMIT, weil pro Krankheit mehrere Phänotyp-Zeilen kommen.
ASSOCIATION_FETCH_LIMIT = 500

DISEASES_HEADERS = ["id", "name", "score", "matched"]
GENE_DISEASE_HEADERS = ["gene", "disease_id", "disease", "predicate"]
ORPHANET_HEADERS = ["orpha", "name", "omim", "xrefs"]


# -- HPO-Serialisierung + Query-Param-Bildung (reine Funktionen, ohne HTTP) -


def serialize_hpo_terms(hpo_ids: Iterable[str]) -> list[str]:
    """Bringt HPO-IDs in das Query-Format für wiederholte Params.

    Die Monarch-Association-API erwartet die Phänotypen als wiederholte
    ``object``-Query-Params (``object=HP:..&object=HP:..``); ``httpx`` erzeugt
    genau das aus einem Listen-Wert. Diese Funktion trimmt Whitespace, verwirft
    Leerstrings und dedupliziert ordnungserhaltend. Die IDs selbst bleiben
    unverändert (``HP:0000000`` bleibt ``HP:0000000``) — Validierung ist
    bewusst nicht hier (Single source of truth liegt in CLI-05).
    """
    serialized: list[str] = []
    for raw in hpo_ids:
        token = (raw or "").strip()
        if token and token not in serialized:
            serialized.append(token)
    return serialized


def diseases_by_phenotypes_params(
    hpo_ids: Iterable[str],
    *,
    limit: int = ASSOCIATION_FETCH_LIMIT,
    category: str = DISEASE_PHENOTYPE_CATEGORY,
) -> dict[str, object]:
    """Params für die Phänotyp→Krankheit-Abfrage (Association-Endpunkt)."""
    return {
        "object": serialize_hpo_terms(hpo_ids),
        "category": category,
        "limit": limit,
    }


def gene_diseases_params(
    gene: str,
    *,
    limit: int = DEFAULT_LIMIT,
    category: str = GENE_DISEASE_CATEGORY,
) -> dict[str, object]:
    """Params für die Gen→Krankheit-Abfrage (Association-Endpunkt)."""
    return {"subject": gene.strip(), "category": category, "limit": limit}


def gene_search_params(gene: str, *, limit: int = 1) -> dict[str, object]:
    """Params für die Auflösung eines Gen-Symbols zu einer CURIE (Search)."""
    return {"q": gene.strip(), "category": GENE_CATEGORY, "limit": limit}


def is_curie(token: str) -> bool:
    """Ob ``token`` bereits eine CURIE ist (z. B. ``HGNC:3603``)."""
    return ":" in token.strip()


def orpha_code_of(term: str) -> str | None:
    """Liefert den numerischen ORPHA-Code, falls ``term`` einer ist, sonst ``None``.

    Akzeptiert ``558``, ``ORPHA:558`` und ``ORPHAcode:558``; alles andere
    (z. B. ``Marfan syndrome``) gilt als Suchbegriff → ``None``.
    """
    token = term.strip()
    upper = token.upper()
    for prefix in ("ORPHACODE:", "ORPHANET:", "ORPHA:", "ORPHA"):
        if upper.startswith(prefix):
            token = token[len(prefix):].lstrip(":")
            break
    return token if token.isdigit() else None


def orphanet_code_url(code: str) -> str:
    """URL für die Suche per ORPHA-Code."""
    return f"{ORPHANET_CODE_URL}/{code}"


def orphanet_name_url(name: str) -> str:
    """URL für die Suche per Krankheitsname."""
    return f"{ORPHANET_NAME_URL}/{name.strip()}"


def orphanet_params(
    lang: str = "en",
    api_key: str | None = None,
) -> dict[str, object]:
    """Params für eine Orphadata-Abfrage (Sprache + optionaler Key)."""
    params: dict[str, object] = {"lang": lang}
    if api_key:
        params["api_key"] = api_key
    return params


# -- Response-Parsing (reine Funktionen, ohne HTTP) -----------------------


def _as_list(value: object) -> list[Any]:
    """Normalisiert ein Feld, das einzeln **oder** als Liste kommen kann."""
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _items(data: object) -> list[dict[str, Any]]:
    """Holt die ``items``-Liste aus einer Monarch-Association/Search-Response."""
    if not isinstance(data, dict):
        return []
    items = data.get("items")
    if not isinstance(items, list):
        return []
    return [item for item in items if isinstance(item, dict)]


def first_search_id(data: object) -> str:
    """Erste Entitäts-ID aus einer Monarch-Search-Response (sonst Leerwert)."""
    for item in _items(data):
        entity_id = item.get("id")
        if entity_id:
            return str(entity_id)
    return EMPTY


def parse_disease_matches(
    data: object,
    queried: Iterable[str] | None = None,
) -> list[dict[str, object]]:
    """Aggregiert Phänotyp→Krankheit-Assoziationen zu Krankheits-Records.

    Pro Zeile liefert die API ein (Krankheit, Phänotyp)-Paar. Hier werden die
    Zeilen je Krankheit (``subject``) zusammengefasst; der Score ist die Zahl
    der getroffenen — auf Wunsch auf ``queried`` beschränkten — Phänotypen.
    Sortiert nach Score absteigend, dann Name, dann ID.
    """
    allowed = set(serialize_hpo_terms(queried)) if queried is not None else None
    aggregate: dict[str, dict[str, Any]] = {}
    for item in _items(data):
        disease_id = item.get("subject")
        if not disease_id:
            continue
        key = str(disease_id)
        record = aggregate.setdefault(
            key, {"id": key, "name": EMPTY, "matched": set()}
        )
        if not record["name"] and item.get("subject_label"):
            record["name"] = str(item["subject_label"])
        phenotype = item.get("object")
        if not phenotype:
            continue
        phenotype = str(phenotype)
        if allowed is None or phenotype in allowed:
            record["matched"].add(phenotype)

    records = [
        {
            "id": record["id"],
            "name": record["name"],
            "score": len(record["matched"]),
            "matched": "; ".join(sorted(record["matched"])),
        }
        for record in aggregate.values()
    ]
    records.sort(key=lambda r: (-int(r["score"]), str(r["name"]), str(r["id"])))
    return records


def parse_gene_diseases(data: object) -> list[dict[str, object]]:
    """Gen→Krankheit-Records aus einer Monarch-Association-Response."""
    records: list[dict[str, object]] = []
    for item in _items(data):
        disease_id = item.get("object")
        if not disease_id:
            continue
        gene = item.get("subject_label") or item.get("subject")
        records.append(
            {
                "gene": str(gene) if gene else EMPTY,
                "disease_id": str(disease_id),
                "disease": str(item.get("object_label") or EMPTY),
                "predicate": str(item.get("predicate") or EMPTY),
            }
        )
    return records


def orphanet_results(data: object) -> dict[str, Any]:
    """Holt das Disorder-Objekt aus ``data.results`` (Einzel-Objekt **oder** Liste)."""
    if not isinstance(data, dict):
        return {}
    payload = data.get("data")
    payload = payload if isinstance(payload, dict) else {}
    results = payload.get("results")
    if isinstance(results, list):
        first = results[0] if results else {}
        return first if isinstance(first, dict) else {}
    return results if isinstance(results, dict) else {}


def parse_orphanet(data: object) -> dict[str, object]:
    """Orphanet-Eintrag: ORPHA-Code, Name, OMIM-Querverweise, alle Cross-Refs."""
    results = orphanet_results(data)
    omim: list[str] = []
    xrefs: list[str] = []
    for ref in _as_list(results.get("ExternalReference")):
        if not isinstance(ref, dict):
            continue
        source = ref.get("Source")
        reference = ref.get("Reference")
        if not (source and reference):
            continue
        pair = f"{source}:{reference}"
        if pair not in xrefs:
            xrefs.append(pair)
        if str(source).upper() == "OMIM":
            omim.append(str(reference))
    code = results.get("ORPHAcode")
    name = results.get("Preferred term")
    return {
        "orpha": str(code) if code is not None else EMPTY,
        "name": str(name) if name else EMPTY,
        "omim": "; ".join(omim),
        "xrefs": "; ".join(xrefs),
    }


# -- Kernlogik (Client + Connection injiziert) ----------------------------


def resolve_gene(client: HttpClient, gene: str) -> str:
    """Liefert eine Gen-CURIE — direkt bei CURIE-Eingabe, sonst über die Suche."""
    token = gene.strip()
    if is_curie(token):
        return token
    response = client.get(MONARCH_SEARCH_URL, params=gene_search_params(token))
    return first_search_id(response.json()) or token


def run_diseases_by_phenotypes(
    client: HttpClient,
    conn: sqlite3.Connection,
    *,
    hpo_ids: Iterable[str],
    limit: int = DEFAULT_LIMIT,
    fetch_limit: int = ASSOCIATION_FETCH_LIMIT,
) -> list[dict[str, object]]:
    """Phänotyp-Profil → Kandidaten-Krankheiten und protokolliert die Abfrage."""
    serialized = serialize_hpo_terms(hpo_ids)
    response = client.get(
        MONARCH_ASSOCIATION_URL,
        params=diseases_by_phenotypes_params(serialized, limit=fetch_limit),
    )
    records = parse_disease_matches(response.json(), serialized)[:limit]
    top = records[0]["name"] if records else "kein Treffer"
    history.save_query(
        conn,
        source="monarch",
        command="diseases-by-phenotypes",
        params={"hpo": serialized, "limit": limit},
        result_summary=f"{len(records)} Krankheiten für "
        f"{len(serialized)} Phänotyp(en); Top: {top}",
        result_count=len(records),
        raw=records,
    )
    return records


def run_gene_to_diseases(
    client: HttpClient,
    conn: sqlite3.Connection,
    *,
    gene: str,
    limit: int = DEFAULT_LIMIT,
) -> list[dict[str, object]]:
    """Gen → assoziierte Krankheiten und protokolliert die Abfrage."""
    resolved = resolve_gene(client, gene)
    response = client.get(
        MONARCH_ASSOCIATION_URL, params=gene_diseases_params(resolved, limit=limit)
    )
    records = parse_gene_diseases(response.json())
    history.save_query(
        conn,
        source="monarch",
        command="gene-to-diseases",
        params={"gene": gene, "resolved": resolved, "limit": limit},
        result_summary=f"{len(records)} Krankheiten für Gen {gene} ({resolved})",
        result_count=len(records),
        raw=records,
    )
    return records


def run_orphanet_lookup(
    client: HttpClient,
    conn: sqlite3.Connection,
    *,
    term: str,
    lang: str = "en",
    api_key: str | None = None,
) -> list[dict[str, object]]:
    """Orphanet-Eintrag per ORPHA-Code oder Name und protokolliert die Abfrage."""
    code = orpha_code_of(term)
    if code is not None:
        url = orphanet_code_url(code)
    else:
        url = orphanet_name_url(term)
    response = client.get(url, params=orphanet_params(lang, api_key))
    record = parse_orphanet(response.json())
    summary = record["name"] or "kein Orphanet-Eintrag"
    history.save_query(
        conn,
        source="orphanet",
        command="lookup",
        params={"term": term, "lang": lang},
        result_summary=f"ORPHA {record['orpha'] or '—'}: {summary}",
        result_count=1 if record["orpha"] or record["name"] else 0,
        raw=record,
    )
    return [record]


def _api_key() -> str | None:
    return os.environ.get(ORPHANET_API_KEY_ENV) or None


# -- Typer-Befehle (verdrahten Client/History und rendern) ----------------

monarch_app = typer.Typer(
    help="Monarch Initiative: Phänotyp→Krankheit und Gen→Krankheit (Graph).",
    no_args_is_help=True,
)
orphanet_app = typer.Typer(
    help="Orphanet/Orphadata: Eintrag per ORPHA-Code oder Name nachschlagen.",
    no_args_is_help=True,
)


@monarch_app.command("diseases-by-phenotypes")
def diseases_by_phenotypes(
    hpo: list[str] = typer.Argument(
        ..., help="HPO-IDs, z. B. HP:0001250 HP:0001263."
    ),
    limit: int = typer.Option(
        DEFAULT_LIMIT, "--limit", "-n", help="Maximale Anzahl Krankheiten."
    ),
    json_: bool = typer.Option(False, "--json", help="Ausgabe als JSON-Lines."),
) -> None:
    """Kandidaten-Krankheiten zu einem Phänotyp-Profil (HPO-Liste)."""
    from rdc import main

    with HttpClient() as client:
        conn = history.connect(history.default_db_path())
        records = run_diseases_by_phenotypes(client, conn, hpo_ids=hpo, limit=limit)
    main.render(
        records,
        DISEASES_HEADERS,
        json_override=json_,
        empty="(keine passende Krankheit)",
    )


@monarch_app.command("gene-to-diseases")
def gene_to_diseases(
    gene: str = typer.Argument(
        ..., help="Gen als Symbol (FBN1) oder CURIE (HGNC:3603)."
    ),
    limit: int = typer.Option(
        DEFAULT_LIMIT, "--limit", "-n", help="Maximale Anzahl Krankheiten."
    ),
    json_: bool = typer.Option(False, "--json", help="Ausgabe als JSON-Lines."),
) -> None:
    """Assoziierte Krankheiten zu einem Gen aus dem Monarch-Graphen."""
    from rdc import main

    with HttpClient() as client:
        conn = history.connect(history.default_db_path())
        records = run_gene_to_diseases(client, conn, gene=gene, limit=limit)
    main.render(
        records,
        GENE_DISEASE_HEADERS,
        json_override=json_,
        empty="(keine assoziierte Krankheit)",
    )


@orphanet_app.command("lookup")
def orphanet_lookup(
    term: str = typer.Argument(
        ..., help="ORPHA-Code (558 / ORPHA:558) oder Suchbegriff (Marfan syndrome)."
    ),
    lang: str = typer.Option("en", "--lang", help="Sprachcode der Orphadata-Antwort."),
    json_: bool = typer.Option(False, "--json", help="Ausgabe als JSON-Lines."),
) -> None:
    """Orphanet-Eintrag: Name, ORPHA-Code, OMIM- und weitere Querverweise."""
    from rdc import main

    with HttpClient() as client:
        conn = history.connect(history.default_db_path())
        records = run_orphanet_lookup(
            client, conn, term=term, lang=lang, api_key=_api_key()
        )
    main.render(
        records,
        ORPHANET_HEADERS,
        json_override=json_,
        empty="(kein Orphanet-Eintrag)",
    )
