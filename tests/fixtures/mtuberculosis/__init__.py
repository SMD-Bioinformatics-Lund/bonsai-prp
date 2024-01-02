"""mtuberculosis input data fixutres."""

import pytest

from ..fixtures import data_path


@pytest.fixture()
def mtuberculosis_analysis_meta_path(data_fpath):
    """Get path for mtuberculosis meta file"""
    return str(data_fpath.joinpath("mtuberculosis", "analysis_meta.json"))


@pytest.fixture()
def mtuberculosis_bracken_path(data_fpath):
    """Get path for mtuberculosis bracken file"""
    return str(data_fpath.joinpath("mtuberculosis", "bracken.out"))


@pytest.fixture()
def mtuberculosis_bwa_path(data_fpath):
    """Get path for mtuberculosis bwa qc file"""
    return str(data_fpath.joinpath("mtuberculosis", "bwa.qc"))


@pytest.fixture()
def mtuberculosis_mykrobe_path(data_fpath):
    """Get path for mtuberculosis mykrobe file"""
    return str(data_fpath.joinpath("mtuberculosis", "mykrobe.csv"))


@pytest.fixture()
def mtuberculosis_quast_path(data_fpath):
    """Get path for mtuberculosis quast file"""
    return str(data_fpath.joinpath("mtuberculosis", "quast.tsv"))


@pytest.fixture()
def mtuberculosis_tbprofiler_path(data_fpath):
    """Get path for mtuberculosis tbprofiler file"""
    return str(data_fpath.joinpath("mtuberculosis", "tbprofiler.json"))
