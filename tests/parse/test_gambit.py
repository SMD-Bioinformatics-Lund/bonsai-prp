"""Test gambit parsing."""


from prp.models.base import ParserOutput
from prp.models.enums import AnalysisType
from prp.models.qc import GambitcoreQcResult
from prp.parse.gambit import GambitCoreParser


def test_gambit_parser(ecoli_gambitcore_path):
    """Test quast parser."""
    parser = GambitCoreParser()
    result = parser.parse(ecoli_gambitcore_path)

    # test that result is method index
    assert isinstance(result, ParserOutput)

    # verify that parser produces what it say it should
    assert all(at in parser.produces for at in result.results.keys())

    assert isinstance(result.results[AnalysisType.QC], GambitcoreQcResult)

    assert result.results[AnalysisType.QC].assembly_core == 2852
    assert result.results[AnalysisType.QC].species_core == 2864