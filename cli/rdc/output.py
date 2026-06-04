"""Agenten-freundliche Ausgabe: knappe Tabellen und JSON-Lines.

Jede Ergebniszeile trägt ihre Quellen-IDs (PMID, RCV, OMIM/ORPHA …) mit, damit
Claude Code Quellen referenzieren kann. Subkommandos wählen über einen
``--json``/``--format``-Schalter zwischen Tabelle und JSON-Lines.
"""

from __future__ import annotations

import json
import sys
from collections.abc import Iterable, Mapping, Sequence
from typing import Any, TextIO


def print_table(
    rows: Iterable[Sequence[Any]],
    headers: Sequence[str],
    *,
    file: TextIO | None = None,
) -> None:
    """Gibt ``rows`` als monospace-ausgerichtete Tabelle aus."""
    out = file or sys.stdout
    cols = list(headers)
    str_rows = [[_cell(value) for value in row] for row in rows]

    widths = [len(col) for col in cols]
    for row in str_rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(cell))

    def fmt(cells: Sequence[str]) -> str:
        return "  ".join(cell.ljust(widths[i]) for i, cell in enumerate(cells))

    print(fmt(cols), file=out)
    print("  ".join("-" * width for width in widths), file=out)
    for row in str_rows:
        print(fmt(row), file=out)


def print_jsonl(
    records: Iterable[Mapping[str, Any]],
    *,
    file: TextIO | None = None,
) -> None:
    """Gibt ``records`` als JSON-Lines aus (ein JSON-Objekt pro Zeile)."""
    out = file or sys.stdout
    for record in records:
        print(json.dumps(record, ensure_ascii=False, default=str), file=out)


def _cell(value: Any) -> str:
    return "" if value is None else str(value)
