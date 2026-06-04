"""Fallakten-Ordner-Validierung (KB-03) — deterministisch, offline.

Prüft einen Fall-Ordner gegen die Ordner-Konvention (SET-01) und das
Fallakten-Schema (KB-01-Template). Claude Code liest den Ordner **direkt** als
Dateien — es gibt keine RAG-Ingestion und keinen Server. Dieses Skript ist die
maschinelle Absicherung dieser Konvention:

1. **Pflichtsektionen** — jede Akte muss die im KB-01-Template definierten
   ``## …``-Überschriften enthalten.
2. **HPO-Format** — alle HPO-IDs in der Symptom-Tabelle müssen ``HP:`` + genau
   7 Ziffern sein.
3. **PII** — jede Akte wird durch den PII-Guard (KB-02, ``tools/pii_guard.py``)
   geschickt; gefundene Lecks landen als Befund im Report.

Single source of truth: Die Sektionsliste stammt aus dem KB-01-Template, die
PII-Logik aus KB-02 (hier nur Import, keine Doppel-Implementierung). Reine
Stdlib + lokaler Import, kein Netzwerk, kein Index, keine DB.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

import pii_guard

# -- Konvention ---------------------------------------------------------------
# Pflichtsektionen exakt wie im KB-01-Template (docs/case-file-TEMPLATE.md).
# Reihenfolge stabil, damit fehlende Sektionen deterministisch gemeldet werden.
REQUIRED_SECTIONS: tuple[str, ...] = (
    "## Stammdaten",
    "## Zeitleiste",
    "## Symptome",
    "## Befunde",
    "## Ausgeschlossenes",
    "## Genetik-Zusammenfassung",
    "## Offene Fragen",
    "## Medikation",
)

# Dateinamen-Muster der Fallakte(n) im Ordner.
_CASE_FILE_GLOB = "case-file*.md"

# Korrekt formatierte HPO-ID: HP: + genau 7 Ziffern.
_HPO_VALID = re.compile(r"^HP:[0-9]{7}$")

# Kandidaten-Token, die wie eine HPO-Referenz aussehen (richtig ODER falsch),
# damit Fehlformate (HP:123, HP0001250, HPO:0001250) als Befund auffallen statt
# stillschweigend durchzurutschen. Wortgrenzen, damit Fließtext nicht triggert.
_HPO_CANDIDATE = re.compile(r"\bHPO?:?[0-9]{1,}\b")


@dataclass(frozen=True)
class Issue:
    """Ein einzelner Validierungs-Befund: Art, betroffene Datei, Detailtext."""

    kind: str
    file: str
    detail: str


def _find_case_files(folder: Path) -> list[Path]:
    """Liefert die Fallakten-Dateien (``case-file*.md``) im Ordner, sortiert."""
    return sorted(folder.glob(_CASE_FILE_GLOB))


def _check_sections(text: str, file_label: str) -> list[Issue]:
    """Meldet jede fehlende Pflichtsektion als ``fehlende_sektion``-Befund."""
    issues: list[Issue] = []
    lines = text.splitlines()
    for section in REQUIRED_SECTIONS:
        if section not in lines:
            issues.append(
                Issue("fehlende_sektion", file_label, f"Pflichtsektion fehlt: {section}")
            )
    return issues


def _check_hpo(text: str, file_label: str) -> list[Issue]:
    """Meldet jede falsch formatierte HPO-Referenz als ``hpo_format``-Befund.

    Geprüft werden nur Zeilen der Symptom-Tabelle (Markdown-Tabellenzeilen).
    Ein Kandidat, der nicht ``HP:`` + 7 Ziffern ist, erzeugt einen Befund.
    """
    issues: list[Issue] = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        if not line.lstrip().startswith("|"):
            continue
        for match in _HPO_CANDIDATE.finditer(line):
            token = match.group(0)
            if not _HPO_VALID.match(token):
                issues.append(
                    Issue(
                        "hpo_format",
                        file_label,
                        f"Zeile {lineno}: ungültige HPO-ID '{token}' "
                        "(erwartet HP: + 7 Ziffern)",
                    )
                )
    return issues


def _check_pii(path: Path, file_label: str) -> list[Issue]:
    """Ruft den KB-02-PII-Guard auf und meldet jeden Treffer als ``pii``-Befund."""
    issues: list[Issue] = []
    for finding in pii_guard.scan_file(path):
        issues.append(
            Issue(
                "pii",
                file_label,
                f"Zeile {finding.line}: PII-Verdacht [{finding.kind}]",
            )
        )
    return issues


def validate_case_folder(path: str | Path) -> list[Issue]:
    """Validiert einen Fall-Ordner und liefert alle Befunde.

    Befund-Arten: ``kein_ordner``, ``keine_akte``, ``fehlende_sektion``,
    ``hpo_format``, ``pii``, ``lesefehler``. Leere Liste = sauber.
    """
    folder = Path(path)
    if not folder.is_dir():
        return [Issue("kein_ordner", str(folder), "Pfad ist kein Verzeichnis")]

    case_files = _find_case_files(folder)
    if not case_files:
        return [
            Issue(
                "keine_akte",
                str(folder),
                f"keine Fallakte gefunden (Muster '{_CASE_FILE_GLOB}')",
            )
        ]

    issues: list[Issue] = []
    for case_file in case_files:
        label = str(case_file)
        try:
            text = case_file.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            issues.append(Issue("lesefehler", label, f"konnte nicht gelesen werden ({exc})"))
            continue
        issues.extend(_check_sections(text, label))
        issues.extend(_check_hpo(text, label))
        issues.extend(_check_pii(case_file, label))
    return issues


def _format_report(folder: Path, issues: list[Issue]) -> str:
    """Erzeugt einen lesbaren Report (ohne PII-Vollwerte)."""
    if not issues:
        return f"OK — '{folder}': keine Befunde."
    lines = [f"{len(issues)} Befund(e) in '{folder}':"]
    for issue in issues:
        lines.append(f"  [{issue.kind}] {issue.file}: {issue.detail}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    """CLI-Einstieg: validiert einen Ordner. Exit != 0 bei Befunden."""
    parser = argparse.ArgumentParser(
        description=(
            "Validiert einen Fallakten-Ordner gegen Pflichtsektionen, HPO-Format "
            "und PII (lokal, offline). Exit != 0 bei Befunden."
        )
    )
    parser.add_argument("folder", type=Path, help="Pfad zum Fall-Ordner")
    args = parser.parse_args(argv)

    issues = validate_case_folder(args.folder)
    report = _format_report(args.folder, issues)
    print(report, file=sys.stderr if issues else sys.stdout)
    return 1 if issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
