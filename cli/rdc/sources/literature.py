"""Literatur-Quelle: PubMed (NCBI E-utilities) und Europe PMC.

Zwei Typer-Subkommando-Gruppen, die sich über die Registry aus CLI-01 in ``rdc``
einhängen:

- ``rdc pubmed search <query>`` / ``rdc pubmed fetch <pmid...>``
- ``rdc europepmc search <query>``

Aufbau-Disziplin:

- **Kein eigener HTTP-Stack.** Aller Netzwerkverkehr läuft über den zentralen
  :class:`~rdc.http_client.HttpClient` (Cache, Rate-Limit, Retry, User-Agent).
- **Reine Funktionen** bilden Query-Params (``*_params``) und parsen Responses
  (``parse_*``) — beide ohne HTTP-Call, damit Tests sie ohne Netzwerk prüfen.
- **Dependency-Injection:** die ``run_*``-Kernfunktionen bekommen Client und
  History-Connection übergeben; Tests speisen einen ``MockTransport``-Client und
  eine in-memory-History ein, die Typer-Befehle verdrahten die echten.
- **Jede Suche/jeder Fetch** schreibt einen History-Eintrag (auch bei 0 Treffern).

NCBI-Etikette: der optionale ``NCBI_API_KEY`` (Env) wird nur als Query-Param
angehängt — **nie** geloggt oder in der History gespeichert.
"""

from __future__ import annotations

import os
import sqlite3
from xml.etree import ElementTree as ET

import typer

from .. import history
from ..http_client import HttpClient

NCBI_API_KEY_ENV = "NCBI_API_KEY"

# E-utilities-Endpunkte (NCBI Entrez).
ESEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
ESUMMARY_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
EFETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

# Europe-PMC-REST-Suche.
EUROPEPMC_SEARCH_URL = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"

# Höfliche Tool-Identifikation gegenüber NCBI (kein Secret).
EUTILS_TOOL = "raredisease-compass"

PUBMED_HEADERS = ["pmid", "year", "authors", "journal", "title", "doi"]
EUROPEPMC_HEADERS = ["pmid", "pmcid", "doi", "year", "source", "title"]


# -- Query-Param-Bildung (reine Funktionen, ohne HTTP) --------------------


def pubmed_search_params(
    term: str,
    retmax: int = 20,
    api_key: str | None = None,
) -> dict[str, object]:
    """E-utilities-``esearch``-Params für eine PubMed-Suche."""
    params: dict[str, object] = {
        "db": "pubmed",
        "term": term,
        "retmode": "json",
        "retmax": retmax,
        "tool": EUTILS_TOOL,
    }
    if api_key:
        params["api_key"] = api_key
    return params


def pubmed_summary_params(
    pmids: list[str],
    api_key: str | None = None,
) -> dict[str, object]:
    """E-utilities-``esummary``-Params für eine Menge PMIDs."""
    params: dict[str, object] = {
        "db": "pubmed",
        "id": ",".join(pmids),
        "retmode": "json",
        "tool": EUTILS_TOOL,
    }
    if api_key:
        params["api_key"] = api_key
    return params


def pubmed_fetch_params(
    pmids: list[str],
    api_key: str | None = None,
) -> dict[str, object]:
    """E-utilities-``efetch``-Params (XML, Abstracts) für eine Menge PMIDs."""
    params: dict[str, object] = {
        "db": "pubmed",
        "id": ",".join(pmids),
        "retmode": "xml",
        "rettype": "abstract",
        "tool": EUTILS_TOOL,
    }
    if api_key:
        params["api_key"] = api_key
    return params


def europepmc_search_params(
    query: str,
    page_size: int = 25,
) -> dict[str, object]:
    """Europe-PMC-``/search``-Params (Core-Result-Type, JSON)."""
    return {
        "query": query,
        "format": "json",
        "pageSize": page_size,
        "resultType": "core",
    }


# -- Response-Parsing (reine Funktionen, ohne HTTP) -----------------------


def parse_esearch(data: dict[str, object]) -> dict[str, object]:
    """``esearch``-JSON → ``{"pmids": [...], "total": int}``."""
    result = data.get("esearchresult", {}) if isinstance(data, dict) else {}
    result = result if isinstance(result, dict) else {}
    idlist = result.get("idlist", [])
    pmids = [str(pmid) for pmid in idlist] if isinstance(idlist, list) else []
    try:
        total = int(result.get("count", len(pmids)))
    except (TypeError, ValueError):
        total = len(pmids)
    return {"pmids": pmids, "total": total}


