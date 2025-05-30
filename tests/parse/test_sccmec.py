"""Test functions for parsing SCCmec results."""

import pytest

from prp.parse.sccmec import parse_sccmec_results


def test_parse_sccmec_results(saureus_sccmec_path):
    """Test parsing of spatyper result file."""

    # test parsing the output of saureus.
    result = parse_sccmec_results(saureus_sccmec_path)
    expected_sccmec = {
        "type": "sccmectype",
        "software": "sccmec",
        "result": {
            "type": "IV",
            "subtype": "multiple",
            "mecA": "+",
            "targets": ["ccrA2", "ccrB2", "IS431", "IS431_1", "IS431_2", "IS1272", "mecA", "mecR1"],
            "regions": ["IVa", "IVn"],
            "coverage": [96.31, 83.93],
            "hits": [27,25],
            "target_comment": None,
            "region_comment": "Found matches for multiple types including: IVa, IVn",
            "comment": "The type was determined based on matches to multiple subtypes of the same type"
        }
    }
    # check if data matches
    assert expected_sccmec == result.model_dump()
