"""Tests für die Compound-Quelle (quellenübergreifende Phänotyp-Abklärung).

Die Dedup-/Ranking-Logik wird über die **reinen** Funktionen mit Fixtures
geprüft (kein HTTP). Die Orchestrierung läuft über ``httpx.MockTransport`` —
**kein** echter Netzwerk-Call; der Transport zählt PubMed-Treffer, damit
``--no-literature`` maschinell prüfbar ist. Die History ist in-memory.
"""

from __future__ import annotations

import httpx
from typer.testing import CliRunner

from rdc import compound, history
from rdc.http_client import HttpClient
from rdc.main import app

# -- Fixtures: synthetische Kandidaten je Quelle --------------------------

# Zwei Quellen liefern dieselbe Krankheit (gleiche OMIM-ID, leicht andere
# Schreibweise des Namens) — muss zu EINEM Eintrag verschmelzen.
_PUBCASEFINDER = [
    {"rank": 1, "id": "OMIM:154700", "disease": "Marfan syndrome", "score": 0.83},
    {"rank": 2, "id": "OMIM:130050", "disease": "Ehlers-Danlos, vascular"},
]
_MONARCH = [
    {"id": "omim:154700", "name": "Marfan-Syndrom", "score": 3},
    {"id": "MONDO:0007947", "name": "Loeys-Dietz syndrome", "score": 2},
]


# -- Reine Funktionen: Normalisierung -------------------------------------


def test_normalize_disease_id_canonicalizes_prefix() -> None:
    assert compound.normalize_disease_id("omim:154700") == "OMIM:154700"
    assert compound.normalize_disease_id("Orphanet:558") == "ORPHA:558"
    assert compound.normalize_disease_id("ORPHA:558") == "ORPHA:558"
    assert compound.normalize_disease_id(" MONDO:0007947 ") == "MONDO:0007947"
    assert compound.normalize_disease_id("") == ""


# -- Reine Funktionen: Dedup + Ranking ------------------------------------


def test_merge_diseases_dedupes_same_id_across_sources() -> None:
    merged = compound.merge_disease_candidates(
        {"pubcasefinder": _PUBCASEFINDER, "monarch": _MONARCH}
    )
    # Marfan kommt aus beiden Quellen → genau EIN Eintrag.
    marfan = [r for r in merged if r["id"] == "OMIM:154700"]
    assert len(marfan) == 1
    assert marfan[0]["consensus"] == 2
    assert "monarch" in str(marfan[0]["sources"])
    assert "pubcasefinder" in str(marfan[0]["sources"])
    # Insgesamt drei distinkte Krankheiten (154700, 130050, MONDO).
    assert len({r["id"] for r in merged}) == 3


def test_merge_diseases_ranks_consensus_first() -> None:
    merged = compound.merge_disease_candidates(
        {"pubcasefinder": _PUBCASEFINDER, "monarch": _MONARCH}
    )
    # Der Mehrfach-Quellen-Konsens (Marfan, 2 Quellen) steht ganz oben.
    assert merged[0]["id"] == "OMIM:154700"
    assert merged[0]["consensus"] == 2
    assert all(r["consensus"] == 1 for r in merged[1:])


def test_merge_diseases_keeps_best_rank_per_source() -> None:
    merged = compound.merge_disease_candidates(
        {"pubcasefinder": _PUBCASEFINDER, "monarch": _MONARCH}
    )
    marfan = next(r for r in merged if r["id"] == "OMIM:154700")
    # PubCaseFinder rank=1, Monarch Position 1 → bester Rang 1.
    assert marfan["best_rank"] == 1


def test_merge_diseases_uses_position_when_rank_missing() -> None:
    merged = compound.merge_disease_candidates(
        {"monarch": [{"id": "OMIM:1", "name": "X"}, {"id": "OMIM:2", "name": "Y"}]}
    )
    by_id = {r["id"]: r for r in merged}
    assert by_id["OMIM:1"]["best_rank"] == 1
    assert by_id["OMIM:2"]["best_rank"] == 2


def test_merge_diseases_skips_records_without_id() -> None:
    merged = compound.merge_disease_candidates(
        {"pubcasefinder": [{"disease": "namenlos"}, {"id": "OMIM:9", "disease": "Z"}]}
    )
    assert [r["id"] for r in merged] == ["OMIM:9"]


def test_merge_genes_dedupes_symbol_across_sources() -> None:
    merged = compound.merge_gene_candidates(
        {
            "phen2gene": [{"rank": 1, "gene": "FBN1", "gene_id": "2200"}],
            "other": [{"rank": 3, "gene": "fbn1"}],
        }
    )
    fbn1 = [r for r in merged if str(r["gene"]).upper() == "FBN1"]
    assert len(fbn1) == 1
    assert fbn1[0]["consensus"] == 2
    assert fbn1[0]["gene_id"] == "2200"
    assert fbn1[0]["best_rank"] == 1


