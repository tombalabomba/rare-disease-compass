"""Tests für die Fallakten-Ordner-Validierung (KB-03).

Deterministisch, offline, Stdlib + lokaler Import. Geprüft werden:
- valider Ordner ⇒ keine Befunde,
- fehlende Pflichtsektion ⇒ Sektions-Befund,
- falsch formatierte HPO-ID ⇒ HPO-Befund (korrekte ID löst keinen aus),
- ``pii_guard.scan_file`` wird aufgerufen und ein PII-Treffer wird zum Befund,
- Exit-Code-Verhalten der CLI (Befunde ⇒ != 0, sauber ⇒ 0).
"""

from __future__ import annotations

from pathlib import Path

import pii_guard
import validate_case_folder
from validate_case_folder import validate_case_folder as validate

_FIXTURES = Path(__file__).parent / "fixtures"
_OK = _FIXTURES / "case-folder-ok"
_MISSING = _FIXTURES / "case-folder-missing-section"
_BAD_HPO = _FIXTURES / "case-folder-bad-hpo"


# -- Valider Ordner -----------------------------------------------------------


def test_valider_ordner_keine_befunde() -> None:
    assert validate(_OK) == []


# -- Fehlende Sektion ---------------------------------------------------------


def test_fehlende_sektion_erkannt() -> None:
    issues = validate(_MISSING)
    sektion = [i for i in issues if i.kind == "fehlende_sektion"]
    assert sektion, "erwartet einen Sektions-Befund"
    assert any("## Medikation" in i.detail for i in sektion)


# -- HPO-Format ---------------------------------------------------------------


def test_bad_hpo_erzeugt_befund() -> None:
    issues = validate(_BAD_HPO)
    hpo = [i for i in issues if i.kind == "hpo_format"]
    assert len(hpo) == 1, "genau die falsch formatierte ID 'HP:123' ist ein Befund"
    assert "HP:123" in hpo[0].detail


def test_korrekte_hpo_id_kein_befund() -> None:
    # Die korrekt formatierte ID HP:0003324 in derselben Akte darf NICHT
    # als Befund auftauchen.
    issues = validate(_BAD_HPO)
    assert all("HP:0003324" not in i.detail for i in issues)
    # Der valide Ordner (nur korrekte IDs) erzeugt gar keine HPO-Befunde.
    assert [i for i in validate(_OK) if i.kind == "hpo_format"] == []


# -- PII-Guard wird aufgerufen ------------------------------------------------


def test_pii_guard_wird_aufgerufen(monkeypatch) -> None:
    aufrufe: list[Path] = []
    leck = [pii_guard.Finding("geburtsdatum", 12, "0***9")]

    def fake_scan_file(path):
        aufrufe.append(Path(path))
        return leck

    monkeypatch.setattr(validate_case_folder.pii_guard, "scan_file", fake_scan_file)
    issues = validate(_OK)

    # Beweis 1: scan_file wurde auf die Akte des Ordners angewandt.
    assert aufrufe and aufrufe[0].name.startswith("case-file")
    # Beweis 2: der PII-Treffer wird zu einem PII-Befund im Report.
    pii = [i for i in issues if i.kind == "pii"]
    assert len(pii) == 1
    assert "geburtsdatum" in pii[0].detail


# -- Exit-Code-Verhalten ------------------------------------------------------


def test_cli_exit_code_bei_befunden_ungleich_null() -> None:
    assert validate_case_folder.main([str(_MISSING)]) != 0


def test_cli_exit_code_bei_sauberem_ordner_null() -> None:
    assert validate_case_folder.main([str(_OK)]) == 0
