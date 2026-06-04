#!/usr/bin/env python3
"""Exomiser-Ergebnis → Fallakten-Markdown-Konverter.

Liest einen Exomiser-Ergebnis-Output (TSV primär, JSON optional) und erzeugt die
Sektion ``## Genetik-Zusammenfassung`` im Format des Fallakten-Templates
(``docs/case-file-TEMPLATE.md``) — eine kuratierte Top-N-Kandidaten-Tabelle mit
medizinischem Disclaimer.

Datenschutz: Es fließt **nur** das kuratierte Ergebnis in die Akte. Keine
vollständige Variantenliste, keine Rohgenom-/Roh-VCF-Zeilen. Das Skript liest
ausschließlich den übergebenen Pfad und schreibt selbst **keine** Patientendatei —
das Markdown geht auf stdout, das Einsetzen in die (lokale, gitignored) Akte ist
ein manueller Schritt des Kurators.
"""

import argparse
import json
import sys
from dataclasses import dataclass

# Exakt die Überschrift aus KB-01 (docs/case-file-TEMPLATE.md). Single source of
# truth — wird hier 1:1 reproduziert, damit die Sektion an der richtigen Stelle
# eingefügt werden kann.
SECTION_HEADING = "## Genetik-Zusammenfassung"

# Tabellen-Spalten der kuratierten Ausgabe (Reihenfolge ist Teil des Vertrags).
TABLE_COLUMNS = (
    "Gen",
    "Variante",
    "ClinVar-Bedeutung",
    "Häufigkeit",
    "Phänotyp-Score",
    "Quelle",
)

# Platzhalter für fehlende Werte in der Tabelle.
NA = "n. v."

# Default-Quelle pro Kandidat.
SOURCE_LABEL = "Exomiser"

DISCLAIMER = (
    "> **Hinweis – keine Diagnose:** Diese Tabelle ist eine **computergestützte "
    "Priorisierung** (Exomiser und zugrundeliegende Datenbanken: ClinVar, gnomAD, "
    "HPO). Sie ist **keine Diagnose** und ersetzt keine ärztliche Beurteilung. "
    "Jeder Kandidat muss **ärztlich/humangenetisch** bewertet und validiert werden."
)

# Spalten-Synonyme: normalisierter Header-Name → Candidate-Feld. Header-getrieben,
# damit der Parser robust gegen Exomiser-Versionsunterschiede und Spalten-
# Reihenfolge bleibt.
_GENE_KEYS = ("GENE_SYMBOL", "GENE", "#GENE_SYMBOL")
_VARIANT_KEYS = ("HGVS", "HGVS_GENOMIC", "VARIANT")
_CLINVAR_KEYS = ("CLINVAR_PRIMARY_INTERPRETATION", "CLINVAR_SIG", "CLINVAR")
_FREQ_KEYS = ("MAX_FREQ", "MAX_FREQUENCY", "MAX_FREQ_SOURCE_FREQ")
_PHENO_KEYS = ("EXOMISER_GENE_PHENO_SCORE", "PHENO_SCORE", "PHENOTYPE_SCORE")


@dataclass(frozen=True)
class Candidate:
    """Ein kuratierter Top-Kandidat. Bewusst klein — nur Felder, die in die Akte
    dürfen. Keine Rohkoordinaten (CHROM/POS/REF/ALT), keine Genotypen."""

    gene: str
    variant: str
    clinvar_significance: str
    frequency: str
    phenotype_score: float
    source: str = SOURCE_LABEL


def _to_score(value: object) -> float:
    """Score robust nach float; nicht-parsebare Werte → 0.0 (sortiert nach unten)."""
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return 0.0


def _clean(value: object) -> str:
    """Zellwert säubern; leer/None → Platzhalter ``NA``."""
    text = "" if value is None else str(value).strip()
    return text if text else NA


