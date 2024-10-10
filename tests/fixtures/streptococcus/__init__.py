"""Fixtures for Streptococcus."""
import pytest

from ..fixtures import data_path


@pytest.fixture()
def streptococcus_emmtyper_path(data_path):
    """Get path for Emmtyper results for streptococcus."""
    return str(data_path.joinpath("streptococcus", "emmtyper.tsv"))
