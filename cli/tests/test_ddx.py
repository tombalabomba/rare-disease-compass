"""Tests für die Differentialdiagnose-Quelle (PubCaseFinder + Phen2Gene).

Alle HTTP-Interaktionen laufen über ``httpx.MockTransport`` — **kein** echter
Netzwerk-Call. Der Transport zählt Treffer, damit der Negativ-Fall (ungültige
HPO-Eingabe → kein Request) maschinell prüfbar ist. Die History ist durchweg
in-memory (``":memory:"``).
"""

from __future__ import annotations

import httpx
import pytest
from typer.testing import CliRunner

from rdc import history
from rdc.http_client import HttpClient
from rdc.main import app
from rdc.sources import ddx

# -- Fixtures (gemockte Responses) ----------------------------------------

# PubCaseFinder pcf_get_ranked_list: gerankte seltene Krankheiten.
_PUBCASEFINDER_JSON = [
    {
        "rank": 1,
        "id": "OMIM:154700",
        "disease_name_en": "Marfan syndrome",
        "score": 0.83,
    },
    {
        "rank": 2,
        "id": "OMIM:130050",
        "disease_name_en": "Ehlers-Danlos syndrome, vascular type",
        "score": 0.51,
    },
]

# Phen2Gene API: gerankte Kandidatengene (Felder als Strings wie im Original).
_PHEN2GENE_JSON = {
    "results": [
        {"Rank": "1", "Gene": "FBN1", "ID": "2200", "Score": "1.0",
         "Status": "SeedGene"},
        {"Rank": "2", "Gene": "TGFBR2", "ID": "7048", "Score": "0.42",
         "Status": "SeedGene"},
    ],
}


class _CountingRouter:
    """Routet gemockte Responses und zählt jeden tatsächlichen HTTP-Aufruf."""

    def __init__(self) -> None:
        self.calls = 0

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.calls += 1
        url = str(request.url)
        if "pubcasefinder" in url:
            return httpx.Response(200, json=_PUBCASEFINDER_JSON)
        if "phen2gene" in url:
            return httpx.Response(200, json=_PHEN2GENE_JSON)
        return httpx.Response(404)


def _client(router: _CountingRouter | None = None) -> HttpClient:
    router = router or _CountingRouter()
    return HttpClient(transport=httpx.MockTransport(router), min_interval=0)


# -- HPO-Validierung (reine Funktion, Single source of truth) -------------


def test_is_valid_hpo_accepts_canonical_form() -> None:
    assert ddx.is_valid_hpo("HP:0001250")
    assert ddx.is_valid_hpo(" HP:0001263 ")  # Whitespace toleriert


def test_is_valid_hpo_rejects_garbage() -> None:
    assert not ddx.is_valid_hpo("HP:123")  # zu wenige Ziffern
    assert not ddx.is_valid_hpo("0001250")  # Präfix fehlt
    assert not ddx.is_valid_hpo("foo")
    assert not ddx.is_valid_hpo("")
    assert not ddx.is_valid_hpo("HP:00012501")  # zu viele Ziffern


def test_validate_hpo_terms_trims_and_dedupes() -> None:
    assert ddx.validate_hpo_terms(["HP:0001250", " HP:0001263 "]) == [
        "HP:0001250",
        "HP:0001263",
    ]
    assert ddx.validate_hpo_terms(["HP:0001250", "HP:0001250"]) == ["HP:0001250"]


@pytest.mark.parametrize("bad", ["HP:123", "0001250", "foo", ""])
def test_validate_hpo_terms_rejects_garbage(bad: str) -> None:
    with pytest.raises(ValueError):
        ddx.validate_hpo_terms([bad])


def test_validate_hpo_terms_rejects_empty_list() -> None:
    with pytest.raises(ValueError):
        ddx.validate_hpo_terms([])


def test_validate_hpo_terms_rejects_mixed_valid_and_garbage() -> None:
    with pytest.raises(ValueError):
        ddx.validate_hpo_terms(["HP:0001250", "foo"])


# -- Query-Params (reine Funktionen) --------------------------------------


def test_pubcasefinder_params_joins_with_comma() -> None:
    params = ddx.pubcasefinder_params(["HP:0001250", "HP:0001263"])
    assert params["hpo_id"] == "HP:0001250,HP:0001263"
    assert params["format"] == "json"
    assert params["target"] == ddx.PUBCASEFINDER_TARGET


def test_phen2gene_params_joins_with_semicolon() -> None:
    params = ddx.phen2gene_params(["HP:0001250", "HP:0001263"])
    assert params["HPO_list"] == "HP:0001250;HP:0001263"


# -- Response-Parsing (reine Funktionen) ----------------------------------


def test_parse_pubcasefinder_extracts_ranked_diseases() -> None:
    records = ddx.parse_pubcasefinder(_PUBCASEFINDER_JSON)
    assert len(records) == 2
    assert records[0]["rank"] == 1
    assert records[0]["id"] == "OMIM:154700"
    assert records[0]["disease"] == "Marfan syndrome"
    assert records[0]["score"] == 0.83
    # API-Reihenfolge bleibt erhalten (gerankt).
    assert records[1]["id"] == "OMIM:130050"


