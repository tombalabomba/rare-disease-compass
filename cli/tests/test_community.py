"""Tests für die Community-Quelle (Patientenorganisationen + RareConnect).

Alle HTTP-Interaktionen laufen über ``httpx.MockTransport`` — **kein** echter
Netzwerk-Call. Die History ist durchweg in-memory (``":memory:"``).
"""

from __future__ import annotations

import httpx
from typer.testing import CliRunner

from rdc import history
from rdc.http_client import HttpClient
from rdc.main import app
from rdc.sources import community

# -- Fixtures (gemockte Responses) ----------------------------------------

# Orphadata rd-cross-referencing: data.results als Einzel-Objekt (wie graph).
_ORPHANET_JSON = {
    "data": {
        "results": {
            "ORPHAcode": 558,
            "Preferred term": "Marfan syndrome",
            "ExternalReference": [
                {"Source": "OMIM", "Reference": "154700"},
            ],
        }
    },
    "datasetCategory": "rd-cross-referencing",
}

# Leere Orphadata-Antwort (Krankheit nicht aufgelöst).
_ORPHANET_EMPTY = {"data": {"results": {}}, "datasetCategory": "rd-cross-referencing"}


def _route(request: httpx.Request) -> httpx.Response:
    url = str(request.url)
    if "orphadata.com" in url:
        # Ein unbekannter Name (kein "marfan") liefert die leere Antwort.
        if "names/" in request.url.path and "marfan" not in url.lower():
            return httpx.Response(200, json=_ORPHANET_EMPTY)
        return httpx.Response(200, json=_ORPHANET_JSON)
    return httpx.Response(404)


def _client() -> HttpClient:
    return HttpClient(transport=httpx.MockTransport(_route), min_interval=0)


# -- Reine Funktionen (URLs/Slugs, ohne HTTP) -----------------------------


def test_slugify_disease_basic() -> None:
    assert community.slugify_disease("Marfan syndrome") == "marfan-syndrome"


def test_slugify_disease_collapses_and_strips() -> None:
    assert community.slugify_disease("  Ehlers–Danlos,  type IV! ") == (
        "ehlers-danlos-type-iv"
    )
    assert community.slugify_disease("---") == ""
    assert community.slugify_disease("") == ""


def test_orphanet_disease_url() -> None:
    assert community.orphanet_disease_url("558").endswith("/disease/detail/558")
    assert community.orphanet_disease_url("558").startswith("https://")


def test_rareconnect_community_url() -> None:
    url = community.rareconnect_community_url("marfan-syndrome")
    assert url == "https://www.rareconnect.org/en/community/marfan-syndrome"


# -- Zeilen-Bildung: jede Zeile trägt einen vollständigen Link -------------


def test_orgs_rows_resolved_has_orpha_deep_link() -> None:
    rows = community.orgs_rows("558", "Marfan syndrome", "Marfan syndrome")
    assert len(rows) == 1
    assert rows[0]["url"] == "https://www.orpha.net/en/disease/detail/558"
    assert "Marfan syndrome" in rows[0]["name"]


def test_orgs_rows_unresolved_falls_back_to_index() -> None:
    rows = community.orgs_rows("", "", "Unbekanntomalie")
    assert len(rows) == 1
    assert rows[0]["url"] == community.ORPHANET_DISEASE_INDEX_URL
    assert "Unbekanntomalie" in rows[0]["name"]


def test_rareconnect_rows_always_has_browse_url() -> None:
    rows = community.rareconnect_rows("", "")
    assert rows  # immer mindestens eine Zeile
    assert rows[0]["type"] == "browse"
    assert rows[0]["url"] == community.RARECONNECT_COMMUNITIES_URL


def test_rareconnect_rows_adds_candidate_from_name() -> None:
    rows = community.rareconnect_rows("Marfan syndrome", "558")
    assert len(rows) == 2
    candidate = rows[1]
    assert candidate["type"] == "candidate"
    assert candidate["url"].endswith("/community/marfan-syndrome")


def test_every_result_line_carries_full_http_link() -> None:
    """Acceptance: keine nackten IDs — jede Zeile hat einen http(s)://-Link."""
    rows = community.orgs_rows("558", "Marfan syndrome", "Marfan syndrome")
    rows += community.orgs_rows("", "", "x")
    rows += community.rareconnect_rows("Marfan syndrome", "558")
    rows += community.rareconnect_rows("", "")
    for row in rows:
        url = str(row["url"])
        assert url.startswith("http://") or url.startswith("https://")


# -- Kernlogik + History (über MockTransport) -----------------------------


def test_run_orgs_resolves_and_writes_history() -> None:
    conn = history.connect(":memory:")
    rows = community.run_orgs(_client(), conn, term="558")

    assert rows[0]["url"].endswith("/disease/detail/558")
    db_rows = history.list_queries(conn, limit=10, source="community")
    assert len(db_rows) == 1
    assert db_rows[0]["command"] == "orgs"
    assert db_rows[0]["result_count"] == 1


def test_run_orgs_unresolved_name_uses_fallback() -> None:
    conn = history.connect(":memory:")
    rows = community.run_orgs(_client(), conn, term="Voellig unbekannt")
    assert rows[0]["url"] == community.ORPHANET_DISEASE_INDEX_URL


def test_run_rareconnect_always_returns_url_and_writes_history() -> None:
    conn = history.connect(":memory:")
    rows = community.run_rareconnect(_client(), conn, term="558")

    assert rows[0]["url"] == community.RARECONNECT_COMMUNITIES_URL
    # Name aus der Auflösung erzeugt den Kandidaten-Slug.
    assert any(r["url"].endswith("/community/marfan-syndrome") for r in rows)
    db_rows = history.list_queries(conn, limit=10, source="community")
    assert len(db_rows) == 1
    assert db_rows[0]["command"] == "rareconnect"


def test_run_rareconnect_unresolved_still_has_browse_url() -> None:
    conn = history.connect(":memory:")
    rows = community.run_rareconnect(_client(), conn, term="Voellig unbekannt")
    assert rows[0]["url"] == community.RARECONNECT_COMMUNITIES_URL


def test_history_stores_only_query_no_pii() -> None:
    """Negativ-Check: History speichert nur die Abfrage, keine PII."""
    conn = history.connect(":memory:")
    community.run_orgs(_client(), conn, term="Marfan syndrome")
    db_rows = history.list_queries(conn, limit=10, source="community")
    params = db_rows[0]["params"]
    # Nur der Krankheits-Term + Sprache landen in den Params.
    assert "Marfan syndrome" in params
    assert set(__import__("json").loads(params).keys()) == {"term", "lang"}


# -- CLI-Verdrahtung ------------------------------------------------------


def test_community_help_lists_subcommands() -> None:
    result = CliRunner().invoke(app, ["community", "--help"])
    assert result.exit_code == 0
    assert "orgs" in result.output
    assert "rareconnect" in result.output


def test_groups_registered() -> None:
    from rdc import main

    assert "community" in main.registered_groups()
