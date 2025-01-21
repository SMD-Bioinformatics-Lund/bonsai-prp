"""Virulencefinder parser test suite."""

# import pytest

from prp.parse.amrfinder import (
    AMRMethodIndex,
    VirulenceMethodIndex,
    parse_vir_pred,
    parse_amr_pred
)


def test_parse_virulence_prediction(saureus_amrfinder_path):
    """Test parsing amrfinder resistance."""
    result = parse_vir_pred(saureus_amrfinder_path)

    # test that result is method index
    assert isinstance(result, VirulenceMethodIndex)

    # test that all genes are identified
    assert len(result.result.genes) == 14


def test_parse_amr_prediction(saureus_amrfinder_path):
    """Test parsing amrfinder resistance."""
    result = parse_amr_pred(saureus_amrfinder_path)

    # test that result is method index
    assert isinstance(result, AMRMethodIndex)

    # test that all genes and variants are identified
    assert len(result.result.genes) == 8

    # test that all genes and variants are identified
    assert len(result.result.variants) == 3

    # test that all phenotypes have been reported
    exp_phenotypes = { 
        "beta-lactam",
        "fosfomycin",
        "methicillin",
        "quinolone",
        "tetracycline",
        "tigecycline",
    }
    assert set(result.result.phenotypes['resistant']) == exp_phenotypes