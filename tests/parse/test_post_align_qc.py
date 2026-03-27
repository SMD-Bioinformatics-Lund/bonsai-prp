"""Test PostAlignQcParser."""

import json

import pytest

from prp.parse.models.base import ParserOutput, ResultEnvelope
from prp.parse.models.enums import AnalysisType
from prp.parse.models.qc import PostAlignQcResult
from prp.parse.parsers.post_align_qc import PostAlignQcParser

FULL_QC = {
    "ins_size": "288.607639",
    "ins_size_dev": "144.314025",
    "pct_above_x": {"1": 99.95, "10": 98.34, "30": 86.12},
    "mean_cov": 95.14,
    "coverage_uniformity": 1.125,
    "quartile1": 43.0,
    "median_cov": 80.0,
    "quartile3": 133.0,
    "n_reads": 1211056,
    "n_mapped_reads": 1014751,
    "n_read_pairs": 1203302,
}

MINIMAL_QC = {
    "n_reads": 500000,
    "n_read_pairs": 498000,
}


def test_post_align_qc_parser_full(tmp_path):
    """Parser handles a complete QC JSON (all fields present)."""
    qc_file = tmp_path / "qc.json"
    qc_file.write_text(json.dumps(FULL_QC))

    result = PostAlignQcParser().parse(qc_file)

    assert isinstance(result, ParserOutput)
    assert all(at in PostAlignQcParser().produces for at in result.results)

    env = result.results[AnalysisType.QC]
    assert isinstance(env, ResultEnvelope)
    assert env.status == "parsed"

    qc = env.value
    assert isinstance(qc, PostAlignQcResult)
    assert qc.n_reads == 1211056
    assert qc.n_read_pairs == 1203302
    assert qc.n_mapped_reads == 1014751
    assert qc.mean_cov == pytest.approx(95.14)
    assert qc.median_cov == 80.0
    assert qc.quartile1 == 43.0
    assert qc.quartile3 == 133.0
    assert qc.pct_above_x is not None


def test_post_align_qc_parser_minimal(tmp_path):
    """Parser succeeds with only n_reads and n_read_pairs; optional fields are None."""
    qc_file = tmp_path / "qc_minimal.json"
    qc_file.write_text(json.dumps(MINIMAL_QC))

    result = PostAlignQcParser().parse(qc_file)
    qc = result.results[AnalysisType.QC].value

    assert isinstance(qc, PostAlignQcResult)
    assert qc.n_reads == 500000
    assert qc.n_read_pairs == 498000
    assert qc.mean_cov is None
    assert qc.n_mapped_reads is None
    assert qc.pct_above_x is None
    assert qc.quartile1 is None
    assert qc.median_cov is None
    assert qc.quartile3 is None
    assert qc.ins_size is None
    assert qc.ins_size_dev is None
