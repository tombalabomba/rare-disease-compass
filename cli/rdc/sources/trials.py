"""Klinische-Studien-Quelle: ClinicalTrials.gov API v2.

Eine Typer-Subkommando-Gruppe, die sich über die Registry aus CLI-01 als Gruppe
``rdc trials`` einhängt:

- ``rdc trials search <begriff>`` — Studien zu einer Krankheit/einem Gen über die
  **ClinicalTrials.gov API v2** (``https://clinicaltrials.gov/api/v2/studies``,
  JSON, keine Auth). Optionen ``--recruiting`` (nur aktiv rekrutierende),
  ``--country <land>`` und ``--limit``.

Rekrutierende Studien sind ein doppelter Hebel: ein Weg zu spezialisierten
Zentren und zu anderen Betroffenen. Pro Studie wird die **NCT-ID als klickbarer
Link** (``clinicaltrials.gov/study/<NCT>``) plus Titel, Status, Phase und ein
knapper Orts-/Land-Auszug ausgegeben.

Aufbau-Disziplin (analog ``literature.py``):

- **Kein eigener HTTP-Stack.** Aller Netzwerkverkehr läuft über den zentralen
  :class:`~rdc.http_client.HttpClient`.
- **Reine Funktionen** bilden Query-Params (``*_params``) und parsen Responses
  (``parse_*``) — beide ohne HTTP-Call, damit Tests sie ohne Netzwerk prüfen.
- **Dependency-Injection:** die ``run_*``-Kernfunktion bekommt Client und
  History-Connection übergeben; Tests speisen einen ``MockTransport``-Client und
  eine in-memory-History ein.
- **Datenschutz:** die History speichert nur die **Abfrage** (Suchbegriff +
  Filter), niemals personenbezogene Daten — die Abfrage führt keine PII mit.
"""

from __future__ import annotations

import sqlite3

import typer

from .. import history
from ..http_client import HttpClient

# ClinicalTrials.gov v2 Studies-Endpunkt (öffentlich, kein Key).
STUDIES_URL = "https://clinicaltrials.gov/api/v2/studies"
# Klickbare Detailseite je Studie.
STUDY_BASE_URL = "https://clinicaltrials.gov/study"

# Status-Wert für aktiv rekrutierende Studien (filter.overallStatus).
RECRUITING_STATUS = "RECRUITING"

# Nur die für die Tabelle benötigten Felder anfordern (knappe Payload).
STUDY_FIELDS = [
    "NCTId",
    "BriefTitle",
    "OverallStatus",
    "Phase",
    "LocationCountry",
    "LocationCity",
    "LocationFacility",
]

STUDIES_HEADERS = ["nct", "status", "phase", "locations", "title", "url"]


# -- Reine Funktionen (URLs/Params/Parsing, ohne HTTP) --------------------


def study_url(nct: str) -> str:
    """Klickbare ClinicalTrials.gov-Detail-URL zu einer NCT-ID."""
    return f"{STUDY_BASE_URL}/{nct}"


def studies_search_params(
    term: str,
    *,
    recruiting: bool = False,
    country: str | None = None,
    limit: int = 20,
) -> dict[str, object]:
    """ClinicalTrials.gov-v2-``/studies``-Params für eine Studiensuche.

    ``--recruiting`` setzt ``filter.overallStatus=RECRUITING``; ``--country``
    schränkt über das Standort-Feld (``query.locn``) ein. ``countTotal`` liefert
    die Gesamttrefferzahl für die Zusammenfassung.
    """
    params: dict[str, object] = {
        "query.cond": term,
        "pageSize": limit,
        "countTotal": "true",
        "fields": ",".join(STUDY_FIELDS),
    }
    if recruiting:
        params["filter.overallStatus"] = RECRUITING_STATUS
    if country:
        params["query.locn"] = country
    return params


def summarize_locations(locations: object, max_n: int = 2) -> str:
    """Knapper Orts-Auszug: ``Stadt, Land`` der ersten ``max_n`` Standorte.

    Bewusst kurz gehalten (Notes COM-02): nicht die volle Standortliste, sonst
    wird die Tabelle unübersichtlich. Bei mehr Standorten wird ``(+N)`` angehängt.
    """
    if not isinstance(locations, list):
        return ""
    parts: list[str] = []
    for loc in locations:
        loc = loc if isinstance(loc, dict) else {}
        city = str(loc.get("city", "")).strip()
        country = str(loc.get("country", "")).strip()
        label = ", ".join(p for p in (city, country) if p)
        if label and label not in parts:
            parts.append(label)
        if len(parts) >= max_n:
            break
    total = len(locations)
    summary = "; ".join(parts)
    if total > len(parts) and summary:
        summary += f" (+{total - len(parts)})"
    return summary