def test_parse_pubcasefinder_limit_truncates() -> None:
    records = ddx.parse_pubcasefinder(_PUBCASEFINDER_JSON, limit=1)
    assert len(records) == 1
    assert records[0]["id"] == "OMIM:154700"


def test_parse_pubcasefinder_empty_response() -> None:
    assert ddx.parse_pubcasefinder([]) == []
    assert ddx.parse_pubcasefinder({}) == []
    assert ddx.parse_pubcasefinder(None) == []


def test_parse_pubcasefinder_rank_falls_back_to_position() -> None:
    data = [{"id": "OMIM:1", "disease_name_en": "X"}]  # kein rank-Feld
    assert ddx.parse_pubcasefinder(data)[0]["rank"] == 1


def test_parse_phen2gene_extracts_ranked_genes() -> None:
    records = ddx.parse_phen2gene(_PHEN2GENE_JSON)
    assert len(records) == 2
    assert records[0]["rank"] == 1
    assert records[0]["gene"] == "FBN1"
    assert records[0]["gene_id"] == "2200"
    assert records[0]["score"] == "1.0"
    assert records[1]["gene"] == "TGFBR2"


def test_parse_phen2gene_limit_truncates() -> None:
    records = ddx.parse_phen2gene(_PHEN2GENE_JSON, limit=1)
    assert len(records) == 1
    assert records[0]["gene"] == "FBN1"


def test_parse_phen2gene_skips_rows_without_gene() -> None:
    data = {"results": [{"Rank": "1", "ID": "2200", "Score": "1.0"}]}
    assert ddx.parse_phen2gene(data) == []


def test_parse_phen2gene_empty_response() -> None:
    assert ddx.parse_phen2gene({"results": []}) == []
    assert ddx.parse_phen2gene({}) == []


# -- Kernlogik + History (über MockTransport) -----------------------------


def test_run_pubcasefinder_rank_writes_history() -> None:
    conn = history.connect(":memory:")
    records = ddx.run_pubcasefinder_rank(
        _client(), conn, hpo_ids=["HP:0001250", "HP:0001263"]
    )

    assert records[0]["id"] == "OMIM:154700"
    rows = history.list_queries(conn, limit=10)
    assert len(rows) == 1
    assert rows[0]["source"] == "pubcasefinder"
    assert rows[0]["command"] == "rank"
    assert rows[0]["result_count"] == 2
    # HPO-Liste landet in den gespeicherten Params.
    assert '"HP:0001250"' in rows[0]["params"]
    assert '"HP:0001263"' in rows[0]["params"]


def test_run_pubcasefinder_rank_limit_truncates() -> None:
    conn = history.connect(":memory:")
    records = ddx.run_pubcasefinder_rank(
        _client(), conn, hpo_ids=["HP:0001250"], limit=1
    )
    assert len(records) == 1


def test_run_phen2gene_genes_writes_history() -> None:
    conn = history.connect(":memory:")
    records = ddx.run_phen2gene_genes(
        _client(), conn, hpo_ids=["HP:0001250", "HP:0001263"]
    )

    assert records[0]["gene"] == "FBN1"
    rows = history.list_queries(conn, limit=10, source="phen2gene")
    assert len(rows) == 1
    assert rows[0]["command"] == "genes"
    assert '"HP:0001250"' in rows[0]["params"]


def test_invalid_hpo_makes_no_http_call() -> None:
    """Negativ-Check: Müll-Eingabe → ValueError und **kein** HTTP-Treffer."""
    router = _CountingRouter()
    client = _client(router)
    conn = history.connect(":memory:")
    for bad in (["HP:123"], ["0001250"], ["foo"], [""]):
        with pytest.raises(ValueError):
            ddx.run_pubcasefinder_rank(client, conn, hpo_ids=bad)
        with pytest.raises(ValueError):
            ddx.run_phen2gene_genes(client, conn, hpo_ids=bad)
    assert router.calls == 0
    # Keine History-Einträge bei abgelehnter Eingabe.
    assert history.list_queries(conn, limit=10) == []


# -- CLI-Verdrahtung ------------------------------------------------------


def test_pubcasefinder_help_lists_rank() -> None:
    result = CliRunner().invoke(app, ["pubcasefinder", "--help"])
    assert result.exit_code == 0
    assert "rank" in result.output


def test_phen2gene_help_lists_genes() -> None:
    result = CliRunner().invoke(app, ["phen2gene", "--help"])
    assert result.exit_code == 0
    assert "genes" in result.output


def test_cli_rejects_invalid_hpo_with_nonzero_exit() -> None:
    result = CliRunner().invoke(app, ["pubcasefinder", "rank", "foo"])
    assert result.exit_code != 0


def test_groups_registered() -> None:
    from rdc import main

    assert "pubcasefinder" in main.registered_groups()
    assert "phen2gene" in main.registered_groups()
