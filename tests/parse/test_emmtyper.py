"""Test functions for parsing Emmtyper results."""

from prp.models.base import ParserOutput
from prp.models.typing import TypingResultEmm
from prp.parse.emmtyper import EmmTyperParser


def test_parse_emmtyper_results(streptococcus_emmtyper_path):
    """Test parsing of emmtyper result files."""

    # test parsing the output of an streptococcus.
    result = parse_emm_pred(streptococcus_emmtyper_path)
    expected_streptococcus = {
        "cluster_count": 2,
        "emmtype": "EMM169.3",
        "emm_like_alleles": ["EMM164.2~*"],
        "emm_cluster": "E4",
    }
    # check if data matches
    assert expected_streptococcus == result[0].result.model_dump()


def test_emmtype_parser_results(streptococcus_emmtyper_path):
    parser = EmmTyperParser()
    with open(streptococcus_emmtyper_path) as inpt:
        result = parser.parse(inpt)
    expected_streptococcus = {
        "cluster_count": 2,
        "emmtype": "EMM169.3",
        "emm_like_alleles": ["EMM164.2~*"],
        "emm_cluster": "E4",
    }
    # check data structure
    assert isinstance(result, ParserOutput)

    assert isinstance(result.results, TypingResultEmm)

    # check if data matches
    assert expected_streptococcus == result.results.model_dump()