"""Virulencefinder parser test suite."""
# import pytest

from prp.models.typing import TypingResultGeneAllele
from prp.parse.phenotype.virulencefinder import parse_virulencefinder_vir_pred, VirulenceMethodIndex
from prp.parse.typing import parse_virulencefinder_stx_typing


# @pytest.mark.parametrize("input", indirect=["ecoli_virulencefinder_wo_sxt_path"])
def test_parse_virulencefinder_output(ecoli_virulencefinder_stx_pred_stx_path):
    """Test parsing virulencefinder output json file."""
    result = parse_virulencefinder_vir_pred(ecoli_virulencefinder_stx_pred_stx_path)

    # test that result is method index
    assert isinstance(result, VirulenceMethodIndex)
    # test that all genes are identified
    assert len(result.result.genes) == 26


def test_parse_stx_typing(
    ecoli_virulencefinder_stx_pred_no_stx_path, ecoli_virulencefinder_stx_pred_stx_path
):
    """Test parsing of virulencefinder stx typing prediction."""

    # If stx gene is not found result should be Null
    res = parse_virulencefinder_stx_typing(ecoli_virulencefinder_stx_pred_no_stx_path)
    assert res is None

    # If stx gene is found result should be instance of typingMethod
    res = parse_virulencefinder_stx_typing(ecoli_virulencefinder_stx_pred_stx_path)
    assert isinstance(res.result, TypingResultGeneAllele)
