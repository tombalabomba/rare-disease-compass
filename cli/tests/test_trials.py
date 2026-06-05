"""Tests für die Studien-Quelle (ClinicalTrials.gov API v2).

Alle HTTP-Interaktionen laufen über ``httpx.MockTransport`` — **kein** echter
Netzwerk-Call. Die History ist durchweg in-memory (``":memory:"``).
"""

from __future__ import annotations

import json

import httpx
from typer.testing import CliRunner

from rdc import history
from rdc.http_client import HttpClient
from rdc.main import app
from rdc.sources import trials

# -- Fixtures (gemockte Responses) ----------------------------------------

# Zwei Studien im v2-Schema (verschachtelt unter protocolSection).
_STUDIES_JSON = {
    "totalCount": 42,
    "studies": [
        {
            "protocolSection": {
                "identificationModule": {
                    "nctId": "NCT05809323",
                    "briefTitle": "Marfan Syndrome Moderate Exercise Trial II",
                },
                "statusModule": {"overallStatus": "RECRUITING"},
                "designModule": {"phases": ["NA"]},
                "contactsLocationsModule": {
                    "locations": [
                        {
                            "facility": "Texas Children's Hospital",
                            "city": "Houston",
                            "country": "United States",
                        },
                        {"city": "Boston", "country": "United States"},
                        {"city": "Berlin", "country": "Germany"},
                    ]
                },
            }
        },
        {
            "protocolSection": {
                "identificationModule": {
                    "nctId": "NCT06720883",
                    "briefTitle": "A Second Study",
                },
                "statusModule": {"overallStatus": "COMPLETED"},
                "designModule": {},
                "contactsLocationsModule": {},
            }
        },
    ],
}

_STUDIES_EMPTY: dict[str, object] = {"totalCount": 0, "studies": []}


def _route(request: httpx.Request) -> httpx.Response:
    url = str(request.url)
    if "clinicaltrials.gov/api/v2/studies" in url:
        if "Unbekanntomalie" in url:
            return httpx.Response(200, json=_STUDIES_EMPTY)
        return httpx.Response(200, json=_STUDIES_JSON)
    return httpx.Response(404)


def _client() -> HttpClient:
    return HttpClient(transport=httpx.MockTransport(_route), min_interval=0)


# -- Reine Funktionen (URLs/Params, ohne HTTP) ----------------------------


def test_study_url_is_full_link() -> None:
    url = trials.study_url("NCT05809323")
    assert url == "https://clinicaltrials.gov/study/NCT05809323"
    assert url.startswith("https://")


def test_search_params_default_has_no_status_or_country_filter() -> None:
    params = trials.studies_search_params("Marfan syndrome", limit=15)
    assert params["query.cond"] == "Marfan syndrome"
    assert params["pageSize"] == 15
    assert "filter.overallStatus" not in params
    assert "query.locn" not in params


def test_search_params_recruiting_sets_status_filter() -> None:
    params = trials.studies_search_params("Marfan syndrome", recruiting=True)
    assert params["filter.overallStatus"] == trials.RECRUITING_STATUS == "RECRUITING"


def test_search_params_country_sets_location_filter() -> None:
    params = trials.studies_search_params("Marfan syndrome", country="Germany")
    assert params["query.locn"] == "Germany"


def test_summarize_locations_is_terse() -> None:
    locations = [
        {"city": "Houston", "country": "United States"},
        {"city": "Boston", "country": "United States"},
        {"city": "Berlin", "country": "Germany"},
    ]
    summary = trials.summarize_locations(locations, max_n=2)
    assert summary == "Houston, United States; Boston, United States (+1)"


def test_summarize_locations_handles_missing() -> None:
    assert trials.summarize_locations(None) == ""
    assert trials.summarize_locations([]) == ""


# -- Parsing: NCT-ID wird zu vollständigem Link ---------------------------


def test_parse_studies_builds_full_nct_link() -> None:
    parsed = trials.parse_studies(_STUDIES_JSON)
    assert parsed["total"] == 42
    records = parsed["records"]
    assert len(records) == 2
    first = records[0]
    assert first["nct"] == "NCT05809323"
    assert first["url"] == "https://clinicaltrials.gov/study/NCT05809323"
    assert first["status"] == "RECRUITING"
    assert first["phase"] == "NA"
    assert "Houston, United States" in first["locations"]


def test_parse_studies_empty_is_safe() -> None:
    parsed = trials.parse_studies(_STUDIES_EMPTY)
    assert parsed["total"] == 0
    assert parsed["records"] == []


def test_every_record_carries_full_http_link() -> None:
    """Acceptance: keine nackten IDs — jede Zeile hat einen http(s)://-Link."""
    records = trials.parse_studies(_STUDIES_JSON)["records"]
    for record in records:
        url = str(record["url"])
        assert url.startswith("http://") or url.startswith("https://")


# -- Kernlogik + History (über MockTransport) -----------------------------


def test_run_studies_search_writes_history() -> None:
    conn = history.connect(":memory:")
    records = trials.run_studies_search(_client(), conn, term="Marfan syndrome")

    assert records[0]["url"].endswith("/study/NCT05809323")
    db_rows = history.list_queries(conn, limit=10, source="trials")
    assert len(db_rows) == 1
    assert db_rows[0]["command"] == "search"
    assert db_rows[0]["result_count"] == 2


def test_run_studies_search_empty_still_logs() -> None:
    conn = history.connect(":memory:")
    records = trials.run_studies_search(_client(), conn, term="Unbekanntomalie")
    assert records == []
    db_rows = history.list_queries(conn, limit=10, source="trials")
    assert len(db_rows) == 1
    assert db_rows[0]["result_count"] == 0


def test_history_stores_only_query_no_pii() -> None:
    """Negativ-Check: History speichert nur Suchbegriff + Filter, keine PII."""
    conn = history.connect(":memory:")
    trials.run_studies_search(
        _client(), conn, term="Marfan syndrome", recruiting=True, country="Germany"
    )
    db_rows = history.list_queries(conn, limit=10, source="trials")
    params = json.loads(db_rows[0]["params"])
    assert set(params.keys()) == {"term", "recruiting", "country", "limit"}
    assert params["term"] == "Marfan syndrome"


# -- CLI-Verdrahtung ------------------------------------------------------


def test_trials_help_lists_search() -> None:
    result = CliRunner().invoke(app, ["trials", "--help"])
    assert result.exit_code == 0
    assert "search" in result.output


def test_search_help_lists_recruiting_flag() -> None:
    result = CliRunner().invoke(app, ["trials", "search", "--help"])
    assert result.exit_code == 0
    assert "--recruiting" in result.output


def test_groups_registered() -> None:
    from rdc import main

    assert "trials" in main.registered_groups()
