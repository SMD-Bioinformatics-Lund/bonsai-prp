"""Test parsing of Kleborate results."""

from pathlib import Path
from typing import Any

import pytest

from prp.parse import kleborate


def test_parse_kleborate_output(kp_kleborate_path: Path):
    """Test parsing of kleborate output."""

    test_file = Path(kp_kleborate_path)
    kleborate.parse_kleborate_v3(test_file)


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
