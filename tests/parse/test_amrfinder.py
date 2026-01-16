"""Virulencefinder parser test suite."""

import pytest

from prp.models.base import AnalysisType, ParserOutput
from prp.parse.amrfinder import AmrFinderParser


EXPECTED_RESULT = [
    (
        "saureus_amrfinder_path",
        (
            8,
            3,
            (
                "beta-lactam",
                "fosfomycin",
                "methicillin",
                "quinolone",
                "tetracycline",
                "tigecycline",
            ),
        ),
    ),
    ("saureus_amrfinder_no_amr_path", (0, 0, tuple())),
]


EXPECTED_AMRFINDER_RESULT = [
    (
        "saureus_amrfinder_path",
        (
            14,  # virulence genes
            8,   # amr genes
            3,   # amr variants
            (
                "beta-lactam",
                "fosfomycin",
                "methicillin",
                "quinolone",
                "tetracycline",
                "tigecycline",
            ),
        ),
    ),
    ("saureus_amrfinder_no_amr_path", (0, 0, 0, tuple())),
]


@pytest.mark.parametrize("fixture_name,expected", EXPECTED_AMRFINDER_RESULT)
def test_amrfinder_parser_results(fixture_name, expected, request):
    """Test parsing amrfinder resistance."""
    exp_vir_genes, exp_genes, exp_variants, exp_phenotypes = expected
    filename = request.getfixturevalue(fixture_name)

    # parse result
    parser = AmrFinderParser()
    result = parser.parse(source=filename)

    # test that result is method index
    assert isinstance(result, ParserOutput)

    # test that result contain the expected types 
    result_types = list(result.results.keys())
    assert all(method in result_types for method in ["amr", "stress", "virulence"])

    # test that all virulence genes were parsed
    assert len(result.results["virulence"].genes) == exp_vir_genes

    # test that all genes, variants, and phenotypes are identified
    assert len(result.results["amr"].genes) == exp_genes
    assert len(result.results["amr"].variants) == exp_variants
    assert set(result.results["amr"].phenotypes["resistant"]) == set(exp_phenotypes)


def test_amrfinder_parser_filter(saureus_amrfinder_path):
    """Test that filtering of AMRfinder results works."""
    selected_result = AnalysisType.AMR
    with open(saureus_amrfinder_path) as intp:
        parser = AmrFinderParser()
        result = parser.parse(stream=intp, want=selected_result)

    assert list(result.results.keys()) == [selected_result.value]
    