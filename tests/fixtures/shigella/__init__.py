"""Fixtures for Shigella."""
import pytest

from ..fixtures import data_path


@pytest.fixture()
def shigella_shigapass_path(data_path):
    """Get path for Shigapass results for shigella."""
    return str(data_path.joinpath("shigella", "shigapass.csv"))
