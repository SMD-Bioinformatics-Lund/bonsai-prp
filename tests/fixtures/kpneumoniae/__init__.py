"""Keep track of Klebsiella pneumoniae fixtures."""

import pytest
from pathlib import Path

@pytest.fixture()
def kp_kleborate_path(data_path: Path):
    """Get path for kleborate result file"""
    return str(data_path.joinpath("kpneumoniae", "kleborate_v3_kpsc_output.txt"))