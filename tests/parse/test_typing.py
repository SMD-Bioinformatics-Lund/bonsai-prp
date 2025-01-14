"""Test typing method parsing."""

import logging

import pytest

from prp.models.typing import ChewbbacaErrors
from prp.parse.typing import parse_mlst_results, replace_cgmlst_errors

# build test cases for handeling chewbacca allele caller errors and annotations
# reference, https://chewbbaca.readthedocs.io/en/latest/user/modules/AlleleCall.html
cgmlst_test_base = [("1", 1), ("99", 99)]  # normal alllale calls
cgmlst_test_include_novel = [
    ("INF-1", 1),
    ("INF-99", 99),
    ("*1", 1),
    ("*99", 99),
]  # inferred alleles
cgmlst_test_not_include_novel = [
    ("INF-1", "INF-1"),
    ("INF-99", "INF-99"),
]  # inferred alleles
cgmlst_test_replace_errors = [
    (err.value, None) for err in ChewbbacaErrors
]  # errors to strip
cgmlst_test_not_replace_errors = [
    (err.value, err.value) for err in ChewbbacaErrors
]  # errors to strip


@pytest.mark.parametrize(
    "called_allele,expected",
    [
        *cgmlst_test_base,
        *cgmlst_test_not_include_novel,
        *cgmlst_test_not_replace_errors,
    ],
)
def test_replace_cgmlst_errors_not_include_novel(called_allele, expected):
    """Test function that process Chewbbaca allele calling."""

    assert (
        replace_cgmlst_errors(
            called_allele, include_novel_alleles=False, correct_alleles=False
        )
        == expected
    )


@pytest.mark.parametrize(
    "called_allele,expected",
    [*cgmlst_test_base, *cgmlst_test_include_novel, *cgmlst_test_not_replace_errors],
)
def test_replace_cgmlst_errors_include_novel(called_allele, expected):
    """Test function that process Chewbbaca allele calling."""

    assert (
        replace_cgmlst_errors(
            called_allele, include_novel_alleles=True, correct_alleles=False
        )
        == expected
    )


@pytest.mark.parametrize(
    "called_allele,expected",
    [*cgmlst_test_base, *cgmlst_test_include_novel, *cgmlst_test_replace_errors],
)
def test_replace_cgmlst_errors_include_novel_and_correct_allels(
    called_allele, expected
):
    """Test function that process Chewbbaca allele calling."""

    assert (
        replace_cgmlst_errors(
            called_allele, include_novel_alleles=True, correct_alleles=True
        )
        == expected
    )


def test_replace_cgmlst_errors_warnings(caplog):
    """Test that replace_cgmlst_errors warns if allele could not be cast as an integer."""
    caplog.at_level(logging.WARNING)
    # run test that should not trigger a warning
    replace_cgmlst_errors("1", include_novel_alleles=True, correct_alleles=True)
    # check that warning was not triggered
    for record in caplog.records:
        assert record.levelname != "WARNING"

    # run test that a warning was triggered if input is unknown string
    allele = "A_STRANGE_STRING"
    replace_cgmlst_errors(allele, include_novel_alleles=True, correct_alleles=True)
    assert allele in caplog.text


def test_parse_mlst_result(ecoli_mlst_path):
    """Test parsing of MLST result file."""
    # FIRST run result parser
    res_obj = parse_mlst_results(ecoli_mlst_path)

    # THEN verify result type
    assert res_obj.type == "mlst"
    # THEN verify software
    assert res_obj.software == "mlst"
    # THEN verify sequence type and allele assignment
    assert res_obj.result.sequence_type == 58
    assert len(res_obj.result.alleles) == 8


def test_parse_mlst_result_w_no_call(mlst_result_path_no_call):
    """Test parsing of MLST results file where the alleles was not called."""
    # FIRST run result parser
    res_obj = parse_mlst_results(mlst_result_path_no_call)

    # THEN verify that sequence type is None
    assert res_obj.result.sequence_type is None
    assert len(res_obj.result.alleles) == 0
