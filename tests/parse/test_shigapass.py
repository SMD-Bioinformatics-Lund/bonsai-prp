"""Test functions for parsing Shigapass results."""

import pytest
from prp.parse.phenotype.shigapass import parse_shigapass_pred, _extract_percentage


@pytest.mark.parametrize(
    "input,expected",
    [
        ("79,(48.2%)", 48.2),
        ("79,(48.0%)", 48.0),
        ("79,(48%)", 48.0),
        ("NA,(0.0%)", 0.0),
        ("NA,(0%)", 0.0),
    ],
)
def test_extract_percentage(input, expected):
    """
    Test that the percentage can be extracted from rfb_hits.

    "foo, (12%)" -> 12%
    """
    result = _extract_percentage(input)
    assert result == expected


def test_parse_shigapass_results(ecoli_shigapass_path, shigella_shigapass_path):
    """Test parsing of shigapass result files."""

    # test parsing the output of an ecoli.
    result = parse_shigapass_pred(ecoli_shigapass_path)
    expected_ecoli = {
        "type": "shigatype",
        "software": "shigapass",
        "result": {
            "rfb": None,
            "rfb_hits": 0.0,
            "mlst": None,
            "flic": None,
            "crispr": None,
            "ipah": "ipaH-",
            "predicted_serotype": "Not Shigella/EIEC",
            "predicted_flex_serotype": None,
            "comments": None,
        },
    }
    # check if data matches
    assert expected_ecoli == result[0].model_dump()

    # test parsing the output with a shigella.
    result = parse_shigapass_pred(shigella_shigapass_path)
    expected_shigella = {
        "type": "shigatype",
        "software": "shigapass",
        "result": {
            "rfb": "C2",
            "rfb_hits": 48.2,
            "mlst": "ST145",
            "flic": "ShH57(ShH3cplx)",
            "crispr": "A-var2",
            "ipah": "ipaH+",
            "predicted_serotype": "SB2",
            "predicted_flex_serotype": None,
            "comments": None,
        },
    }

    # check if data matches
    assert expected_shigella == result[0].model_dump()
