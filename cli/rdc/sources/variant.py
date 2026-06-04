"""Varianten-Quelle: MyVariant.info (ClinVar-Pathogenität + gnomAD-Frequenz).

Eine Typer-Subkommando-Gruppe, die sich über die Registry aus CLI-01 in ``rdc``
einhängt:

- ``rdc variant lookup <variant>`` — Pathogenität (ClinVar) **und** Allelfrequenz
  (gnomAD exome/genome) zu einer Variante.
- ``rdc variant clinvar <variant>`` — fokussiert auf die ClinVar-Sicht (Signifikanz,
  Review-Status, Condition(s), RCV-IDs).

Aufbau-Disziplin:

- **Kein eigener HTTP-Stack.** Aller Netzwerkverkehr läuft über den zentralen
  :class:`~rdc.http_client.HttpClient` (Cache, Rate-Limit, Retry, User-Agent).
- **Reine Funktionen** bilden Query-Params (``*_params``) und parsen Responses
  (``parse_*``) — beide ohne HTTP-Call, damit Tests sie ohne Netzwerk prüfen.
- **Defensiv lesen.** MyVariant-Responses sind tief verschachtelt und je nach
  Variante unterschiedlich besetzt. Fehlende Schlüssel führen nie zum Crash
  (VUS ohne Frequenz, Variante ohne ClinVar-Eintrag → definierter Leerwert).
- **Keine Diagnose-Sprache.** Ausgegeben werden nur Datenbank-Fakten (Signifikanz,
  Frequenz, Quellen-IDs) — die klinische Einordnung übernimmt der Mensch.

Der optionale ``MYVARIANT_API_KEY`` (Env) wird nur als Query-Param angehängt —
**nie** geloggt oder in der History gespeichert.
"""

from __future__ import annotations

import os
import sqlite3
from typing import Any

import typer

from .. import history
from ..http_client import HttpClient

MYVARIANT_API_KEY_ENV = "MYVARIANT_API_KEY"

# MyVariant.info v1: Annotation per Variant-ID (HGVS) und die Query-API (z. B. rsID).
MYVARIANT_VARIANT_URL = "https://myvariant.info/v1/variant"
MYVARIANT_QUERY_URL = "https://myvariant.info/v1/query"

# Definierter Leerwert für fehlende Felder (statt None/Crash).
EMPTY = ""

# Default-Feldsatz fürs ClinVar-fokussierte Kommando (schlankere Response).
CLINVAR_FIELDS = "clinvar,dbsnp"

LOOKUP_HEADERS = [
    "id",
    "variant_id",
    "gene",
    "rsid",
    "clinical_significance",
    "gnomad_exome_af",
    "gnomad_genome_af",
    "rcv",
]
CLINVAR_HEADERS = [
    "id",
    "variant_id",
    "gene",
    "clinical_significance",
    "review_status",
    "conditions",
    "rcv",
]


# -- Eingabe-Erkennung + Query-Param-Bildung (reine Funktionen, ohne HTTP) -


def is_rsid(variant: str) -> bool:
    """Ob ``variant`` eine dbSNP-rsID ist (``rs`` + Ziffern)."""
    token = variant.strip().lower()
    return token.startswith("rs") and token[2:].isdigit() and len(token) > 2


def variant_lookup_params(
    fields: str | None = None,
    api_key: str | None = None,
) -> dict[str, object]:
    """Params für die Annotation per Variant-ID (``/v1/variant/<id>``)."""
    params: dict[str, object] = {}
    if fields:
        params["fields"] = fields
    if api_key:
        params["api_key"] = api_key
    return params


def variant_query_params(
    variant: str,
    fields: str | None = None,
    api_key: str | None = None,
) -> dict[str, object]:
    """Params für die Query-API (``/v1/query?q=...``), z. B. rsID-Lookup."""
    params: dict[str, object] = {"q": variant}
    if fields:
        params["fields"] = fields
    if api_key:
        params["api_key"] = api_key
    return params


# -- Response-Parsing (reine Funktionen, ohne HTTP) -----------------------


def _as_list(value: object) -> list[Any]:
    """Normalisiert ein Feld, das einzeln **oder** als Liste kommen kann."""
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _join_unique(values: list[str]) -> str:
    """Fügt nicht-leere Werte ordnungserhaltend und dedupliziert zusammen."""
    seen: list[str] = []
    for value in values:
        if value and value not in seen:
            seen.append(value)
    return "; ".join(seen)


def _has_payload(hit: object) -> bool:
    """Ob ein Treffer die gesuchten Annotationsblöcke (ClinVar/gnomAD) trägt."""
    if not isinstance(hit, dict):
        return False
    return any(
        key in hit for key in ("clinvar", "gnomad_exome", "gnomad_genome")
    )


