"""Ecoli input data fixutres."""

import pytest
import json

from ..fixtures import data_path


@pytest.fixture()
def ecoli_analysis_meta_path(data_path):
    return str(data_path.joinpath("ecoli", "analysis_meta.json"))


@pytest.fixture()
def ecoli_bwa_path(data_path):
    return str(data_path.joinpath("ecoli", "bwa.qc"))


@pytest.fixture()
def ecoli_quast_path(data_path):
    return str(data_path.joinpath("ecoli", "quast.tsv"))


@pytest.fixture()
def ecoli_amrfinder_path(data_path):
    return str(data_path.joinpath("ecoli", "amrfinder.out"))


@pytest.fixture()
def ecoli_resfinder_path(data_path):
    return str(data_path.joinpath("ecoli", "resfinder.json"))


@pytest.fixture()
def ecoli_resfinder_meta_path(data_path):
    return str(data_path.joinpath("ecoli", "resfinder_meta.json"))


@pytest.fixture()
def ecoli_virulencefinder_path(data_path):
    return str(data_path.joinpath("ecoli", "virulencefinder.json"))


@pytest.fixture()
def ecoli_virulencefinder_meta_path(data_path):
    return str(data_path.joinpath("ecoli", "virulencefinder_meta.json"))


@pytest.fixture()
def ecoli_mlst_path(data_path):
    return str(data_path.joinpath("ecoli", "mlst.json"))


@pytest.fixture()
def ecoli_chewbbaca_path(data_path):
    return str(data_path.joinpath("ecoli", "chewbbaca.out"))


@pytest.fixture()
def ecoli_bracken_path(data_path):
    return str(data_path.joinpath("ecoli", "bracken.out"))


@pytest.fixture()
def ecoli_cdm_input(data_path):
    path = data_path.joinpath("ecoli", "cdm_input.json")
    with open(path) as inpt:
        return json.load(inpt)
