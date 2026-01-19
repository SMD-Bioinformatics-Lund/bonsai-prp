"""Test functions for parsing Emmtyper results."""

from prp.models.base import ParserOutput, ResultEnvelope
from prp.models.enums import AnalysisType
from prp.models.typing import TypingResultEmm
from prp.parse.emmtyper import EmmTyperParser


def test_emmtype_parser_results(streptococcus_emmtyper_path):
    parser = EmmTyperParser()
    result = parser.parse(streptococcus_emmtyper_path)
    expected_streptococcus = {
        "cluster_count": 2,
        "emmtype": "EMM169.3",
        "emm_like_alleles": ["EMM164.2~*"],
        "emm_cluster": "E4",
    }
    # check data structure
    assert isinstance(result, ParserOutput)

    assert isinstance(result.results, dict)

    res = result.results[AnalysisType.EMM]
    assert isinstance(res, ResultEnvelope)
    assert res.status == "parsed"

    assert isinstance(res.value, TypingResultEmm)

    # check if data matches
    assert expected_streptococcus == res.value.model_dump()