def _pick_hit(hits: list[Any]) -> dict[str, Any]:
    """Wählt aus mehreren Query-Treffern den datentragenden.

    MyVariant liefert für eine rsID oft mehrere Repräsentationen derselben
    Variante (del/dup/abweichende Normalisierung); nur eine trägt den ClinVar-/
    gnomAD-Block. Blind ``hits[0]`` zu nehmen lieferte für bekannt pathogene
    Varianten leere Felder. Wir nehmen daher den ersten Treffer **mit** Payload,
    sonst den ersten überhaupt (Fallback).
    """
    for hit in hits:
        if _has_payload(hit):
            return hit  # type: ignore[return-value]
    first = hits[0] if hits else {}
    return first if isinstance(first, dict) else {}


def as_variant(data: object) -> dict[str, Any]:
    """Holt das Variant-Objekt aus einer MyVariant-Antwort.

    Die Annotation-API liefert das Objekt direkt (oder eine Liste), die
    Query-API verpackt Treffer unter ``hits``. Bei mehreren Treffern wird der
    datentragende gewählt (siehe :func:`_pick_hit`). Fehlt alles, ist es ``{}``.
    """
    if isinstance(data, list):
        return _pick_hit(data)
    if isinstance(data, dict):
        hits = data.get("hits")
        if isinstance(hits, list):
            return _pick_hit(hits)
        return data
    return {}


def _clinvar_block(data: dict[str, Any]) -> dict[str, Any]:
    block = data.get("clinvar") if isinstance(data, dict) else None
    return block if isinstance(block, dict) else {}


def _rsid(data: dict[str, Any]) -> str:
    dbsnp = data.get("dbsnp") if isinstance(data, dict) else None
    if isinstance(dbsnp, dict):
        rsid = dbsnp.get("rsid")
        if rsid:
            return str(rsid)
    return EMPTY


def parse_clinvar(data: dict[str, Any]) -> dict[str, str]:
    """ClinVar-Sicht: Signifikanz, Review-Status, Conditions, RCV-IDs, Gen.

    Tolerant gegenüber fehlendem ClinVar-Block und gegenüber ``rcv`` als
    Einzel-Objekt oder Liste.
    """
    clinvar = _clinvar_block(data)
    significances: list[str] = []
    review_statuses: list[str] = []
    accessions: list[str] = []
    conditions: list[str] = []
    for rcv in _as_list(clinvar.get("rcv")):
        if not isinstance(rcv, dict):
            continue
        if sig := rcv.get("clinical_significance"):
            significances.append(str(sig))
        if status := rcv.get("review_status"):
            review_statuses.append(str(status))
        if accession := rcv.get("accession"):
            accessions.append(str(accession))
        for cond in _as_list(rcv.get("conditions")):
            if isinstance(cond, dict):
                if name := cond.get("name"):
                    conditions.append(str(name))
            elif cond:
                conditions.append(str(cond))
    gene = EMPTY
    gene_block = clinvar.get("gene")
    if isinstance(gene_block, dict) and gene_block.get("symbol"):
        gene = str(gene_block["symbol"])
    variant_id = clinvar.get("variant_id")
    return {
        "clinical_significance": _join_unique(significances),
        "review_status": _join_unique(review_statuses),
        "rcv": _join_unique(accessions),
        "conditions": _join_unique(conditions),
        "gene": gene,
        "variant_id": str(variant_id) if variant_id is not None else EMPTY,
    }


def parse_frequency(data: dict[str, Any]) -> dict[str, object]:
    """gnomAD-Allelfrequenz (exome **und** genome getrennt).

    Fehlt eine Quelle, steht dort der definierte Leerwert :data:`EMPTY` statt
    eines Crashes — beide werden ausgegeben, keine wird stillschweigend gewählt.
    """

    def _af(section: str) -> object:
        block = data.get(section) if isinstance(data, dict) else None
        block = block if isinstance(block, dict) else {}
        af = block.get("af")
        af = af if isinstance(af, dict) else {}
        value = af.get("af")
        return value if value is not None else EMPTY

    return {
        "gnomad_exome_af": _af("gnomad_exome"),
        "gnomad_genome_af": _af("gnomad_genome"),
    }


def parse_variant(data: dict[str, Any]) -> dict[str, object]:
    """Kompakter Lookup-Record: ClinVar-Pathogenität + gnomAD-Frequenz."""
    clinvar = parse_clinvar(data)
    frequency = parse_frequency(data)
    return {
        "id": str(data.get("_id", EMPTY)) if isinstance(data, dict) else EMPTY,
        "variant_id": clinvar["variant_id"],
        "gene": clinvar["gene"],
        "rsid": _rsid(data),
        "clinical_significance": clinvar["clinical_significance"],
        "review_status": clinvar["review_status"],
        "conditions": clinvar["conditions"],
        "rcv": clinvar["rcv"],
        "gnomad_exome_af": frequency["gnomad_exome_af"],
        "gnomad_genome_af": frequency["gnomad_genome_af"],
    }


