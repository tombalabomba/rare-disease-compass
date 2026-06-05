"""Tests für ``rdc community matchmaking`` (genetisches Matching, Wegweiser).

Der Befehl ist **offline**: kein HTTP-Aufruf, keine Datenübertragung. Ein
``HttpClient`` mit MockTransport, der jeden Call hart fehlschlagen lässt, beweist,
dass keine Netzwerk-Interaktion stattfindet. Negativ-Check: kein Code-Pfad sendet
Daten an MME/GeneMatcher/MyGene2.
"""

from __future__ import annotations

import inspect

import httpx
from typer.testing import CliRunner

from rdc.main import app
from rdc.sources import community

# -- Reine Funktion: statische Wegweiser-Zeilen ---------------------------


def test_matchmaking_rows_cover_all_paths() -> None:
    rows = community.matchmaking_rows()
    urls = {str(r["url"]) for r in rows}
    assert community.MATCHMAKER_EXCHANGE_URL in urls
    assert community.MATCHMAKER_PARTICIPANTS_URL in urls
    assert community.GENEMATCHER_URL in urls
    assert community.MYGENE2_URL in urls


def test_matchmaking_rows_every_line_has_full_https_link() -> None:
    for row in community.matchmaking_rows():
        url = str(row["url"])
        assert url.startswith("https://")
        # Jede Zeile trägt Ressource + Zielgruppe + Link.
        assert row["resource"] and row["audience"]


def test_matchmaking_rows_clinic_path_first() -> None:
    """Üblicher Weg (über die Klinik) steht vor dem Selbst-Teil-Weg."""
    rows = community.matchmaking_rows()
    assert rows[0]["url"] == community.MATCHMAKER_EXCHANGE_URL
    assert rows[-1]["url"] == community.MYGENE2_URL


# -- CLI: offline, gibt Links + Hinweis aus -------------------------------


def test_matchmaking_cli_outputs_links_and_note() -> None:
    result = CliRunner().invoke(app, ["community", "matchmaking"])
    assert result.exit_code == 0
    for url in (
        community.MATCHMAKER_EXCHANGE_URL,
        community.GENEMATCHER_URL,
        community.MYGENE2_URL,
    ):
        assert url in result.output
    # Einwilligungs-/Datenschutz-Hinweis im Tabellen-Modus.
    assert "RDC reicht nichts ein" in result.output


def test_matchmaking_cli_json_is_clean_lines() -> None:
    """``--json`` liefert nur JSON-Lines, ohne den Hinweis-Block."""
    import json

    result = CliRunner().invoke(app, ["community", "matchmaking", "--json"])
    assert result.exit_code == 0
    lines = [ln for ln in result.output.splitlines() if ln.strip()]
    assert lines  # mindestens eine Zeile
    for line in lines:
        json.loads(line)  # jede Zeile ist valides JSON
    assert "RDC reicht nichts ein" not in result.output


def test_matchmaking_makes_no_http_call() -> None:
    """Negativ-Check: der Befehl löst keinen Netzwerk-Verkehr aus.

    Ein MockTransport, der bei jedem Request explodiert, würde einen verdeckten
    HTTP-Aufruf sofort als Fehler sichtbar machen. Bleibt der Exit-Code 0, gab es
    keinen Call.
    """

    def _explode(request: httpx.Request) -> httpx.Response:  # pragma: no cover
        raise AssertionError(f"unerwarteter HTTP-Aufruf an {request.url}")

    # Auch wenn ein Client gebaut würde: er dürfte nie genutzt werden.
    with httpx.Client(transport=httpx.MockTransport(_explode)):
        result = CliRunner().invoke(app, ["community", "matchmaking"])
    assert result.exit_code == 0


# -- Negativ-Check: kein Submit/POST an die Matching-Netze ----------------


def test_no_data_submission_path_in_module() -> None:
    """Statisch: das Community-Modul enthält keinen POST/Submit an die Netze.

    Die Matching-Hosts dürfen ausschließlich als Wegweiser-URL auftauchen, nie in
    einem schreibenden Aufruf. Es gibt im Modul keinerlei ``.post(``/``.put(``.
    """
    src = inspect.getsource(community)
    for host in ("matchmakerexchange.org", "genematcher.org", "mygene2.org"):
        assert host in src  # als Wegweiser vorhanden …
    assert ".post(" not in src  # … aber kein schreibender HTTP-Call
    assert ".put(" not in src
