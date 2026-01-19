"""Test parsing of Kleborate results."""

from pathlib import Path

from prp.models.base import ParserOutput, ResultEnvelope
from prp.models.enums import AnalysisType
from prp.models.hamronization import HamronizationEntry
from prp.parse.hamronization import HAmrOnizationParser


def test_parse_hamronization(kp_kleborate_hamronization_path: Path):
    """Test parsing kleborate AMR predictions in hamronization format."""

    parser = HAmrOnizationParser()
    result = parser.parse(kp_kleborate_hamronization_path)

    # test that result is method index
    assert isinstance(result, ParserOutput)

    # verify that parser produces what it say it should
    assert all(at in parser.produces for at in result.results.keys())

    res = result.results[AnalysisType.AMR]
    assert isinstance(res, ResultEnvelope)
    assert isinstance(res.value, list) and isinstance(res.value[0], HamronizationEntry)
