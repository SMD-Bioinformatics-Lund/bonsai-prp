"""Test Mykrobe parser."""


from prp.models.base import ParserOutput
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