"""saureus input data fixutres."""

import pytest

@pytest.fixture()
def saureus_analysis_meta_path(data_path):
    """Get path for saureus meta file"""
    return str(data_path.joinpath("saureus", "analysis_meta.json"))


@pytest.fixture()
def saureus_bwa_path(data_path):
    """Get path for saureus bwa qc file"""
    return str(data_path.joinpath("saureus", "bwa.qc"))


@pytest.fixture()
def saureus_quast_path(data_path):
    """Get path for saureus quast file"""
    return str(data_path.joinpath("saureus", "quast.tsv"))


@pytest.fixture()
def saureus_amrfinder_path(data_path):
    """Get path for saureus amrfinder file"""
    return str(data_path.joinpath("saureus", "amrfinder.out"))


@pytest.fixture()
def saureus_resfinder_path(data_path):
    """Get path for saureus resfinder file"""
    return str(data_path.joinpath("saureus", "resfinder.json"))


@pytest.fixture()
def saureus_resfinder_meta_path(data_path):
    """Get path for saureus resfinder meta file"""
    return str(data_path.joinpath("saureus", "resfinder_meta.json"))


@pytest.fixture()
def saureus_virulencefinder_path(data_path):
    """Get path for saureus virulencefinder file"""
    return str(data_path.joinpath("saureus", "virulencefinder.json"))


@pytest.fixture()
def saureus_virulencefinder_meta_path(data_path):
    """Get path for saureus virulencefinder meta file"""
    return str(data_path.joinpath("saureus", "virulencefinder_meta.json"))


@pytest.fixture()
def saureus_mlst_path(data_path):
    """Get path for saureus mlst file"""
    return str(data_path.joinpath("saureus", "mlst.json"))


@pytest.fixture()
def saureus_chewbbaca_path(data_path):
    """Get path for saureus chewbbaca file"""
    return str(data_path.joinpath("saureus", "chewbbaca.out"))


@pytest.fixture()
def saureus_bracken_path(data_path):
    """Get path for saureus bracken file"""
    return str(data_path.joinpath("saureus", "bracken.out"))
