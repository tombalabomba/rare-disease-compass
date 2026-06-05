"""Community-Quelle: Patientenorganisationen + RareConnect-Communities.

Zwei Typer-Subkommandos, die sich über die Registry aus CLI-01 als Gruppe
``rdc community`` einhängen:

- ``rdc community orgs <disease|ORPHAcode|MONDO>`` — **Patientenorganisationen**
  zu einer Krankheit. Auflösung der Krankheit (Name + ORPHA-Code) läuft über den
  bereits angebundenen Orphadata-``rd-cross-referencing``-Pfad (Single source of
  truth: die reinen Helfer aus :mod:`rdc.sources.graph`). Ausgegeben werden
  **klickbare Wegweiser** zu den autoritativen Organisations-Verzeichnissen für
  genau diese Krankheit (Orphanet-Disease-Seite mit assoziierten
  Patientenorganisationen + professionellen Ressourcen).
- ``rdc community rareconnect <disease|ORPHAcode>`` — die passende **RareConnect**-
  Community (EURORDIS). RareConnect ist eine reine SPA **ohne Daten-API und ohne
  maschinenlesbare Community-Liste** (siehe ``AGENTS.md``); Slugs sind
  serverseitig nicht verifizierbar. Deshalb als **Wegweiser**: immer die stabile
  Communities-Browse-URL plus eine aus dem Krankheitsnamen abgeleitete
  **Kandidaten**-URL, die ausdrücklich als „candidate" markiert ist — nie wird
  behauptet, eine Community existiere, ohne dass ein anklickbarer Link dabei ist.

Aufbau-Disziplin (analog ``graph.py``):

- **Kein eigener HTTP-Stack.** Aller Netzwerkverkehr läuft über den zentralen
  :class:`~rdc.http_client.HttpClient`.
- **Reine Funktionen** bilden URLs/Slugs und Ergebnis-Zeilen ohne HTTP-Call,
  damit Tests sie ohne Netzwerk prüfen.
- **Datenschutz:** die History speichert nur die **Abfrage** (Krankheit/ORPHA),
  niemals personenbezogene Daten.
- **Keine erfundenen Organisationen.** Es gibt keinen freien API-Datensatz mit
  Org-Namen/Ländern (``api.orphadata.com`` führt keinen, ``en_product8.xml`` ist
  404). Statt zu fabrizieren, verweist die Quelle auf die autoritativen
  Verzeichnisse — jede Zeile mit vollständigem ``http(s)://``-Link.
"""

from __future__ import annotations

import os
import sqlite3

import typer

from .. import history
from ..http_client import HttpClient
from . import graph

# -- Stabile, verifizierte Wegweiser-URLs ---------------------------------

# Orphanet-Disease-Seite: listet je Krankheit die assoziierten
# Patientenorganisationen + professionellen Ressourcen (verifiziert: 200).
ORPHANET_DISEASE_URL = "https://www.orpha.net/en/disease/detail"
# Fallback-Index, wenn die Krankheit nicht zu einem ORPHA-Code auflöst.
ORPHANET_DISEASE_INDEX_URL = "https://www.orpha.net/en/disease"

# RareConnect (EURORDIS): reine SPA, keine API/Sitemap.
RARECONNECT_COMMUNITIES_URL = "https://www.rareconnect.org/en/communities"
RARECONNECT_COMMUNITY_URL = "https://www.rareconnect.org/en/community"

ORGS_HEADERS = ["name", "scope", "url"]
RARECONNECT_HEADERS = ["community", "type", "url"]

# -- Genetisches Matching: statische Wegweiser (COM-03) --------------------
#
# Stand 2026-06-06, Links beim Schreiben geprüft. Bewusst **kein** API-Zugriff:
# Matching-Netze nehmen Gen-/Symptomdaten eines Kindes ENTGEGEN — eine
# einwilligungs-gegatete Entscheidung, die über die Humangenetik läuft. RDC
# reicht nichts ein und überträgt keine Daten; dieser Befehl ist ein reiner
# Info-/Wegweiser-Befehl (siehe docs/connect-genetic-matching.md).

