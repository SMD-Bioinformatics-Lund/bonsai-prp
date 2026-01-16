"""Test Mykrobe parser."""


from prp.models.base import ParserOutput
from prp.models.phenotype import ElementTypeResult
from prp.models.typing import ResultLineageBase
from prp.parse.mykrobe import MykrobeParser


def test_mykrobe_parser_results(mtuberculosis_mykrobe_path):
    """Test Mykrobe parser"""

    parser = MykrobeParser()
    result = parser.parse(mtuberculosis_mykrobe_path)

    # test that result is method index
    assert isinstance(result, ParserOutput)

    # test that result contain the expected types
    result_types = list(result.results.keys())
    assert all(method in result_types for method in parser.produces)

    # verify that species prediction was included
    assert len(result.results["species"]) == 1
    assert result.results["species"][0].scientific_name == "Mycobacterium tuberculosis"

    # verify that lineage prediction
    assert isinstance(result.results["lineage"], ResultLineageBase)

    # verify that amr predictions
    pred = result.results["amr"]
    assert isinstance(pred, ElementTypeResult)
    assert len(pred.variants) == 6
