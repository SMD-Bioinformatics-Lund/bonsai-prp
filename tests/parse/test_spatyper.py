"""Test functions for parsing spaTyper results."""

from prp.models.base import ParserOutput
from prp.models.enums import AnalysisType
from prp.models.typing import TypingResultSpatyper
from prp.parse.spatyper import SpatyperParser


def test_parse_spatyper_results(saureus_spatyper_path):
    """Test parsing of spatyper result file."""

    parser = SpatyperParser()
    result = parser.parse(saureus_spatyper_path)

    # assert correct ouptut data model
    assert isinstance(result, ParserOutput)

    assert isinstance(result.results[AnalysisType.SPATYPE], TypingResultSpatyper)

    expected_spatyper = {
        "sequence_name": "contig_1",
        "repeats": "15-12-16-02-16-02-25-17-24",
        "type": "t021",
    }
    # check if data matches
    assert expected_spatyper == result.results[AnalysisType.SPATYPE].model_dump()
