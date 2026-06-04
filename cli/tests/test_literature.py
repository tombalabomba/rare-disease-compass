"""Tests für die Literatur-Quelle (PubMed + Europe PMC).

Alle HTTP-Interaktionen laufen über ``httpx.MockTransport`` — **kein** echter
Netzwerk-Call. Die History ist durchweg in-memory (``":memory:"``).
"""

from __future__ import annotations

import httpx
from typer.testing import CliRunner

from rdc import history
from rdc.http_client import HttpClient
from rdc.main import app
from rdc.sources import literature

# -- Fixtures (gemockte API-Antworten) ------------------------------------

_ESEARCH_JSON = {
    "esearchresult": {"count": "42", "idlist": ["111", "222"]},
}

_ESUMMARY_JSON = {
    "result": {
        "uids": ["111", "222"],
        "111": {
            "uid": "111",
            "title": "A rare phenotype",
            "pubdate": "2021 Mar",
            "source": "J Rare Dis",
            "authors": [{"name": "Smith J"}, {"name": "Doe A"}],
            "articleids": [{"idtype": "doi", "value": "10.1000/abc"}],
        },
        "222": {
            "uid": "222",
            "title": "Another report",
            "pubdate": "2019",
            "source": "Clin Genet",
            "authors": [{"name": "Roe B"}],
            "articleids": [{"idtype": "pubmed", "value": "222"}],
        },
    },
}

_EFETCH_XML = """<?xml version="1.0"?>
<PubmedArticleSet>
  <PubmedArticle>
    <MedlineCitation>
      <PMID>111</PMID>
      <Article>
        <Abstract>
          <AbstractText Label="Background">First part.</AbstractText>
          <AbstractText>Second part.</AbstractText>
        </Abstract>
      </Article>
    </MedlineCitation>
  </PubmedArticle>
</PubmedArticleSet>
"""

_EUROPEPMC_JSON = {
    "hitCount": 7,
    "resultList": {
        "result": [
            {
                "id": "PMC123",
                "source": "MED",
                "pmid": "333",
                "pmcid": "PMC123",
                "doi": "10.1/xyz",
                "title": "Europe PMC hit",
                "authorString": "Lee K, Park S.",
                "pubYear": "2022",
                "journalTitle": "Eur J Med Genet",
            }
        ]
    },
}


def _route(request: httpx.Request) -> httpx.Response:
    path = request.url.path
    if "esearch.fcgi" in path:
        return httpx.Response(200, json=_ESEARCH_JSON)
    if "esummary.fcgi" in path:
        return httpx.Response(200, json=_ESUMMARY_JSON)
    if "efetch.fcgi" in path:
        return httpx.Response(200, text=_EFETCH_XML)
    if "/search" in path:
        return httpx.Response(200, json=_EUROPEPMC_JSON)
    return httpx.Response(404)


def _client() -> HttpClient:
    return HttpClient(transport=httpx.MockTransport(_route), min_interval=0)


# -- Query-Param-Bildung --------------------------------------------------


def test_pubmed_search_params_has_expected_keys() -> None:
    params = literature.pubmed_search_params("BRCA1", retmax=5)
    assert params["db"] == "pubmed"
    assert params["term"] == "BRCA1"
    assert params["retmax"] == 5
    assert params["retmode"] == "json"
    assert "api_key" not in params


def test_pubmed_search_params_includes_api_key_when_set() -> None:
    with_key = literature.pubmed_search_params("BRCA1", api_key="SECRET")
    assert with_key["api_key"] == "SECRET"


def test_europepmc_search_params() -> None:
    params = literature.europepmc_search_params("phenotype", page_size=10)
    assert params["query"] == "phenotype"
    assert params["format"] == "json"
    assert params["pageSize"] == 10


# -- Parsing --------------------------------------------------------------


def test_parse_esearch_extracts_pmids_and_total() -> None:
    parsed = literature.parse_esearch(_ESEARCH_JSON)
    assert parsed["pmids"] == ["111", "222"]
    assert parsed["total"] == 42


def test_parse_esummary_extracts_records() -> None:
    records = literature.parse_esummary(_ESUMMARY_JSON)
    assert [r["pmid"] for r in records] == ["111", "222"]
    assert records[0]["title"] == "A rare phenotype"
    assert records[0]["year"] == "2021"
    assert records[0]["authors"] == "Smith J, Doe A"
    assert records[0]["doi"] == "10.1000/abc"
    assert records[1]["doi"] == ""  # nur pubmed-id, kein DOI


def test_parse_efetch_abstracts() -> None:
    abstracts = literature.parse_efetch_abstracts(_EFETCH_XML)
    assert "111" in abstracts
    assert "Background: First part." in abstracts["111"]
    assert "Second part." in abstracts["111"]


def test_parse_europepmc_extracts_records() -> None:
    parsed = literature.parse_europepmc(_EUROPEPMC_JSON)
    assert parsed["total"] == 7
    record = parsed["records"][0]
    assert record["pmid"] == "333"
    assert record["pmcid"] == "PMC123"
    assert record["year"] == "2022"
    assert record["doi"] == "10.1/xyz"


# -- Kernlogik + History (über MockTransport) -----------------------------


def test_run_pubmed_search_writes_history() -> None:
    conn = history.connect(":memory:")
    records = literature.run_pubmed_search(_client(), conn, term="BRCA1")

    assert [r["pmid"] for r in records] == ["111", "222"]
    rows = history.list_queries(conn, limit=10)
    assert len(rows) == 1
    assert rows[0]["source"] == "pubmed"
    assert rows[0]["command"] == "search"
    assert rows[0]["result_count"] == 2


def test_run_pubmed_fetch_attaches_abstract() -> None:
    conn = history.connect(":memory:")
    records = literature.run_pubmed_fetch(_client(), conn, pmids=["111", "222"])

    by_pmid = {r["pmid"]: r for r in records}
    assert "First part." in by_pmid["111"]["abstract"]
    assert by_pmid["222"]["abstract"] == ""  # kein Abstract im efetch-XML
    rows = history.list_queries(conn, limit=10, source="pubmed")
    assert rows[0]["command"] == "fetch"


def test_run_europepmc_search_writes_history() -> None:
    conn = history.connect(":memory:")
    records = literature.run_europepmc_search(_client(), conn, query="phenotype")

    assert records[0]["pmid"] == "333"
    rows = history.list_queries(conn, limit=10, source="europepmc")
    assert len(rows) == 1
    assert rows[0]["command"] == "search"
    assert rows[0]["result_count"] == 1


def test_run_pubmed_search_empty_logs_zero() -> None:
    def empty_route(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"esearchresult": {"count": "0", "idlist": []}})

    client = HttpClient(transport=httpx.MockTransport(empty_route), min_interval=0)
    conn = history.connect(":memory:")
    records = literature.run_pubmed_search(client, conn, term="no-such-term")

    assert records == []
    rows = history.list_queries(conn, limit=10)
    assert rows[0]["result_count"] == 0


# -- CLI-Verdrahtung ------------------------------------------------------


def test_pubmed_help_lists_subcommands() -> None:
    result = CliRunner().invoke(app, ["pubmed", "--help"])
    assert result.exit_code == 0
    assert "search" in result.output
    assert "fetch" in result.output


def test_europepmc_help_lists_subcommands() -> None:
    result = CliRunner().invoke(app, ["europepmc", "--help"])
    assert result.exit_code == 0
    assert "search" in result.output


def test_groups_registered() -> None:
    from rdc import main

    assert "pubmed" in main.registered_groups()
    assert "europepmc" in main.registered_groups()
