"""Virulencefinder parser test suite."""

import pytest

from prp.parse.amrfinder import (
    AMRMethodIndex,
    ElementType,
    VirulenceMethodIndex,
    parse_amr_pred,
    parse_vir_pred,
)


def test_parse_virulence_prediction(saureus_amrfinder_path):
    """Test parsing amrfinder resistance."""
    # parse result
    result = parse_vir_pred(saureus_amrfinder_path)

    # test that result is method index
    assert isinstance(result, VirulenceMethodIndex)

    # test that all genes are identified
    assert len(result.result.genes) == 14


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


@pytest.mark.parametrize("fixture_name,expected", EXPECTED_RESULT)
def test_parse_amr_prediction(fixture_name, expected, request):
    """Test parsing amrfinder resistance."""
    exp_genes, exp_variants, exp_phenotypes = expected
    filename = request.getfixturevalue(fixture_name)
    # parse result
    result = parse_amr_pred(filename, ElementType.AMR)

    # test that result is method index
    assert isinstance(result, AMRMethodIndex)

    # test that all genes and variants are identified
    assert len(result.result.genes) == exp_genes

    # test that all genes and variants are identified
    assert len(result.result.variants) == exp_variants

    # test that all phenotypes have been reported
    assert set(result.result.phenotypes["resistant"]) == set(exp_phenotypes)