def _normalize_header(name: str) -> str:
    return name.strip().lstrip("#").strip().upper()


def _pick(row: dict[str, str], keys: tuple[str, ...]) -> str:
    for key in keys:
        if key in row and str(row[key]).strip():
            return str(row[key]).strip()
    return ""


def parse_exomiser_tsv(text: str) -> list[Candidate]:
    """Parst einen Exomiser-TSV-Output (z. B. ``*.variants.tsv``/``*.genes.tsv``).

    Header-getrieben: die erste nicht-leere Zeile ist die Spalten-Kopfzeile
    (typischerweise mit ``#`` beginnend). Erkennt die kuratierten Felder über
    Spaltennamen, nicht über Positionen. Roh-Koordinaten-Spalten (CONTIG/START/
    REF/ALT etc.) werden ignoriert — sie fließen nicht in die Kandidaten.
    """
    lines = [line for line in text.splitlines() if line.strip()]
    if not lines:
        return []

    header = [_normalize_header(col) for col in lines[0].split("\t")]
    if not any(k in header for k in _GENE_KEYS):
        raise ValueError(
            "Exomiser-TSV ohne erkennbare Gen-Spalte (erwartet z. B. GENE_SYMBOL)."
        )

    candidates: list[Candidate] = []
    for line in lines[1:]:
        if line.startswith("#"):
            continue  # weitere Kommentarzeilen überspringen
        cells = line.split("\t")
        row = {header[i]: cells[i] for i in range(min(len(header), len(cells)))}
        gene = _pick(row, _GENE_KEYS)
        if not gene:
            continue  # Zeile ohne Gen ist kein Kandidat
        candidates.append(
            Candidate(
                gene=gene,
                variant=_clean(_pick(row, _VARIANT_KEYS)),
                clinvar_significance=_clean(_pick(row, _CLINVAR_KEYS)),
                frequency=_clean(_pick(row, _FREQ_KEYS)),
                phenotype_score=_to_score(_pick(row, _PHENO_KEYS)),
            )
        )
    return candidates


def _first_variant(gene_result: dict) -> dict:
    """Wählt aus einem Exomiser-JSON-Gen-Ergebnis die beitragende Variante
    (``contributingVariant``), sonst die erste."""
    variants = gene_result.get("variantEvaluations") or gene_result.get("variants") or []
    if not isinstance(variants, list) or not variants:
        return {}
    for variant in variants:
        if isinstance(variant, dict) and variant.get("contributingVariant"):
            return variant
    first = variants[0]
    return first if isinstance(first, dict) else {}


def _json_clinvar(variant: dict) -> str:
    path = variant.get("pathogenicityData") or {}
    clinvar = path.get("clinVarData") or variant.get("clinVarData") or {}
    return str(clinvar.get("primaryInterpretation", "")).strip()


def _json_frequency(variant: dict) -> str:
    freq = variant.get("frequencyData") or {}
    known = freq.get("knownFrequencies")
    if isinstance(known, list) and known:
        values = [
            f.get("frequency")
            for f in known
            if isinstance(f, dict) and isinstance(f.get("frequency"), (int, float))
        ]
        if values:
            return str(max(values))
    if isinstance(freq.get("maxFreq"), (int, float)):
        return str(freq["maxFreq"])
    return ""


