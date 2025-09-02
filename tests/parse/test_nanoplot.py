"""Test functions for parsing NanoPlot results."""

import pytest

from prp.parse.qc import parse_nanoplot_results


def test_parse_nanoplot_results(saureus_nanoplot_path):
    """Test parsing of NanoPlot result file."""

    # Test parsing the output
    result = parse_nanoplot_results(saureus_nanoplot_path)
    expected_nanoplot = {
        "software": "nanoplot",
        "result": {
            "mean_read_length": 4697.8,
            "mean_read_quality": 13.2,
            "median_read_length": 2814.0,
            "median_read_quality": 15.2,
            "number_of_reads": 1000.0,
            "read_length_n50": 6893.0,
            "stdev_read_length": 5845.6,
            "total_bases": 4697845.0
        }
    }

    # Check if data matches
    assert expected_nanoplot == result.model_dump()