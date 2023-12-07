"""saureus input data fixutres."""

import pytest

from ..fixtures import data_path


@pytest.fixture()
def saureus_analysis_meta_path(data_path):
    return str(data_path.joinpath("saureus", "analysis_meta.json"))


@pytest.fixture()
def saureus_bwa_path(data_path):
    return str(data_path.joinpath("saureus", "bwa.qc"))


@pytest.fixture()
def saureus_quast_path(data_path):
    return str(data_path.joinpath("saureus", "quast.tsv"))


@pytest.fixture()
def saureus_amrfinder_path(data_path):
    return str(data_path.joinpath("saureus", "amrfinder.out"))


@pytest.fixture()
def saureus_resfinder_path(data_path):
    return str(data_path.joinpath("saureus", "resfinder.json"))


@pytest.fixture()
def saureus_resfinder_meta_path(data_path):
    return str(data_path.joinpath("saureus", "resfinder_meta.json"))


@pytest.fixture()
def saureus_virulencefinder_path(data_path):
    return str(data_path.joinpath("saureus", "virulencefinder.json"))


@pytest.fixture()
def saureus_virulencefinder_meta_path(data_path):
    return str(data_path.joinpath("saureus", "virulencefinder_meta.json"))


@pytest.fixture()
def saureus_mlst_path(data_path):
    return str(data_path.joinpath("saureus", "mlst.json"))


@pytest.fixture()
def saureus_chewbbaca_path(data_path):
    return str(data_path.joinpath("saureus", "chewbbaca.out"))


@pytest.fixture()
def saureus_bracken_path(data_path):
    return str(data_path.joinpath("saureus", "bracken.out"))
