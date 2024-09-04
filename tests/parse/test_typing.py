"""Test typing method parsing."""

import pytest
import logging
from prp.parse.typing import replace_cgmlst_errors
from prp.models.typing import ChewbbacaErrors

# build test cases for handeling chewbacca allele caller errors and annotations
# reference, https://chewbbaca.readthedocs.io/en/latest/user/modules/AlleleCall.html
cgmlst_test_base = [("1", 1), ("99", 99)]  # normal alllale calls
cgmlst_test_include_novel = [("INF-1", 1), ("INF-99", 99), ("*1", 1), ("*99", 99)]  # inferred alleles
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