# Verbund-Knoten des Matchmaker Exchange (live 2026): Einreichung über Klinik.
MATCHMAKER_EXCHANGE_URL = "https://www.matchmakerexchange.org/"
MATCHMAKER_PARTICIPANTS_URL = "https://www.matchmakerexchange.org/participants.html"
GENEMATCHER_URL = "https://genematcher.org/"
# Familien teilen selbst offen.
MYGENE2_URL = "https://www.mygene2.org/"

MATCHMAKING_HEADERS = ["resource", "audience", "url"]

# Hinweis-Block, nur im Tabellen-Modus ausgegeben (JSON bleibt sauber).
MATCHMAKING_NOTE = (
    "Hinweis: RDC reicht nichts ein und überträgt keine Daten an diese Netze. "
    "Eine Einreichung übermittelt Gen-/Symptomdaten (oft eines Kindes) — eine "
    "bewusste Einwilligungs-Entscheidung der Sorgeberechtigten, üblicherweise "
    "über die Humangenetik/behandelnde Klinik. Details, Einwilligung und "
    "Datenschutz: docs/connect-genetic-matching.md, docs/consent-template.md, "
    "docs/security.md."
)


def matchmaking_rows() -> list[dict[str, object]]:
    """Statische Wegweiser-Zeilen zum genetischen Matching (ohne HTTP).

    Jede Zeile trägt einen vollständigen ``https://``-Link. Reihenfolge: zuerst
    der übliche Weg über die Humangenetik (Matchmaker Exchange + GeneMatcher),
    dann der Selbst-Teil-Weg für Familien (MyGene2).
    """
    return [
        {
            "resource": "Matchmaker Exchange — Verbund, Einreichung über die "
            "Humangenetik/Klinik",
            "audience": "Kliniker:innen / Forschende",
            "url": MATCHMAKER_EXCHANGE_URL,
        },
        {
            "resource": "Matchmaker Exchange — teilnehmende Knoten "
            "(GeneMatcher, DECIPHER, PhenomeCentral, MyGene2 …)",
            "audience": "Kliniker:innen / Forschende",
            "url": MATCHMAKER_PARTICIPANTS_URL,
        },
        {
            "resource": "GeneMatcher — gen-basiertes Matching, Einreichung "
            "durch Ärzt:innen",
            "audience": "Kliniker:innen / Forschende",
            "url": GENEMATCHER_URL,
        },
        {
            "resource": "MyGene2 — für Familien, die selbst offen teilen wollen",
            "audience": "Familien (Selbst-Einreichung)",
            "url": MYGENE2_URL,
        },
    ]


# -- Reine Funktionen (URLs/Slugs/Zeilen, ohne HTTP) ----------------------


def orphanet_disease_url(code: str) -> str:
    """Klickbare Orphanet-Disease-URL zu einem ORPHA-Code."""
    return f"{ORPHANET_DISEASE_URL}/{code}"


def slugify_disease(name: str) -> str:
    """Krankheitsname → RareConnect-Slug-Kandidat.

    ``Marfan syndrome`` → ``marfan-syndrome``.
    Lowercase, jede nicht-alphanumerische Folge wird zu **einem** Bindestrich,
    führende/abschließende Bindestriche entfallen. Liefert ``""`` für leere oder
    rein nicht-alphanumerische Eingaben.
    """
    out: list[str] = []
    prev_hyphen = False
    for ch in (name or "").strip().lower():
        if ch.isalnum():
            out.append(ch)
            prev_hyphen = False
        elif out and not prev_hyphen:
            out.append("-")
            prev_hyphen = True
    return "".join(out).strip("-")


def rareconnect_community_url(slug: str) -> str:
    """Klickbare RareConnect-Community-URL zu einem Slug."""
    return f"{RARECONNECT_COMMUNITY_URL}/{slug}"


