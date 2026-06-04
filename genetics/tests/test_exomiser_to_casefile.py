"""Tests für den Exomiser → Fallakten-Markdown-Konverter (GEN-03).

Offline und deterministisch: nur lokale Fixture + Inline-Daten, kein Netzwerk,
kein Container.
"""

import json
import sys
from pathlib import Path

# Modul aus genetics/ importierbar machen (kein installiertes Paket).
GENETICS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(GENETICS_DIR))

import exomiser_to_casefile as conv  # noqa: E402

FIXTURE = GENETICS_DIR / "tests" / "fixtures" / "exomiser_result.tsv.sample"


def _load_fixture() -> str:
    return FIXTURE.read_text(encoding="utf-8")


# --- Parsing (TSV) ---------------------------------------------------------


def test_parse_tsv_candidate_count():
    candidates = conv.parse_exomiser_tsv(_load_fixture())
    # Fixture hat 12 Datenzeilen.
    assert len(candidates) == 12


def test_parse_tsv_field_mapping():
    candidates = conv.parse_exomiser_tsv(_load_fixture())
    top = max(candidates, key=lambda c: c.phenotype_score)
    assert top.gene == "FGFR2"
    assert top.variant == "c.1694A>C (p.Glu565Ala)"
    assert top.clinvar_significance == "PATHOGENIC"
    assert top.frequency == "0.0"
    assert top.phenotype_score == 0.9912
    assert top.source == "Exomiser"


def test_parse_tsv_ignores_raw_coordinate_columns():
    # CONTIG/START/REF/ALT dürfen NICHT in den kuratierten Kandidaten landen.
    candidates = conv.parse_exomiser_tsv(_load_fixture())
    for cand in candidates:
        for field in (cand.variant, cand.clinvar_significance, cand.frequency):
            assert "123276893" not in field  # eine START-Koordinate aus der Fixture


def test_parse_tsv_empty_input():
    assert conv.parse_exomiser_tsv("") == []


def test_parse_tsv_missing_gene_column_raises():
    bad = "#FOO\tBAR\n1\t2\n"
    try:
        conv.parse_exomiser_tsv(bad)
    except ValueError:
        return
    raise AssertionError("Erwartete ValueError bei fehlender Gen-Spalte.")


# --- Parsing (JSON) --------------------------------------------------------


def test_parse_json_nested_shape():
    payload = [
        {
            "geneSymbol": "FGFR2",
            "phenotypeScore": 0.99,
            "variantEvaluations": [
                {
                    "contributingVariant": True,
                    "hgvsGenomic": "chr10:g.123A>C",
                    "pathogenicityData": {
                        "clinVarData": {"primaryInterpretation": "PATHOGENIC"}
                    },
                    "frequencyData": {
                        "knownFrequencies": [
                            {"frequency": 0.001},
                            {"frequency": 0.004},
                        ]
                    },
                }
            ],
        }
    ]
    candidates = conv.parse_exomiser_json(json.dumps(payload))
    assert len(candidates) == 1
    cand = candidates[0]
    assert cand.gene == "FGFR2"
    assert cand.variant == "chr10:g.123A>C"
    assert cand.clinvar_significance == "PATHOGENIC"
    assert cand.frequency == "0.004"  # Maximum der bekannten Frequenzen
    assert cand.phenotype_score == 0.99


def test_parse_json_missing_fields_use_placeholder():
    payload = [{"geneSymbol": "LMNA"}]
    candidates = conv.parse_exomiser_json(json.dumps(payload))
    assert candidates[0].gene == "LMNA"
    assert candidates[0].variant == conv.NA
    assert candidates[0].clinvar_significance == conv.NA
    assert candidates[0].phenotype_score == 0.0


# --- Rendering -------------------------------------------------------------


def test_render_has_exact_heading():
    md = conv.render_genetics_section(conv.parse_exomiser_tsv(_load_fixture()))
    assert "## Genetik-Zusammenfassung" in md
    # Exakt der String aus KB-01 (docs/case-file-TEMPLATE.md).
    assert conv.SECTION_HEADING == "## Genetik-Zusammenfassung"


def test_render_heading_matches_template():
    template = (
        GENETICS_DIR.parent / "docs" / "case-file-TEMPLATE.md"
    ).read_text(encoding="utf-8")
    assert conv.SECTION_HEADING in template


def test_render_has_all_table_columns():
    md = conv.render_genetics_section(conv.parse_exomiser_tsv(_load_fixture()))
    for column in ("Gen", "Variante", "ClinVar-Bedeutung", "Häufigkeit",
                   "Phänotyp-Score", "Quelle"):
        assert column in md


def test_render_has_disclaimer():
    md = conv.render_genetics_section(conv.parse_exomiser_tsv(_load_fixture()))
    assert "keine Diagnose" in md
    assert "ärztlich" in md


def test_render_top_n_limit():
    candidates = conv.parse_exomiser_tsv(_load_fixture())
    md3 = conv.render_genetics_section(candidates, top_n=3)
    # Genau 3 Datenzeilen in der Tabelle (Zeilen mit "| " am Anfang minus Header).
    data_rows = [
        line for line in md3.splitlines()
        if line.startswith("| ") and "Gen |" not in line
    ]
    assert len(data_rows) == 3
    # Top-3 nach Phänotyp-Score: FGFR2, SCN1A, COL2A1.
    assert "FGFR2" in md3 and "SCN1A" in md3 and "COL2A1" in md3
    # Niedriger gerankte erscheinen nicht.
    assert "LMNA" not in md3 and "BRCA2" not in md3


def test_render_empty_candidates_still_valid_table():
    md = conv.render_genetics_section([])
    assert conv.SECTION_HEADING in md
    assert "keine Diagnose" in md


# --- Negativ-Check: keine Rohgenom-Zeilen ----------------------------------


def test_render_no_raw_genome_lines():
    candidates = conv.parse_exomiser_tsv(_load_fixture())
    md = conv.render_genetics_section(candidates, top_n=10)
    # Kein VCF-Header.
    assert "##fileformat=VCF" not in md
    # Keine Roh-Varianten-Kopfzeile.
    assert "#CHROM\tPOS\tID\tREF\tALT" not in md
    assert "#CHROM" not in md
    # Keine Roh-Koordinaten (START-Werte aus der Fixture).
    for raw in ("123276893", "166053123", "153296777"):
        assert raw not in md


def test_render_no_variants_beyond_top_n():
    # Über die Top-N hinaus erscheinen keine weiteren Varianten/Gene.
    candidates = conv.parse_exomiser_tsv(_load_fixture())
    md = conv.render_genetics_section(candidates, top_n=10)
    # Fixture hat 12 Gene; bei top_n=10 fehlen die zwei schwächsten.
    assert "BRCA2" not in md
    assert "LMNA" not in md