def parse_esummary(data: dict[str, object]) -> list[dict[str, str]]:
    """``esummary``-JSON → schlanke Records (PMID, Titel, Autoren, Jahr, …)."""
    result = data.get("result", {}) if isinstance(data, dict) else {}
    result = result if isinstance(result, dict) else {}
    uids = result.get("uids", [])
    records: list[dict[str, str]] = []
    for uid in uids if isinstance(uids, list) else []:
        item = result.get(str(uid), {})
        item = item if isinstance(item, dict) else {}
        authors = item.get("authors", [])
        names = [
            a.get("name", "")
            for a in authors
            if isinstance(a, dict)
        ] if isinstance(authors, list) else []
        records.append(
            {
                "pmid": str(uid),
                "title": str(item.get("title", "")),
                "authors": ", ".join(n for n in names if n),
                "year": _year_from_pubdate(item.get("pubdate", "")),
                "journal": str(item.get("source", "")),
                "doi": _doi_from_articleids(item.get("articleids", [])),
            }
        )
    return records


def parse_efetch_abstracts(xml_text: str) -> dict[str, str]:
    """``efetch``-XML → ``{pmid: abstract}``.

    Quelle ist der vertrauenswürdige NCBI-E-utilities-Endpunkt (HTTPS über den
    zentralen Client); ``ElementTree`` löst keine externen Entities auf.
    """
    abstracts: dict[str, str] = {}
    root = ET.fromstring(xml_text)
    for article in root.findall(".//PubmedArticle"):
        pmid = article.findtext(".//MedlineCitation/PMID") or ""
        parts: list[str] = []
        for node in article.findall(".//Abstract/AbstractText"):
            text = "".join(node.itertext()).strip()
            if not text:
                continue
            label = node.get("Label")
            parts.append(f"{label}: {text}" if label else text)
        if pmid:
            abstracts[pmid.strip()] = "\n".join(parts)
    return abstracts


def parse_europepmc(data: dict[str, object]) -> dict[str, object]:
    """Europe-PMC-Such-JSON → ``{"total": int, "records": [...]}``."""
    result_list = data.get("resultList", {}) if isinstance(data, dict) else {}
    result_list = result_list if isinstance(result_list, dict) else {}
    items = result_list.get("result", [])
    records: list[dict[str, str]] = []
    for item in items if isinstance(items, list) else []:
        item = item if isinstance(item, dict) else {}
        records.append(
            {
                "pmid": str(item.get("pmid", "")),
                "pmcid": str(item.get("pmcid", "")),
                "doi": str(item.get("doi", "")),
                "title": str(item.get("title", "")),
                "authors": str(item.get("authorString", "")),
                "year": str(item.get("pubYear", "")),
                "source": str(item.get("source", "")),
                "journal": str(item.get("journalTitle", "")),
                "id": str(item.get("id", "")),
            }
        )
    try:
        total = int(data.get("hitCount", len(records)))
    except (TypeError, ValueError):
        total = len(records)
    return {"total": total, "records": records}


def _year_from_pubdate(pubdate: object) -> str:
    for token in str(pubdate).replace("-", " ").split():
        if len(token) == 4 and token.isdigit():
            return token
    return ""


def _doi_from_articleids(articleids: object) -> str:
    if not isinstance(articleids, list):
        return ""
    for entry in articleids:
        if isinstance(entry, dict) and entry.get("idtype") == "doi":
            return str(entry.get("value", ""))
    return ""


# -- Kernlogik (Client + Connection injiziert) ----------------------------


def _enrich_pubmed(
    client: HttpClient,
    pmids: list[str],
    api_key: str | None,
) -> list[dict[str, str]]:
    if not pmids:
        return []
    response = client.get(ESUMMARY_URL, params=pubmed_summary_params(pmids, api_key))
    return parse_esummary(response.json())


def run_pubmed_search(
    client: HttpClient,
    conn: sqlite3.Connection,
    *,
    term: str,
    retmax: int = 20,
    api_key: str | None = None,
) -> list[dict[str, str]]:
    """Sucht in PubMed (``esearch`` → ``esummary``) und protokolliert die Suche."""
    response = client.get(
        ESEARCH_URL, params=pubmed_search_params(term, retmax, api_key)
    )
    parsed = parse_esearch(response.json())
    pmids = list(parsed["pmids"])  # type: ignore[arg-type]
    records = _enrich_pubmed(client, pmids, api_key)
    if not records:
        records = [{"pmid": pmid} for pmid in pmids]
    history.save_query(
        conn,
        source="pubmed",
        command="search",
        params={"term": term, "retmax": retmax},
        result_summary=f"{len(records)} von {parsed['total']} Treffern",
        result_count=len(records),
        raw=records,
    )
    return records


