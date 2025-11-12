"""Test parsing of Kleborate results."""

from pathlib import Path
from typing import Any

import pytest

from prp.models.hamronization import HamronizationEntry
from prp.parse import kleborate


def test_parse_kleborate_output(kp_kleborate_path: Path):
    """Test parsing of kleborate output."""

    kleborate.parse_kleborate_v3(kp_kleborate_path, version="3.1.3")


def test_hamronization_to_amr_record(hamronization_entry: HamronizationEntry):
    """Test converting kleborate hAMRonization a PRP resistance record."""

    idx = kleborate.hamronization_to_restance_entry([hamronization_entry])


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
