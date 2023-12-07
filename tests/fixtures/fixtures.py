"""General fixtures."""

from pathlib import Path

import pytest


@pytest.fixture()
def data_path():
    conftest_path = Path(__file__)
    return conftest_path.parent
