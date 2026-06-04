"""Tests für den PII-Guard (KB-02).

Deterministisch, offline, Stdlib-only. Geprüft werden:
- Erkennung von Geburtsdatum UND Klarname (plus E-Mail/IBAN) in der Leck-Fixture,
- Exit-Code-Verhalten der CLI (Funde => != 0, sauber => 0),
- Abwesenheit von False-Positives auf der sauberen Fixture, insbesondere keine
  Klarnamen-Alarme durch medizinische Eigennamen.
"""

from __future__ import annotations

from pathlib import Path

import pii_guard

_FIXTURES = Path(__file__).parent / "fixtures"
_CLEAN = _FIXTURES / "case-file-FIXTURE-clean.md"
_LEAK = _FIXTURES / "case-file-FIXTURE-leak.md"


# -- Erkennung ----------------------------------------------------------------


def test_leak_findet_geburtsdatum_und_klarname() -> None:
    findings = pii_guard.scan_file(_LEAK)
    kinds = {f.kind for f in findings}
    assert "geburtsdatum" in kinds
    assert "klarname" in kinds


def test_leak_findet_email_und_iban() -> None:
    kinds = {f.kind for f in pii_guard.scan_file(_LEAK)}
    assert "email" in kinds
    assert "iban" in kinds


def test_findings_redigiert_keinen_vollwert() -> None:
    # Kein Finding-Snippet enthält den vollständigen erfundenen Klarnamen.
    snippets = [f.snippet for f in pii_guard.scan_file(_LEAK)]
    assert all("Mustermann" not in s for s in snippets)


# -- Erweiterte Muster (Regressionsschutz für die geschlossenen Lücken) -------


def test_erkennt_iso_datum() -> None:
    # ISO-Format YYYY-MM-DD wurde vorher übersehen.
    kinds = {f.kind for f in pii_guard.scan_text("Kontrolle am 2018-03-14.")}
    assert "geburtsdatum" in kinds


def test_erkennt_internationale_telefonnummer_ohne_fuehrende_null() -> None:
    kinds = {f.kind for f in pii_guard.scan_text("Mobil: +49 171 1234567")}
    assert "telefon" in kinds


def test_erkennt_deutsche_adresse() -> None:
    kinds = {
        f.kind
        for f in pii_guard.scan_text("Musterstraße 12, 80331 München")
    }
    assert "adresse" in kinds


def test_hpo_id_ist_kein_telefon() -> None:
    # HPO-IDs dürfen NICHT als Telefonnummer fehlalarmieren.
    kinds = {f.kind for f in pii_guard.scan_text("Symptom HP:0002028 seit 2 Jahren")}
    assert "telefon" not in kinds


# -- Exit-Code-Verhalten ------------------------------------------------------


def test_cli_exit_code_bei_leck_ungleich_null() -> None:
    assert pii_guard.main([str(_LEAK)]) != 0


def test_cli_exit_code_bei_sauberer_datei_null() -> None:
    assert pii_guard.main([str(_CLEAN)]) == 0


# -- Negativ-Test gegen False-Positives ---------------------------------------


def test_clean_liefert_null_funde() -> None:
    assert pii_guard.scan_file(_CLEAN) == []


def test_medizinische_eigennamen_kein_klarnamen_alarm() -> None:
    # Selbst im Stammdaten-Kontext (Trigger „Name:") darf ein allowlist-Begriff
    # keinen Klarnamen-Alarm auslösen.
    findings = pii_guard.scan_text("Name: Morbus Crohn")
    assert [f for f in findings if f.kind == "klarname"] == []


def test_hpo_id_kein_telefon_oder_versichertennummer() -> None:
    findings = pii_guard.scan_text("| Chronischer Durchfall | HP:0002028 | seit ... |")
    assert findings == []
