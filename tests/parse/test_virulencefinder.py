"""Virulencefinder parser test suite."""

from prp.models.base import ParserOutput
from prp.models.enums import AnalysisType
from prp.models.typing import TypingResultGeneAllele
from prp.parse.virulencefinder import VirulenceFinderParser


def test_virulencefinder_parser(ecoli_virulencefinder_stx_pred_stx_path):
    """Test parsing of virulencefinder stx typing prediction."""

    parser = VirulenceFinderParser()
    result = parser.parse(ecoli_virulencefinder_stx_pred_stx_path, strict=True)

    # assert correct ouptut data model
    assert isinstance(result, ParserOutput)

    # verify that parser produces what it say it should
    assert all(at in parser.produces for at in result.results.keys())

    # test that all genes are identified
    vir_res = result.results[AnalysisType.VIRULENCE]
    assert len(vir_res.genes) == 29

    # test STX prediction returns the expected results
    stx_res = result.results[AnalysisType.STX]
    assert isinstance(stx_res, TypingResultGeneAllele)

    assert stx_res.gene_symbol == "stx2"