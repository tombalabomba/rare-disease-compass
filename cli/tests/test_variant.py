"""Tests für die Varianten-Quelle (MyVariant.info: ClinVar + gnomAD).

Alle HTTP-Interaktionen laufen über ``httpx.MockTransport`` — **kein** echter
Netzwerk-Call. Die History ist durchweg in-memory (``":memory:"``).
"""

from __future__ import annotations

import httpx
from typer.testing import CliRunner

from rdc import history
from rdc.http_client import HttpClient
from rdc.main import app
from rdc.sources import variant

# -- Fixtures (gemockte MyVariant-Antworten) ------------------------------

_VARIANT_JSON = {
    "_id": "chr7:g.140453136A>T",
    "dbsnp": {"rsid": "rs113488022"},
    "clinvar": {
        "variant_id": 13961,
        "gene": {"symbol": "BRAF"},
        "rcv": [
            {
                "accession": "RCV000014992",
                "clinical_significance": "Pathogenic",
                "review_status": "criteria provided, single submitter",
                "conditions": {"name": "Melanoma"},
            },
            {
                "accession": "RCV000080903",
                "clinical_significance": "Pathogenic",
                "conditions": {"name": "Neoplasm of brain"},
            },
        ],
    },
    "gnomad_exome": {"af": {"af": 1.2e-5}},
    "gnomad_genome": {"af": {"af": 0.0}},
}

# Query-API verpackt Treffer unter ``hits`` (z. B. rsID-Lookup).
_QUERY_JSON = {"hits": [_VARIANT_JSON]}

# VUS ohne gnomAD-Frequenz und mit ``rcv`` als Einzel-Objekt (kein Listentyp).
_VUS_JSON = {
    "_id": "chr1:g.100A>G",
    "clinvar": {
        "variant_id": 42,
        "gene": {"symbol": "GENE1"},
        "rcv": {
            "accession": "RCV999999",
            "clinical_significance": "Uncertain significance",
        },
    },
}


def _route(request: httpx.Request) -> httpx.Response:
    path = request.url.path
    if "/v1/query" in path:
        return httpx.Response(200, json=_QUERY_JSON)
    if "/v1/variant/" in path:
        return httpx.Response(200, json=_VARIANT_JSON)
    return httpx.Response(404)


def _client() -> HttpClient:
    return HttpClient(transport=httpx.MockTransport(_route), min_interval=0)


# -- Eingabe-Erkennung + Query-Params -------------------------------------


def test_is_rsid_detects_rsids() -> None:
    assert variant.is_rsid("rs113488022")
    assert variant.is_rsid("RS123")
    assert not variant.is_rsid("chr7:g.140453136A>T")
    assert not variant.is_rsid("rs")
    assert not variant.is_rsid("rsABC")


def test_variant_lookup_params_omits_optional() -> None:
    params = variant.variant_lookup_params()
    assert "fields" not in params
    assert "api_key" not in params


def test_variant_lookup_params_includes_fields_and_key() -> None:
    params = variant.variant_lookup_params(fields="clinvar", api_key="SECRET")
    assert params["fields"] == "clinvar"
    assert params["api_key"] == "SECRET"


def test_variant_query_params_carries_q() -> None:
    params = variant.variant_query_params("rs113488022")
    assert params["q"] == "rs113488022"


# -- Parsing: Pathogenität ------------------------------------------------


def test_parse_clinvar_extracts_significance_and_rcv() -> None:
    parsed = variant.parse_clinvar(_VARIANT_JSON)
    assert parsed["clinical_significance"] == "Pathogenic"  # dedupliziert
    assert "RCV000014992" in parsed["rcv"]
    assert "RCV000080903" in parsed["rcv"]
    assert parsed["gene"] == "BRAF"
    assert parsed["variant_id"] == "13961"
    assert "Melanoma" in parsed["conditions"]