def orgs_rows(orpha: str, name: str, term: str) -> list[dict[str, object]]:
    """Wegweiser-Zeilen zu den Organisations-Verzeichnissen einer Krankheit.

    Bei aufgelöstem ORPHA-Code: Deep-Link auf die Orphanet-Disease-Seite (dort
    sind die assoziierten Patientenorganisationen gelistet). Sonst: Wegweiser auf
    den Orphanet-Krankheitsindex mit der Suchanfrage als Kontext. Jede Zeile
    trägt einen vollständigen ``http(s)://``-Link.
    """
    if orpha:
        label = name or term
        return [
            {
                "name": f"Orphanet — assoziierte Patientenorganisationen: {label}",
                "scope": "EU",
                "url": orphanet_disease_url(orpha),
            }
        ]
    return [
        {
            "name": f"Orphanet — Krankheitssuche (kein ORPHA-Treffer für: {term})",
            "scope": "EU",
            "url": ORPHANET_DISEASE_INDEX_URL,
        }
    ]


def rareconnect_rows(name: str, term: str) -> list[dict[str, object]]:
    """Wegweiser-Zeilen zu RareConnect: immer Browse-URL, optional Kandidat.

    Die Browse-URL ist garantiert gültig und steht **immer** an erster Stelle.
    Lässt sich aus dem Krankheitsnamen ein Slug bilden, kommt eine als
    ``candidate`` markierte Community-URL hinzu — sie wird **nicht** als sicher
    existierend behauptet, ist aber direkt anklickbar.
    """
    rows: list[dict[str, object]] = [
        {
            "community": "RareConnect — alle Communities durchsuchen",
            "type": "browse",
            "url": RARECONNECT_COMMUNITIES_URL,
        }
    ]
    slug = slugify_disease(name or term)
    if slug:
        rows.append(
            {
                "community": f"RareConnect — Community-Kandidat: {name or term}",
                "type": "candidate",
                "url": rareconnect_community_url(slug),
            }
        )
    return rows


# -- Kernlogik (Client + Connection injiziert) ----------------------------


def resolve_disease(
    client: HttpClient,
    term: str,
    *,
    lang: str = "en",
    api_key: str | None = None,
) -> dict[str, object]:
    """Krankheit → Orphanet-Record (ORPHA-Code + Name) über rd-cross-referencing.

    Nutzt die reinen Helfer aus :mod:`rdc.sources.graph` (Single source of truth
    für den Orphanet-Zugang). ORPHA-Code-Eingaben werden per Code aufgelöst, alles
    andere (inkl. MONDO-IDs/Freitext) per Name; bleibt der Treffer leer, kommt ein
    Record mit leeren Feldern zurück (kein Crash).
    """
    code = graph.orpha_code_of(term)
    if code is not None:
        url = graph.orphanet_code_url(code)
    else:
        url = graph.orphanet_name_url(term)
    response = client.get(url, params=graph.orphanet_params(lang, api_key))
    return graph.parse_orphanet(response.json())


def run_orgs(
    client: HttpClient,
    conn: sqlite3.Connection,
    *,
    term: str,
    lang: str = "en",
    api_key: str | None = None,
) -> list[dict[str, object]]:
    """Patientenorganisationen-Wegweiser zu einer Krankheit + History-Eintrag."""
    record = resolve_disease(client, term, lang=lang, api_key=api_key)
    orpha = str(record.get("orpha") or "")
    name = str(record.get("name") or "")
    rows = orgs_rows(orpha, name, term)
    history.save_query(
        conn,
        source="community",
        command="orgs",
        params={"term": term, "lang": lang},
        result_summary=f"Orgs-Wegweiser für {name or term} "
        f"(ORPHA {orpha or '—'})",
        result_count=len(rows),
        raw=rows,
    )
    return rows


