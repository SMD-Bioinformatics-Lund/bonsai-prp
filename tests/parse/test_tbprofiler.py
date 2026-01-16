"""Test parsing of TbProfiler results."""


from prp.models.base import ParserOutput
from prp.models.enums import AnalysisType
from prp.models.phenotype import ElementTypeResult
from prp.models.typing import LineageInformation
from prp.parse.tbprofiler import TbProfilerParser


def test_tbprofier_parser_results(mtuberculosis_tbprofiler_path):
    """Test that the TbProfilerParser produces the expected result and data types."""

    parser = TbProfilerParser()
    result = parser.parse(mtuberculosis_tbprofiler_path)

    # test that result is method index
    assert isinstance(result, ParserOutput)

    # verify that parser produces what it say it should
    assert all(at in parser.produces for at in result.results.keys())

    res = result.results[AnalysisType.AMR]
    assert isinstance(res, ElementTypeResult)

    res = result.results[AnalysisType.LINEAGE]
    assert isinstance(res, list)
    assert isinstance(res[0], LineageInformation)
