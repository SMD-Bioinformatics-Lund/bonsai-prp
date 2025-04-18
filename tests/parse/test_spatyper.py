"""Test functions for parsing spaTyper results."""

import pytest

from prp.parse.spatyper import parse_spatyper_results


def test_parse_spatyper_results(saureus_spatyper_path):
    """Test parsing of spatyper result file."""

    # test parsing the output of saureus.
    result = parse_spatyper_results(saureus_spatyper_path)
    expected_spatyper = {
        "type": "spatype",
        "software": "spatyper",
        "result": {
            "sequence_name": "contig_1",
            "repeats": "15-12-16-02-16-02-25-17-24",
            "type": "t021"
        }
    }
    # check if data matches
    assert expected_spatyper == result.model_dump()