def run_rareconnect(
    client: HttpClient,
    conn: sqlite3.Connection,
    *,
    term: str,
    lang: str = "en",
    api_key: str | None = None,
) -> list[dict[str, object]]:
    """RareConnect-Wegweiser zu einer Krankheit (immer mind. eine URL) + History.

    Bei ORPHA-Code-/Namens-Eingabe wird zuerst der kanonische Krankheitsname
    aufgelöst, damit der Slug-Kandidat möglichst trifft; schlägt das fehl, dient
    der Eingabe-Term als Basis.
    """
    record = resolve_disease(client, term, lang=lang, api_key=api_key)
    name = str(record.get("name") or "")
    orpha = str(record.get("orpha") or "")
    rows = rareconnect_rows(name, term)
    history.save_query(
        conn,
        source="community",
        command="rareconnect",
        params={"term": term, "lang": lang},
        result_summary=f"RareConnect-Wegweiser für {name or term} "
        f"(ORPHA {orpha or '—'})",
        result_count=len(rows),
        raw=rows,
    )
    return rows


def _api_key() -> str | None:
    return os.environ.get(graph.ORPHANET_API_KEY_ENV) or None


# -- Typer-Befehle (verdrahten Client/History und rendern) ----------------

community_app = typer.Typer(
    help="Community: Patientenorganisationen + RareConnect-Communities (Wegweiser).",
    no_args_is_help=True,
)


@community_app.command("orgs")
def orgs(
    disease: str = typer.Argument(
        ..., help="Krankheit als Name, ORPHA-Code (558 / ORPHA:558) oder MONDO-ID."
    ),
    lang: str = typer.Option("en", "--lang", help="Sprachcode der Orphadata-Antwort."),
    json_: bool = typer.Option(False, "--json", help="Ausgabe als JSON-Lines."),
) -> None:
    """Patientenorganisationen zu einer Krankheit (klickbare Wegweiser)."""
    from rdc import main

    with HttpClient() as client:
        conn = history.connect(history.default_db_path())
        rows = run_orgs(client, conn, term=disease, lang=lang, api_key=_api_key())
    main.render(
        rows,
        ORGS_HEADERS,
        json_override=json_,
        empty="(kein Organisations-Wegweiser)",
    )


@community_app.command("rareconnect")
def rareconnect(
    disease: str = typer.Argument(
        ..., help="Krankheit als Name oder ORPHA-Code (558 / ORPHA:558)."
    ),
    lang: str = typer.Option("en", "--lang", help="Sprachcode der Orphadata-Antwort."),
    json_: bool = typer.Option(False, "--json", help="Ausgabe als JSON-Lines."),
) -> None:
    """RareConnect-Community zu einer Krankheit (immer mit klickbarem Link)."""
    from rdc import main

    with HttpClient() as client:
        conn = history.connect(history.default_db_path())
        rows = run_rareconnect(
            client, conn, term=disease, lang=lang, api_key=_api_key()
        )
    main.render(
        rows,
        RARECONNECT_HEADERS,
        json_override=json_,
        empty="(kein RareConnect-Wegweiser)",
    )


@community_app.command("matchmaking")
def matchmaking(
    json_: bool = typer.Option(False, "--json", help="Ausgabe als JSON-Lines."),
) -> None:
    """Wegweiser zum genetischen Matching (MME/GeneMatcher/MyGene2) — offline.

    Reiner Info-Befehl: kein Netzwerk-Aufruf, keine Datenübertragung. Gibt die
    Wegweiser-Links aus; im Tabellen-Modus zusätzlich den Einwilligungs-Hinweis.
    """
    from rdc import main

    rows = matchmaking_rows()
    main.render(rows, MATCHMAKING_HEADERS, json_override=json_)
    is_jsonl = json_ or main._state["format"] is main.OutputFormat.jsonl
    if not is_jsonl:
        typer.echo("")
        typer.echo(MATCHMAKING_NOTE)
