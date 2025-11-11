"""Test parsing of Kleborate results."""

from pathlib import Path

from prp.parse import hamronization


def test_parse_hamronization(kp_kleborate_hamronization_path: Path):
    """Test parsing kleborate AMR predictions in hamronization format."""

    with kp_kleborate_hamronization_path.open() as filep:
        hamronization.parse_hamronization(filep)
