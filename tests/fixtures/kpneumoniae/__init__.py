"""Keep track of Klebsiella pneumoniae fixtures."""

from pathlib import Path

import pytest


@pytest.fixture()
def kp_kleborate_path(data_path: Path) -> Path:
    """Get path for kleborate result file"""
    return data_path.joinpath("kpneumoniae", "kleborate_v3_kpsc_output.txt")