"""Test typing method parsing."""

import pytest

from prp.parse.models.base import ParserOutput, ResultEnvelope
from prp.parse.models.enums import AnalysisType, ChewbbacaErrors
from prp.parse.models.typing import TypingResultCgMlst
from prp.parse.parsers.chewbacca import ChewbbacaParser, replace_cgmlst_errors

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

    res = replace_cgmlst_errors(
        called_allele, include_novel_alleles=False, correct_alleles=False
    )
    assert res == expected


@pytest.mark.parametrize(
    "called_allele,expected",
    [*cgmlst_test_base, *cgmlst_test_include_novel, *cgmlst_test_not_replace_errors],
)
def test_replace_cgmlst_errors_include_novel(called_allele, expected):
    """Test function that process Chewbbaca allele calling."""

    res = replace_cgmlst_errors(
        called_allele, include_novel_alleles=True, correct_alleles=False
    )
    assert res == expected


@pytest.mark.parametrize(
    "called_allele,expected",
    [*cgmlst_test_base, *cgmlst_test_include_novel, *cgmlst_test_replace_errors],
)
def test_replace_cgmlst_errors_include_novel_and_correct_allels(
    called_allele, expected
):
    """Test function that process Chewbbaca allele calling."""

    res = replace_cgmlst_errors(
        called_allele, include_novel_alleles=True, correct_alleles=True
    )
    assert res == expected


def test_chewbbaca_parser(saureus_chewbbaca_path):
    """Test ChewbbacaParser."""

    parser = ChewbbacaParser()
    result = parser.parse(saureus_chewbbaca_path)

    # assert correct ouptut data model
    assert isinstance(result, ParserOutput)

    # verify that parser produces what it say it should
    assert all(at in parser.produces for at in result.results.keys())

    res = result.results[AnalysisType.CGMLST]
    assert isinstance(res, ResultEnvelope)
    assert res.status == "parsed"

    assert isinstance(res.value, TypingResultCgMlst)
    # v3.4.0 format uses INF- prefix; n_novel should be a counted integer
    assert isinstance(res.value.n_novel, int)
    assert res.value.n_novel > 0


def test_chewbbaca_parser_legacy_format():
    """Test ChewbbacaParser with v3.3.2-style output (no INF- prefix).

    In chewbbaca <v3.4, novel alleles are reported as plain integers,
    making them indistinguishable from known alleles.  n_novel should
    be None rather than a misleading 0.
    """
    import io

    legacy_tsv = "FILE\tLOCUS1\tLOCUS2\tLOCUS3\tLOCUS4\n" "sample\t1\t802\t5\tLNF\n"

    parser = ChewbbacaParser()
    result = parser.parse(io.StringIO(legacy_tsv))

    res = result.results[AnalysisType.CGMLST]
    assert res.status == "parsed"
    assert res.value.n_novel is None
    assert res.value.n_missing == 1
