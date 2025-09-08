"""Test functions for parsing SAMtools coverage results."""

import pytest

from prp.parse.qc import parse_samtools_coverage_results


def test_parse_samtools_coverage_results(test_samtools_coverage_path):
    """Test parsing of SAMtools coverage result file."""

    # test parsing the output
    result = parse_samtools_coverage_results(test_samtools_coverage_path)
    expected_samtools = {
        "type": "qc",
        "software": "samtools",
        "result": {
            "contigs": [
                {
                    "rname": "NC_007795.1",
                    "startpos": 1,
                    "endpos": 2821361,
                    "numreads": 543217,
                    "covbases": 2821361,
                    "coverage": 100.0,
                    "meandepth": 42.5,
                    "meanbaseq": 35.8,
                    "meanmapq": 60.0
                },
                {
                    "rname": "NC_006629.2",
                    "startpos": 1,
                    "endpos": 4440,
                    "numreads": 2012,
                    "covbases": 4406,
                    "coverage": 99.2342,
                    "meandepth": 351.234,
                    "meanbaseq": 24.7,
                    "meanmapq": 30.7
                }
            ]       
        }
    }
    # check if data matches
    assert expected_samtools == result.model_dump()