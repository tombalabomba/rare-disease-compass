"""PII-Guard für Fallakten — deterministischer, offline-Regex-Scanner.

Prüft eine pseudonymisierte Fallakte (Markdown) auf typische PII-Muster
(Geburtsdatum, E-Mail, Telefonnummer, deutsche Versichertennummer, IBAN,
Klarname im Stammdaten-Kontext) und bricht mit Exit-Code != 0 ab, sobald ein
Verdacht vorliegt. Geeignet als Pre-Commit-Hook und als Baustein für KB-03.

Bewusst regelbasiert/heuristisch (Stdlib `re` only) — kein Modell, kein
Netzwerk, reproduzierbar. Der Klarnamen-Detektor greift nur in einem klaren
Stammdaten-Kontext (Zeile mit `Name:`/`Patient:` o. Ä.) und führt eine Allowlist
medizinischer Mehrwort-Begriffe, damit Eigennamen wie „Morbus Crohn" nicht
fehlalarmieren.

CLI-Output enthält nur Art + Zeile (keine vollständigen Treffer) — sonst landet
PII doppelt im Log.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Finding:
    """Ein einzelner PII-Verdacht: Art, Zeilennummer, redigierter Ausschnitt."""

    kind: str
    line: int
    snippet: str


# -- Regex-Detektoren (Pattern-Tabelle) ---------------------------------------
# Jeder Eintrag: (kind, kompiliertes Pattern). Reihenfolge ist stabil, damit die
# Findings deterministisch sortiert sind.
_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    # Geburtsdatum DD.MM.YYYY und DD/MM/YYYY (Jahr 1900–2099, plausibler Tag/Monat).
    (
        "geburtsdatum",
        re.compile(
            r"\b(?:0[1-9]|[12]\d|3[01])[./](?:0[1-9]|1[0-2])[./](?:19|20)\d{2}\b"
        ),
    ),
    # E-Mail-Adresse.
    (
        "email",
        re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
    ),
    # Telefonnummer (DE/international). Verlangt eine Vorwahl mit Trennzeichen,
    # damit HPO-IDs wie `HP:0002028` (keine Trennung) NICHT fehlalarmieren.
    (
        "telefon",
        re.compile(
            r"(?:\+\d{1,3}[\s/\-]?)?\(?0\d{1,4}\)?[\s/\-]\d{3,}(?:[\s/\-]?\d+)*"
        ),
    ),
    # Deutsche Versichertennummer (KV-Nummer): 1 Buchstabe + 9 Ziffern.
    (
        "versichertennummer",
        re.compile(r"\b[A-Z]\d{9}\b"),
    ),
    # IBAN (Länderkürzel + 2 Prüfziffern + 11–30 alphanumerische Stellen).
    (
        "iban",
        re.compile(r"\b[A-Z]{2}\d{2}[A-Z0-9]{11,30}\b"),
    ),
]

# Zeile, in der ein Klarname überhaupt erst gesucht wird (Stammdaten-Kontext).
# Der Doppelpunkt ist Pflicht, damit Fließtext nicht triggert.
_NAME_TRIGGER = re.compile(
    r"\b(?:Name|Patient(?:in)?|Vorname|Nachname|Versicherte[rn]?|Versichertenname)\s*:",
    re.IGNORECASE,
)

# Zwei aufeinanderfolgende großgeschriebene Wörter (mind. 2 Buchstaben je Wort);
# das zweite darf einen Bindestrich-Teil haben (z. B. „Anna Meier-Schmidt").
# Initialen wie „L. K." matchen nicht (Einzelbuchstaben).
_NAME_PAIR = re.compile(
    r"\b([A-ZÄÖÜ][a-zäöüß]+)\s+([A-ZÄÖÜ][a-zäöüß]+(?:-[A-ZÄÖÜ][a-zäöüß]+)?)\b"
)

# Allowlist medizinischer Mehrwort-Eigennamen (klein geschrieben, mit Space).
# Bindestrich-Begriffe (z. B. „Marfan-Syndrom") sind bereits durch _NAME_PAIR
# ausgeschlossen (kein Space) und müssen hier nicht stehen.
_MEDICAL_ALLOWLIST: frozenset[str] = frozenset(
    {
        "morbus crohn",
        "morbus bechterew",
        "morbus wilson",
        "morbus addison",
        "morbus basedow",
        "morbus fabry",
        "morbus pompe",
    }
)


def _redact(value: str) -> str:
    """Redigiert einen Treffer: nur erstes/letztes Zeichen, Mitte maskiert.

    Verhindert, dass der volle PII-Wert in den ``Finding``-Objekten liegt.
    """
    stripped = value.strip()
    if len(stripped) <= 4:
        return "***"
    return f"{stripped[0]}***{stripped[-1]}"


def _scan_names(line: str) -> list[str]:
    """Findet Klarnamen-Verdachte in einer Zeile — nur im Stammdaten-Kontext."""
    if not _NAME_TRIGGER.search(line):
        return []
    names: list[str] = []
    for match in _NAME_PAIR.finditer(line):
        pair = f"{match.group(1)} {match.group(2)}"
        if pair.lower() in _MEDICAL_ALLOWLIST:
            continue
        names.append(pair)
    return names


def scan_text(text: str) -> list[Finding]:
    """Scannt freien Text Zeile für Zeile und liefert alle PII-Verdachte."""
    findings: list[Finding] = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        for kind, pattern in _PATTERNS:
            for match in pattern.finditer(line):
                findings.append(Finding(kind, lineno, _redact(match.group(0))))
        for name in _scan_names(line):
            findings.append(Finding("klarname", lineno, _redact(name)))
    return findings


def scan_file(path: str | Path) -> list[Finding]:
    """Scannt eine Datei (UTF-8) und liefert alle PII-Verdachte."""
    return scan_text(Path(path).read_text(encoding="utf-8"))


def main(argv: list[str] | None = None) -> int:
    """CLI-Einstieg: scannt die übergebenen Dateien. Exit != 0 bei Funden."""
    parser = argparse.ArgumentParser(
        description=(
            "PII-Guard für Fallakten — prüft Markdown-Dateien auf PII-Muster "
            "und beendet mit Code != 0 bei Verdacht."
        )
    )
    parser.add_argument(
        "paths",
        nargs="+",
        type=Path,
        help="zu prüfende Fallakten-Datei(en)",
    )
    args = parser.parse_args(argv)

    total = 0
    for path in args.paths:
        try:
            findings = scan_file(path)
        except (OSError, UnicodeDecodeError) as exc:
            print(f"{path}: konnte nicht gelesen werden ({exc})", file=sys.stderr)
            return 2
        for finding in findings:
            # Bewusst NUR Art + Zeile — keine vollständigen Treffer ins Log.
            print(
                f"{path}:{finding.line}: PII-Verdacht [{finding.kind}]",
                file=sys.stderr,
            )
        total += len(findings)

    if total:
        print(
            f"{total} PII-Verdachtsfall/-fälle gefunden — bitte pseudonymisieren.",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
