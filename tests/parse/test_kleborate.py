"""Test parsing of Kleborate results."""

from pathlib import Path
from typing import Any

import pytest

from prp.models.hamronization import HamronizationEntry
from prp.models.kleborate import KleborateAmrIndex
from prp.models.base import ParserOutput
from prp.models.constants import ElementType
from prp.models.phenotype import PhenotypeInfo
from prp.parse import kleborate


def test_parse_kleborate_output_wo_hamronization(kp_kleborate_path: Path):
    """Test parsing of kleborate output."""

    out = kleborate.parse_kleborate_v3(kp_kleborate_path, version="3.1.3")

    # Test that result in strucutred data
    assert isinstance(out, list)
    assert all(isinstance(e, ParserOutput) for e in out)


def test_parse_kleborate_output_w_hamronization(kp_kleborate_path: Path, hamronization_entry: HamronizationEntry):
    """Test parsing of kleborate output."""

    out = kleborate.parse_kleborate_v3(kp_kleborate_path, hamronization_entries=[hamronization_entry], version="3.1.3")

    # Test that result in strucutred data
    assert isinstance(out, list)

    # Test that hamronization was parsed
    exp_hamronization = out[-1]
    assert isinstance(exp_hamronization, ParserOutput) and isinstance(exp_hamronization.data.result, )

    # Test that target field was set correctly
    assert exp_hamronization.target_field == "element_type_result"


def test_convert_hamronization_to_amr_record(hamronization_entry: HamronizationEntry):
    """Test converting kleborate hAMRonization a PRP resistance record."""

    res = kleborate.hamronization_to_restance_entry([hamronization_entry])

    # Test that result in strucutred data
    assert isinstance(res, KleborateAmrIndex)

    assert res.version == hamronization_entry.analysis_software_version

    # No variants in test data
    assert len(res.result.variants) == 0

    # No gene in test data
    gene = res.result.genes[0]
    assert gene.gene_symbol == hamronization_entry.gene_symbol


def test_get_hamr_phenotype(hamronization_entry: HamronizationEntry):
    """Test building phenotype info."""

    info = kleborate._get_hamr_phenotype(hamronization_entry)

    # Test that result in strucutred data
    assert isinstance(info, PhenotypeInfo)

    # Test that fields were assigned correctly
    assert info.type == ElementType.AMR
    assert info.group == "aminoglycoside antibiotic"
    assert info.name == "aminoglycoside antibiotic"


@pytest.mark.parametrize(
    "path,expected",
    [
        (["foo", "bar", "doo"], {"foo": {"bar": {"doo": "here"}}}),
        (["foo"], {"foo": "here"}),
        (None, None),
    ],
)
def test_set_nested(path: list[str], expected: dict[str, Any]):
    """Test setting values in nested dictionaries."""
    result = kleborate._set_nested({}, path, "here")

    assert result == expected
