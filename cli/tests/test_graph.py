"""Tests für die Krankheits-Graph-Quelle (Monarch v3 + Orphanet/Orphadata).

Alle HTTP-Interaktionen laufen über ``httpx.MockTransport`` — **kein** echter
Netzwerk-Call. Die History ist durchweg in-memory (``":memory:"``).
"""

from __future__ import annotations

import httpx
from typer.testing import CliRunner

from rdc import history
from rdc.http_client import HttpClient
from rdc.main import app
from rdc.sources import graph

# -- Fixtures (gemockte Responses) ----------------------------------------

# Monarch-Association: Phänotyp→Krankheit. Pro Zeile ein (Krankheit, Phänotyp)-
# Paar. MONDO:0007947 trifft beide Query-Phänotypen, MONDO:0100148 nur einen.
_PHENOTYPE_JSON = {
    "limit": 500,
    "total": 3,
    "items": [
        {
            "subject": "MONDO:0007947",
            "subject_label": "Marfan syndrome",
            "predicate": "biolink:has_phenotype",
            "object": "HP:0001250",
        },
        {
            "subject": "MONDO:0007947",
            "subject_label": "Marfan syndrome",
            "predicate": "biolink:has_phenotype",
            "object": "HP:0001263",
        },
        {
            "subject": "MONDO:0100148",
            "subject_label": "X-linked disorder",
            "predicate": "biolink:has_phenotype",
            "object": "HP:0001250",
        },
    ],
}

# Monarch-Association: Gen→Krankheit.
_GENE_JSON = {
    "total": 1,
    "items": [
        {
            "id": "uuid:abc",
            "category": "biolink:CausalGeneToDiseaseAssociation",
            "subject": "HGNC:3603",
            "subject_label": "FBN1",
            "predicate": "biolink:causes",
            "object": "MONDO:0007947",
            "object_label": "Marfan syndrome",
        }
    ],
}

# Monarch-Search: Symbol→CURIE.
_SEARCH_JSON = {
    "total": 1,
    "items": [{"id": "HGNC:3603", "name": "FBN1", "category": "biolink:Gene"}],
}

# Orphadata rd-cross-referencing: data.results als Einzel-Objekt.
_ORPHANET_JSON = {
    "data": {
        "results": {
            "ORPHAcode": 558,
            "Preferred term": "Marfan syndrome",
            "ExternalReference": [
                {"Source": "OMIM", "Reference": "154700"},
                {"Source": "ICD-11", "Reference": "LD28.01"},
            ],
        }
    },
    "datasetCategory": "rd-cross-referencing",
}


def _route(request: httpx.Request) -> httpx.Response:
    url = str(request.url)
    if "monarchinitiative.org" in url and "/search" in request.url.path:
        return httpx.Response(200, json=_SEARCH_JSON)
    if "monarchinitiative.org" in url:
        params = request.url.params
        if params.get("category") == graph.GENE_DISEASE_CATEGORY:
            return httpx.Response(200, json=_GENE_JSON)
        return httpx.Response(200, json=_PHENOTYPE_JSON)
    if "orphadata.com" in url:
        return httpx.Response(200, json=_ORPHANET_JSON)
    return httpx.Response(404)


def _client() -> HttpClient:
    return HttpClient(transport=httpx.MockTransport(_route), min_interval=0)


# -- HPO-Serialisierung + Query-Params (reine Funktionen) -----------------


def test_serialize_hpo_terms_trims_and_dedupes() -> None:
    assert graph.serialize_hpo_terms(["HP:0001250", " HP:0001263 "]) == [
        "HP:0001250",
        "HP:0001263",
    ]
    assert graph.serialize_hpo_terms(["HP:0001250", "HP:0001250", ""]) == [
        "HP:0001250"
    ]


def test_diseases_by_phenotypes_params_repeats_object() -> None:
    params = graph.diseases_by_phenotypes_params(["HP:0001250", "HP:0001263"])
    # Liste unter "object" → httpx erzeugt wiederholte Query-Params.
    assert params["object"] == ["HP:0001250", "HP:0001263"]
    assert params["category"] == graph.DISEASE_PHENOTYPE_CATEGORY


def test_diseases_by_phenotypes_params_keeps_hpo_format() -> None:
    params = graph.diseases_by_phenotypes_params(["HP:0000118"])
    assert params["object"] == ["HP:0000118"]  # unverändert


def test_is_curie() -> None:
    assert graph.is_curie("HGNC:3603")
    assert not graph.is_curie("FBN1")


def test_orpha_code_of_detects_codes_and_terms() -> None:
    assert graph.orpha_code_of("558") == "558"
    assert graph.orpha_code_of("ORPHA:558") == "558"
    assert graph.orpha_code_of("ORPHAcode:558") == "558"
    assert graph.orpha_code_of("Marfan syndrome") is None


def test_orphanet_urls() -> None:
    assert graph.orphanet_code_url("558").endswith("/orphacodes/558")
    assert graph.orphanet_name_url("Marfan syndrome").endswith(
        "/names/Marfan syndrome"
    )


# -- Response-Parsing (reine Funktionen) ----------------------------------


