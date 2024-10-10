"""Test functions for parsing Emmtyper results."""

import pytest

from prp.parse.phenotype.emmtyper import parse_emmtyper_pred


def test_parse_emmtyper_results(streptococcus_emmtyper_path):
    """Test parsing of emmtyper result files."""

    # test parsing the output of an streptococcus.
    result = parse_emmtyper_pred(streptococcus_emmtyper_path)
    expected_streptococcus =  {
        "cluster_count": 2,
        "emmtype": "EMM169.3",
        "emm_like_alleles": [
          "EMM164.2~*"
        ],
        "emm_cluster": "E4"
    }
    # check if data matches
    assert expected_streptococcus == result[0].result.model_dump()