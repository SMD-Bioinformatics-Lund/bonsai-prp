"""Test functions for parsing SAMtools coverage results."""

import pytest

from prp.parse.qc import parse_samtools_coverage_results


def test_parse_samtools_coverage_results(saureus_samtools_coverage_path):
    """Test parsing of SAMtools coverage result file."""

    # test parsing the output
    result = parse_samtools_coverage_results(saureus_samtools_coverage_path)
    expected_samtools = {
        "software": "samtools",
        "version": None,
        "result": {
            "contigs": [
                {
                    "rname": "NC_002951.2",
                    "startpos": 1,
                    "endpos": 2809422,
                    "numreads": 175210,
                    "covbases": 2678233,
                    "coverage": 95.3304,
                    "meandepth": 186.651,
                    "meanbaseq": 22.6,
                    "meanmapq": 57.5,
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
                    "meanmapq": 30.7,
                },
            ]
        },
    }
    # check if data matches
    assert expected_samtools == result.model_dump()