def test_parse_clinvar_tolerates_single_rcv_object() -> None:
    parsed = variant.parse_clinvar(_VUS_JSON)
    assert parsed["clinical_significance"] == "Uncertain significance"
    assert parsed["rcv"] == "RCV999999"
    assert parsed["review_status"] == ""  # fehlt → Leerwert, kein Crash


def test_parse_clinvar_missing_block_returns_empty() -> None:
    parsed = variant.parse_clinvar({"_id": "chrX:g.1A>T"})
    assert parsed["clinical_significance"] == ""
    assert parsed["gene"] == ""
    assert parsed["variant_id"] == ""


# -- Parsing: Frequenz ----------------------------------------------------


def test_parse_frequency_extracts_exome_and_genome() -> None:
    parsed = variant.parse_frequency(_VARIANT_JSON)
    assert parsed["gnomad_exome_af"] == 1.2e-5
    assert parsed["gnomad_genome_af"] == 0.0


def test_parse_frequency_missing_returns_empty_value() -> None:
    parsed = variant.parse_frequency(_VUS_JSON)
    assert parsed["gnomad_exome_af"] == variant.EMPTY
    assert parsed["gnomad_genome_af"] == variant.EMPTY


def test_parse_variant_combines_clinvar_and_frequency() -> None:
    record = variant.parse_variant(_VARIANT_JSON)
    assert record["rsid"] == "rs113488022"
    assert record["clinical_significance"] == "Pathogenic"
    assert record["gnomad_exome_af"] == 1.2e-5
    assert record["id"] == "chr7:g.140453136A>T"


def test_as_variant_unwraps_query_hits() -> None:
    assert variant.as_variant(_QUERY_JSON)["_id"] == "chr7:g.140453136A>T"
    assert variant.as_variant({"hits": []}) == {}
    assert variant.as_variant([_VUS_JSON])["_id"] == "chr1:g.100A>G"


# -- Kernlogik + History (über MockTransport) -----------------------------


def test_run_variant_lookup_writes_history() -> None:
    conn = history.connect(":memory:")
    records = variant.run_variant_lookup(
        _client(), conn, variant="chr7:g.140453136A>T"
    )

    assert len(records) == 1
    assert records[0]["clinical_significance"] == "Pathogenic"
    rows = history.list_queries(conn, limit=10)
    assert len(rows) == 1
    assert rows[0]["source"] == "variant"
    assert rows[0]["command"] == "lookup"
    assert rows[0]["result_count"] == 1


def test_run_variant_lookup_rsid_uses_query_api() -> None:
    conn = history.connect(":memory:")
    records = variant.run_variant_lookup(_client(), conn, variant="rs113488022")

    assert records[0]["rsid"] == "rs113488022"
    assert records[0]["gnomad_genome_af"] == 0.0


def test_run_variant_clinvar_writes_history_with_clinvar_source() -> None:
    conn = history.connect(":memory:")
    records = variant.run_variant_clinvar(
        _client(), conn, variant="chr7:g.140453136A>T"
    )

    assert records[0]["clinical_significance"] == "Pathogenic"
    assert "review_status" in records[0]
    rows = history.list_queries(conn, limit=10, source="clinvar")
    assert len(rows) == 1
    assert rows[0]["source"] == "clinvar"
    assert rows[0]["result_count"] == 1


def test_run_variant_lookup_vus_without_frequency_no_crash() -> None:
    def vus_route(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=_VUS_JSON)

    client = HttpClient(transport=httpx.MockTransport(vus_route), min_interval=0)
    conn = history.connect(":memory:")
    records = variant.run_variant_lookup(client, conn, variant="chr1:g.100A>G")

    assert records[0]["gnomad_exome_af"] == variant.EMPTY
    assert records[0]["clinical_significance"] == "Uncertain significance"


# -- CLI-Verdrahtung ------------------------------------------------------


def test_variant_help_lists_subcommands() -> None:
    result = CliRunner().invoke(app, ["variant", "--help"])
    assert result.exit_code == 0
    assert "lookup" in result.output
    assert "clinvar" in result.output


def test_group_registered() -> None:
    from rdc import main

    assert "variant" in main.registered_groups()