def parse_clinvar_record(data: dict[str, Any]) -> dict[str, object]:
    """ClinVar-fokussierter Record (für ``rdc variant clinvar``)."""
    clinvar = parse_clinvar(data)
    return {
        "id": str(data.get("_id", EMPTY)) if isinstance(data, dict) else EMPTY,
        "variant_id": clinvar["variant_id"],
        "gene": clinvar["gene"],
        "rsid": _rsid(data),
        "clinical_significance": clinvar["clinical_significance"],
        "review_status": clinvar["review_status"],
        "conditions": clinvar["conditions"],
        "rcv": clinvar["rcv"],
    }


# -- Kernlogik (Client + Connection injiziert) ----------------------------


def _fetch_variant(
    client: HttpClient,
    variant: str,
    fields: str | None,
    api_key: str | None,
) -> dict[str, Any]:
    """Holt das rohe Variant-Objekt — rsID über die Query-API, sonst direkt."""
    if is_rsid(variant):
        response = client.get(
            MYVARIANT_QUERY_URL,
            params=variant_query_params(variant, fields, api_key),
        )
    else:
        response = client.get(
            f"{MYVARIANT_VARIANT_URL}/{variant}",
            params=variant_lookup_params(fields, api_key),
        )
    return as_variant(response.json())


def run_variant_lookup(
    client: HttpClient,
    conn: sqlite3.Connection,
    *,
    variant: str,
    fields: str | None = None,
    api_key: str | None = None,
) -> list[dict[str, object]]:
    """Lookup (ClinVar + gnomAD) und protokolliert die Abfrage."""
    record = parse_variant(_fetch_variant(client, variant, fields, api_key))
    sig = record["clinical_significance"] or "keine ClinVar-Signifikanz"
    exome = record["gnomad_exome_af"]
    summary = f"ClinVar: {sig}; gnomAD exome af={exome if exome != EMPTY else '—'}"
    history.save_query(
        conn,
        source="variant",
        command="lookup",
        params={"variant": variant, "fields": fields},
        result_summary=summary,
        result_count=1,
        raw=record,
    )
    return [record]


def run_variant_clinvar(
    client: HttpClient,
    conn: sqlite3.Connection,
    *,
    variant: str,
    fields: str | None = None,
    api_key: str | None = None,
) -> list[dict[str, object]]:
    """ClinVar-fokussierter Lookup und protokolliert die Abfrage."""
    fields_eff = fields or CLINVAR_FIELDS
    record = parse_clinvar_record(
        _fetch_variant(client, variant, fields_eff, api_key)
    )
    sig = record["clinical_significance"] or "kein ClinVar-Eintrag"
    history.save_query(
        conn,
        source="clinvar",
        command="clinvar",
        params={"variant": variant, "fields": fields_eff},
        result_summary=f"ClinVar: {sig}",
        result_count=1,
        raw=record,
    )
    return [record]


def _api_key() -> str | None:
    return os.environ.get(MYVARIANT_API_KEY_ENV) or None


# -- Typer-Befehle (verdrahten Client/History und rendern) ----------------

variant_app = typer.Typer(
    help="MyVariant.info: ClinVar-Pathogenität und gnomAD-Allelfrequenz.",
    no_args_is_help=True,
)


@variant_app.command("lookup")
def variant_lookup(
    variant: str = typer.Argument(
        ..., help="Variante als HGVS (chr7:g.140453136A>T) oder rsID (rs113488022)."
    ),
    fields: str | None = typer.Option(
        None, "--fields", help="MyVariant-Feldauswahl durchreichen (kommagetrennt)."
    ),
    json_: bool = typer.Option(False, "--json", help="Ausgabe als JSON-Lines."),
) -> None:
    """Pathogenität (ClinVar) und Allelfrequenz (gnomAD) zu einer Variante."""
    from rdc import main

    with HttpClient() as client:
        conn = history.connect(history.default_db_path())
        records = run_variant_lookup(
            client, conn, variant=variant, fields=fields, api_key=_api_key()
        )
    main.render(
        records,
        LOOKUP_HEADERS,
        json_override=json_,
        empty="(kein Treffer)",
    )


@variant_app.command("clinvar")
def variant_clinvar(
    variant: str = typer.Argument(
        ..., help="Variante als HGVS oder rsID."
    ),
    fields: str | None = typer.Option(
        None, "--fields", help="MyVariant-Feldauswahl überschreiben (kommagetrennt)."
    ),
    json_: bool = typer.Option(False, "--json", help="Ausgabe als JSON-Lines."),
) -> None:
    """ClinVar-Sicht: Signifikanz, Review-Status, Condition(s), RCV-IDs."""
    from rdc import main

    with HttpClient() as client:
        conn = history.connect(history.default_db_path())
        records = run_variant_clinvar(
            client, conn, variant=variant, fields=fields, api_key=_api_key()
        )
    main.render(
        records,
        CLINVAR_HEADERS,
        json_override=json_,
        empty="(kein ClinVar-Eintrag)",
    )