def parse_studies(data: object) -> dict[str, object]:
    """ClinicalTrials.gov-v2-JSON → ``{"total": int, "records": [...]}``.

    Jeder Record trägt die NCT-ID **und** den vollständigen ``study_url``-Link;
    nackte IDs gibt es bewusst nicht.
    """
    data = data if isinstance(data, dict) else {}
    studies = data.get("studies", [])
    records: list[dict[str, str]] = []
    for study in studies if isinstance(studies, list) else []:
        study = study if isinstance(study, dict) else {}
        section = study.get("protocolSection", {})
        section = section if isinstance(section, dict) else {}

        ident = section.get("identificationModule", {})
        ident = ident if isinstance(ident, dict) else {}
        nct = str(ident.get("nctId", ""))

        status_module = section.get("statusModule", {})
        status_module = status_module if isinstance(status_module, dict) else {}

        design = section.get("designModule", {})
        design = design if isinstance(design, dict) else {}
        phases = design.get("phases", [])
        phase = ", ".join(
            str(p) for p in phases if p
        ) if isinstance(phases, list) else ""

        contacts = section.get("contactsLocationsModule", {})
        contacts = contacts if isinstance(contacts, dict) else {}

        records.append(
            {
                "nct": nct,
                "url": study_url(nct),
                "title": str(ident.get("briefTitle", "")),
                "status": str(status_module.get("overallStatus", "")),
                "phase": phase,
                "locations": summarize_locations(contacts.get("locations", [])),
            }
        )
    try:
        total = int(data.get("totalCount", len(records)))
    except (TypeError, ValueError):
        total = len(records)
    return {"total": total, "records": records}


# -- Kernlogik (Client + Connection injiziert) ----------------------------


def run_studies_search(
    client: HttpClient,
    conn: sqlite3.Connection,
    *,
    term: str,
    recruiting: bool = False,
    country: str | None = None,
    limit: int = 20,
) -> list[dict[str, str]]:
    """Sucht Studien auf ClinicalTrials.gov und protokolliert die Suche."""
    response = client.get(
        STUDIES_URL,
        params=studies_search_params(
            term, recruiting=recruiting, country=country, limit=limit
        ),
    )
    parsed = parse_studies(response.json())
    records: list[dict[str, str]] = parsed["records"]  # type: ignore[assignment]
    history.save_query(
        conn,
        source="trials",
        command="search",
        params={
            "term": term,
            "recruiting": recruiting,
            "country": country,
            "limit": limit,
        },
        result_summary=f"{len(records)} von {parsed['total']} Studien",
        result_count=len(records),
        raw=records,
    )
    return records


# -- Typer-Befehle (verdrahten Client/History und rendern) ----------------

trials_app = typer.Typer(
    help="Klinische Studien (ClinicalTrials.gov): Studiensuche zu Krankheit/Gen.",
    no_args_is_help=True,
)


@trials_app.command("search")
def search(
    query: str = typer.Argument(
        ..., help="Krankheit oder Gen (ClinicalTrials.gov-Condition-Suche)."
    ),
    recruiting: bool = typer.Option(
        False, "--recruiting", help="Nur aktiv rekrutierende Studien."
    ),
    country: str | None = typer.Option(
        None, "--country", help="Auf Studien mit Standort in diesem Land einschränken."
    ),
    limit: int = typer.Option(20, "--limit", help="Maximale Trefferzahl."),
    json_: bool = typer.Option(False, "--json", help="Ausgabe als JSON-Lines."),
) -> None:
    """Sucht klinische Studien (NCT-ID als Link, Titel, Status, Phase, Orte)."""
    from rdc import main

    with HttpClient() as client:
        conn = history.connect(history.default_db_path())
        records = run_studies_search(
            client,
            conn,
            term=query,
            recruiting=recruiting,
            country=country,
            limit=limit,
        )
    main.render(
        records,
        STUDIES_HEADERS,
        json_override=json_,
        empty="(keine Studien)",
    )