def run_pubmed_fetch(
    client: HttpClient,
    conn: sqlite3.Connection,
    *,
    pmids: list[str],
    api_key: str | None = None,
) -> list[dict[str, str]]:
    """Holt Detail-Metadaten (``esummary``) + Abstracts (``efetch``) zu PMIDs."""
    summary_by_pmid = {
        record["pmid"]: record for record in _enrich_pubmed(client, pmids, api_key)
    }
    fetch_response = client.get(
        EFETCH_URL, params=pubmed_fetch_params(pmids, api_key)
    )
    abstracts = parse_efetch_abstracts(fetch_response.text)
    records: list[dict[str, str]] = []
    for pmid in pmids:
        record = dict(summary_by_pmid.get(pmid, {"pmid": pmid}))
        record["abstract"] = abstracts.get(pmid, "")
        records.append(record)
    history.save_query(
        conn,
        source="pubmed",
        command="fetch",
        params={"pmids": pmids},
        result_summary=f"{len(records)} Datensätze geholt",
        result_count=len(records),
        raw=records,
    )
    return records


def run_europepmc_search(
    client: HttpClient,
    conn: sqlite3.Connection,
    *,
    query: str,
    page_size: int = 25,
) -> list[dict[str, str]]:
    """Sucht über die Europe-PMC-REST-API und protokolliert die Suche."""
    response = client.get(
        EUROPEPMC_SEARCH_URL, params=europepmc_search_params(query, page_size)
    )
    parsed = parse_europepmc(response.json())
    records: list[dict[str, str]] = parsed["records"]  # type: ignore[assignment]
    history.save_query(
        conn,
        source="europepmc",
        command="search",
        params={"query": query, "page_size": page_size},
        result_summary=f"{len(records)} von {parsed['total']} Treffern",
        result_count=len(records),
        raw=records,
    )
    return records


def _api_key() -> str | None:
    return os.environ.get(NCBI_API_KEY_ENV) or None


# -- Typer-Befehle (verdrahten Client/History und rendern) ----------------

pubmed_app = typer.Typer(
    help="PubMed (NCBI E-utilities): Literatursuche und Detail-Abruf.",
    no_args_is_help=True,
)
europepmc_app = typer.Typer(
    help="Europe PMC: Literatursuche über die REST-API.",
    no_args_is_help=True,
)


@pubmed_app.command("search")
def pubmed_search(
    query: str = typer.Argument(
        ..., help="Suchbegriff (PubMed-Query-Syntax erlaubt)."
    ),
    retmax: int = typer.Option(20, "--retmax", help="Maximale Trefferzahl."),
    json_: bool = typer.Option(False, "--json", help="Ausgabe als JSON-Lines."),
) -> None:
    """Sucht Publikationen in PubMed und gibt Treffer mit PMID/DOI aus."""
    from rdc import main

    with HttpClient() as client:
        conn = history.connect(history.default_db_path())
        records = run_pubmed_search(
            client, conn, term=query, retmax=retmax, api_key=_api_key()
        )
    main.render(
        records,
        PUBMED_HEADERS,
        json_override=json_,
        empty="(keine Treffer)",
    )


@pubmed_app.command("fetch")
def pubmed_fetch(
    pmids: list[str] = typer.Argument(..., help="Eine oder mehrere PMIDs."),
    json_: bool = typer.Option(False, "--json", help="Ausgabe als JSON-Lines."),
) -> None:
    """Holt Metadaten und Abstracts zu einer oder mehreren PMIDs."""
    from rdc import main

    with HttpClient() as client:
        conn = history.connect(history.default_db_path())
        records = run_pubmed_fetch(client, conn, pmids=pmids, api_key=_api_key())
    main.render(
        records,
        PUBMED_HEADERS,
        json_override=json_,
        empty="(keine Datensätze)",
    )


@europepmc_app.command("search")
def europepmc_search(
    query: str = typer.Argument(..., help="Suchbegriff (Europe-PMC-Syntax)."),
    page_size: int = typer.Option(
        25, "--page-size", help="Trefferzahl pro Seite."
    ),
    json_: bool = typer.Option(False, "--json", help="Ausgabe als JSON-Lines."),
) -> None:
    """Sucht Publikationen in Europe PMC (Titel, Autoren, PMID/PMCID/DOI)."""
    from rdc import main

    with HttpClient() as client:
        conn = history.connect(history.default_db_path())
        records = run_europepmc_search(
            client, conn, query=query, page_size=page_size
        )
    main.render(
        records,
        EUROPEPMC_HEADERS,
        json_override=json_,
        empty="(keine Treffer)",
    )
