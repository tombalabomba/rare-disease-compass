"""Tests für die SQLite-History — durchweg in-memory (``":memory:"``)."""

from __future__ import annotations

from rdc import history


def _seed(conn) -> None:
    history.save_query(
        conn,
        source="pubmed",
        command="search",
        params={"q": "BRCA1"},
        result_summary="3 Treffer",
        result_count=3,
        timestamp="2026-06-01T10:00:00+00:00",
    )
    history.save_query(
        conn,
        source="variant",
        command="lookup",
        params={"rcv": "RCV000123"},
        result_summary="1 Record",
        result_count=1,
        timestamp="2026-06-02T10:00:00+00:00",
    )
    history.save_query(
        conn,
        source="pubmed",
        command="search",
        params={"q": "TP53"},
        result_summary="5 Treffer",
        result_count=5,
        timestamp="2026-06-03T10:00:00+00:00",
    )


def test_save_returns_incrementing_ids() -> None:
    conn = history.connect(":memory:")
    first = history.save_query(conn, source="pubmed", command="search")
    second = history.save_query(conn, source="pubmed", command="search")
    assert first == 1
    assert second == 2


def test_list_orders_newest_first() -> None:
    conn = history.connect(":memory:")
    _seed(conn)

    rows = history.list_queries(conn, limit=10)

    assert len(rows) == 3
    assert rows[0]["result_count"] == 5  # TP53, zuletzt
    assert rows[-1]["result_count"] == 3  # BRCA1, zuerst


def test_list_respects_limit() -> None:
    conn = history.connect(":memory:")
    _seed(conn)

    rows = history.list_queries(conn, limit=2)

    assert len(rows) == 2
    assert rows[0]["result_count"] == 5


def test_list_filters_by_source() -> None:
    conn = history.connect(":memory:")
    _seed(conn)

    rows = history.list_queries(conn, limit=10, source="pubmed")

    assert len(rows) == 2
    assert all(row["source"] == "pubmed" for row in rows)


def test_search_matches_params_via_like() -> None:
    conn = history.connect(":memory:")
    _seed(conn)

    found = history.search_queries(conn, "BRCA1")

    assert len(found) == 1
    assert found[0]["result_count"] == 3


def test_search_matches_source() -> None:
    conn = history.connect(":memory:")
    _seed(conn)

    found = history.search_queries(conn, "variant")

    assert len(found) == 1
    assert found[0]["command"] == "lookup"


def test_search_no_match_returns_empty() -> None:
    conn = history.connect(":memory:")
    _seed(conn)

    assert history.search_queries(conn, "does-not-exist") == []