def test_literature_query_prefers_top_disease_then_gene() -> None:
    assert (
        compound.literature_query([{"disease": "Marfan syndrome"}], [{"gene": "FBN1"}])
        == "Marfan syndrome"
    )
    assert compound.literature_query([], [{"gene": "FBN1"}]) == "FBN1"
    assert compound.literature_query([], []) == ""


# -- Orchestrierung über MockTransport ------------------------------------

_PCF_JSON = [
    {"rank": 1, "id": "OMIM:154700", "disease_name_en": "Marfan syndrome"},
]
_P2G_JSON = {"results": [{"Rank": "1", "Gene": "FBN1", "ID": "2200", "Score": "1.0"}]}
_MONARCH_JSON = {
    "items": [
        {
            "subject": "MONDO:0007947",
            "subject_label": "Marfan syndrome",
            "object": "HP:0001166",
        }
    ]
}
_ESEARCH_JSON = {"esearchresult": {"idlist": ["12345678"], "count": "1"}}
_ESUMMARY_JSON = {
    "result": {
        "uids": ["12345678"],
        "12345678": {
            "title": "Marfan review",
            "authors": [{"name": "Müller A"}],
            "pubdate": "2021 Jan",
            "source": "J Rare Dis",
            "articleids": [{"idtype": "doi", "value": "10.1/x"}],
        },
    }
}


class _CountingRouter:
    """Routet gemockte Responses und zählt PubMed-Aufrufe separat."""

    def __init__(self) -> None:
        self.calls = 0
        self.pubmed_calls = 0

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.calls += 1
        url = str(request.url)
        if "pubcasefinder" in url:
            return httpx.Response(200, json=_PCF_JSON)
        if "phen2gene" in url:
            return httpx.Response(200, json=_P2G_JSON)
        if "monarchinitiative" in url:
            return httpx.Response(200, json=_MONARCH_JSON)
        if "esearch" in url:
            self.pubmed_calls += 1
            return httpx.Response(200, json=_ESEARCH_JSON)
        if "esummary" in url:
            self.pubmed_calls += 1
            return httpx.Response(200, json=_ESUMMARY_JSON)
        return httpx.Response(404)


def _client(router: _CountingRouter) -> HttpClient:
    return HttpClient(transport=httpx.MockTransport(router), min_interval=0)


def test_run_phenotype_workup_writes_compound_history() -> None:
    conn = history.connect(":memory:")
    result = compound.run_phenotype_workup(
        _client(_CountingRouter()), conn, hpo_ids=["HP:0001166", "HP:0001083"]
    )

    assert result["diseases"]
    assert result["genes"][0]["gene"] == "FBN1"
    assert result["literature"]  # Top-Kandidat wurde literarisch gesucht

    rows = history.list_queries(conn, limit=20, source="compound")
    assert len(rows) == 1
    assert rows[0]["command"] == "phenotype-workup"
    assert rows[0]["result_count"] == len(result["diseases"])
    # Die zugrundeliegenden Quellen protokollieren ihre Einzel-Einträge weiter.
    sources = {r["source"] for r in history.list_queries(conn, limit=50)}
    assert {"compound", "pubcasefinder", "monarch", "phen2gene", "pubmed"} <= sources


def test_run_phenotype_workup_no_literature_skips_pubmed() -> None:
    router = _CountingRouter()
    conn = history.connect(":memory:")
    result = compound.run_phenotype_workup(
        _client(router), conn, hpo_ids=["HP:0001166"], with_literature=False
    )
    assert result["literature"] == []
    assert router.pubmed_calls == 0


def test_invalid_hpo_makes_no_http_call() -> None:
    """Negativ-Check: Müll-Eingabe → ValueError und **kein** HTTP-Treffer."""
    import pytest

    router = _CountingRouter()
    conn = history.connect(":memory:")
    with pytest.raises(ValueError):
        compound.run_phenotype_workup(_client(router), conn, hpo_ids=["foo"])
    assert router.calls == 0
    assert history.list_queries(conn, limit=10) == []


# -- CLI-Verdrahtung ------------------------------------------------------


def test_compound_help_lists_phenotype_workup() -> None:
    result = CliRunner().invoke(app, ["compound", "--help"])
    assert result.exit_code == 0
    assert "phenotype-workup" in result.output


def test_compound_group_registered() -> None:
    from rdc import main

    assert "compound" in main.registered_groups()