def test_parse_disease_matches_aggregates_and_ranks() -> None:
    records = graph.parse_disease_matches(
        _PHENOTYPE_JSON, ["HP:0001250", "HP:0001263"]
    )
    assert records[0]["id"] == "MONDO:0007947"
    assert records[0]["name"] == "Marfan syndrome"
    assert records[0]["score"] == 2  # beide Query-Phänotypen getroffen
    assert "HP:0001250" in records[0]["matched"]
    # Krankheit mit weniger Treffern rangiert tiefer.
    assert records[1]["id"] == "MONDO:0100148"
    assert records[1]["score"] == 1


def test_parse_disease_matches_empty_response() -> None:
    assert graph.parse_disease_matches({"items": []}) == []
    assert graph.parse_disease_matches({}) == []


def test_parse_gene_diseases_extracts_records() -> None:
    records = graph.parse_gene_diseases(_GENE_JSON)
    assert len(records) == 1
    assert records[0]["gene"] == "FBN1"
    assert records[0]["disease_id"] == "MONDO:0007947"
    assert records[0]["disease"] == "Marfan syndrome"
    assert records[0]["predicate"] == "biolink:causes"


def test_parse_gene_diseases_missing_object_skipped() -> None:
    data = {"items": [{"subject": "HGNC:1", "subject_label": "X"}]}
    assert graph.parse_gene_diseases(data) == []


def test_first_search_id() -> None:
    assert graph.first_search_id(_SEARCH_JSON) == "HGNC:3603"
    assert graph.first_search_id({"items": []}) == graph.EMPTY


def test_parse_orphanet_extracts_entry() -> None:
    record = graph.parse_orphanet(_ORPHANET_JSON)
    assert record["orpha"] == "558"
    assert record["name"] == "Marfan syndrome"
    assert record["omim"] == "154700"
    assert "OMIM:154700" in record["xrefs"]
    assert "ICD-11:LD28.01" in record["xrefs"]


def test_parse_orphanet_tolerates_results_list() -> None:
    data = {"data": {"results": [_ORPHANET_JSON["data"]["results"]]}}
    assert graph.parse_orphanet(data)["orpha"] == "558"


def test_parse_orphanet_missing_returns_empty() -> None:
    record = graph.parse_orphanet({})
    assert record["orpha"] == graph.EMPTY
    assert record["name"] == graph.EMPTY


# -- Kernlogik + History (über MockTransport) -----------------------------


def test_run_diseases_by_phenotypes_writes_history() -> None:
    conn = history.connect(":memory:")
    records = graph.run_diseases_by_phenotypes(
        _client(), conn, hpo_ids=["HP:0001250", "HP:0001263"]
    )

    assert records[0]["id"] == "MONDO:0007947"
    rows = history.list_queries(conn, limit=10)
    assert len(rows) == 1
    assert rows[0]["source"] == "monarch"
    assert rows[0]["command"] == "diseases-by-phenotypes"
    assert rows[0]["result_count"] == 2


def test_run_diseases_by_phenotypes_limit_truncates() -> None:
    conn = history.connect(":memory:")
    records = graph.run_diseases_by_phenotypes(
        _client(), conn, hpo_ids=["HP:0001250", "HP:0001263"], limit=1
    )
    assert len(records) == 1
    assert records[0]["id"] == "MONDO:0007947"


def test_run_gene_to_diseases_resolves_symbol_and_writes_history() -> None:
    conn = history.connect(":memory:")
    records = graph.run_gene_to_diseases(_client(), conn, gene="FBN1")

    assert records[0]["disease_id"] == "MONDO:0007947"
    rows = history.list_queries(conn, limit=10, source="monarch")
    assert len(rows) == 1
    assert rows[0]["command"] == "gene-to-diseases"


def test_run_gene_to_diseases_curie_skips_search() -> None:
    conn = history.connect(":memory:")
    records = graph.run_gene_to_diseases(_client(), conn, gene="HGNC:3603")
    assert records[0]["gene"] == "FBN1"


def test_resolve_gene_curie_passthrough() -> None:
    assert graph.resolve_gene(_client(), "HGNC:3603") == "HGNC:3603"


def test_resolve_gene_symbol_via_search() -> None:
    assert graph.resolve_gene(_client(), "FBN1") == "HGNC:3603"


def test_run_orphanet_lookup_by_code_writes_history() -> None:
    conn = history.connect(":memory:")
    records = graph.run_orphanet_lookup(_client(), conn, term="558")

    assert records[0]["name"] == "Marfan syndrome"
    assert records[0]["omim"] == "154700"
    rows = history.list_queries(conn, limit=10, source="orphanet")
    assert len(rows) == 1
    assert rows[0]["command"] == "lookup"


def test_run_orphanet_lookup_by_name() -> None:
    conn = history.connect(":memory:")
    records = graph.run_orphanet_lookup(_client(), conn, term="Marfan syndrome")
    assert records[0]["orpha"] == "558"


# -- CLI-Verdrahtung ------------------------------------------------------


def test_monarch_help_lists_subcommands() -> None:
    result = CliRunner().invoke(app, ["monarch", "--help"])
    assert result.exit_code == 0
    assert "diseases-by-phenotypes" in result.output
    assert "gene-to-diseases" in result.output


def test_orphanet_help_lists_subcommands() -> None:
    result = CliRunner().invoke(app, ["orphanet", "--help"])
    assert result.exit_code == 0
    assert "lookup" in result.output


def test_groups_registered() -> None:
    from rdc import main

    assert "monarch" in main.registered_groups()
    assert "orphanet" in main.registered_groups()