def parse_exomiser_json(text: str) -> list[Candidate]:
    """Parst den Exomiser-JSON-Output (Array von Gen-Ergebnissen).

    Defensiv navigiert: fehlende verschachtelte Felder führen zum Platzhalter,
    nicht zum Absturz. Nur kuratierte Felder werden übernommen.
    """
    data = json.loads(text)
    if isinstance(data, dict):
        # Manche Exomiser-Exporte kapseln die Liste unter "geneResults".
        data = data.get("geneResults") or data.get("genes") or []
    if not isinstance(data, list):
        raise ValueError("Exomiser-JSON: erwartet eine Liste von Gen-Ergebnissen.")

    candidates: list[Candidate] = []
    for gene_result in data:
        if not isinstance(gene_result, dict):
            continue
        gene = str(
            gene_result.get("geneSymbol") or gene_result.get("gene") or ""
        ).strip()
        if not gene:
            continue
        variant = _first_variant(gene_result)
        variant_label = str(
            variant.get("hgvsGenomic")
            or variant.get("hgvs")
            or variant.get("hgvsProtein")
            or ""
        ).strip()
        pheno = gene_result.get("phenotypeScore")
        if pheno is None:
            scores = gene_result.get("geneScores") or {}
            pheno = scores.get("phenotypeScore") if isinstance(scores, dict) else None
        candidates.append(
            Candidate(
                gene=gene,
                variant=_clean(variant_label),
                clinvar_significance=_clean(_json_clinvar(variant)),
                frequency=_clean(_json_frequency(variant)),
                phenotype_score=_to_score(pheno),
            )
        )
    return candidates


def _escape_cell(value: str) -> str:
    return value.replace("|", "\\|")


def _format_score(score: float) -> str:
    return f"{score:.4f}"


def render_genetics_section(candidates: list[Candidate], top_n: int = 10) -> str:
    """Erzeugt die Markdown-Sektion ``## Genetik-Zusammenfassung``.

    Sortiert absteigend nach Phänotyp-Score (Tie-Break: Genname), begrenzt auf die
    Top-N und rendert die kuratierte Tabelle plus medizinischen Disclaimer. Es
    werden **nur** die kuratierten Felder ausgegeben — keine Rohgenom-Zeilen.
    """
    if top_n < 0:
        raise ValueError("top_n muss >= 0 sein.")

    ranked = sorted(candidates, key=lambda c: (-c.phenotype_score, c.gene))[:top_n]

    lines = [SECTION_HEADING, ""]
    lines.append("| " + " | ".join(TABLE_COLUMNS) + " |")
    lines.append("|" + "|".join(["---"] * len(TABLE_COLUMNS)) + "|")

    if ranked:
        for cand in ranked:
            row = [
                _escape_cell(cand.gene),
                _escape_cell(cand.variant),
                _escape_cell(cand.clinvar_significance),
                _escape_cell(cand.frequency),
                _format_score(cand.phenotype_score),
                _escape_cell(cand.source),
            ]
            lines.append("| " + " | ".join(row) + " |")
    else:
        lines.append("| " + " | ".join([NA] * len(TABLE_COLUMNS)) + " |")

    lines.extend(["", DISCLAIMER, ""])
    return "\n".join(lines)


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Konvertiert einen Exomiser-Ergebnis-Output in die Fallakten-Sektion "
            "'## Genetik-Zusammenfassung' (Markdown auf stdout). Schreibt keine "
            "Patientendatei."
        )
    )
    parser.add_argument("ergebnis_pfad", help="Pfad zum Exomiser-Output (TSV oder JSON).")
    parser.add_argument(
        "--top",
        type=int,
        default=10,
        metavar="N",
        help="Anzahl der Top-Kandidaten (Default: 10).",
    )
    parser.add_argument(
        "--format",
        choices=("tsv", "json"),
        default="tsv",
        help="Eingabeformat (Default: tsv).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    try:
        with open(args.ergebnis_pfad, encoding="utf-8") as handle:
            text = handle.read()
    except OSError as exc:
        print(f"Fehler: Ergebnis-Datei nicht lesbar: {exc}", file=sys.stderr)
        return 1

    parser_fn = parse_exomiser_json if args.format == "json" else parse_exomiser_tsv
    try:
        candidates = parser_fn(text)
    except (ValueError, json.JSONDecodeError) as exc:
        print(f"Fehler beim Parsen ({args.format}): {exc}", file=sys.stderr)
        return 1

    print(render_genetics_section(candidates, top_n=args.top))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
