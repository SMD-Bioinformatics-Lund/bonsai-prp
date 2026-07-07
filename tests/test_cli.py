"""Test PRP cli functions."""

import json
from pathlib import Path
from typing import Any

import pytest
from click.testing import CliRunner

from bonsai_libs.api_client.bonsai.models import (
    CreateUserInput,
    CreateGroupInput,
    CreateReferenceGenomeInput,
)

from prp.cli.parse import format_cdm, format_results
from prp.cli.bonsai_api import bonsai_bootstrap


@pytest.mark.parametrize(
    "fixture_name,expected_sw",
    [
        ("saureus_sample_conf_path", ["resfinder", "amrfinder", "virulencefinder"]),
        ("ecoli_sample_conf_path", ["resfinder", "amrfinder", "virulencefinder"]),
        # ("kp_sample_conf_path", ["kleborate"]),
        ("mtuberculosis_sample_conf_path", ["mykrobe", "tbprofiler"]),
    ],
)
def test_parse_cmd(
    fixture_name: str, expected_sw: list[str], request: pytest.FixtureRequest
):
    """Test creating a analysis summary.

    The test is intended as an end-to-end test.
    """

    # TODO reinstate the test when implementation of manifest v2 is done

    # sample_conf = request.getfixturevalue(fixture_name)
    # output_file = "test_output.json"
    # runner = CliRunner()
    # with runner.isolated_filesystem():
    #     args: list[str] = [
    #         "--sample",
    #         sample_conf,
    #         "--output",
    #         output_file,
    #     ]
    #     result = runner.invoke(format_jasen, args)
    #     assert result.exit_code == 0

    #     # test that the correct output was generated
    #     with open(output_file) as inpt:
    #         prp_output = json.load(inpt)
    #     # get prediction softwares in ouptut
    #     prediction_sw = {res["software"] for res in prp_output["element_type_result"]}

    #     # Test
    #     # ====

    #     # 1. that resfinder, amrfinder and virulence finder result is in output
    #     assert len(set(expected_sw) & prediction_sw) == len(expected_sw)

    #     # 2. that the output datamodel can be used to format input data as well
    #     output_data_model = PipelineResult.model_validate(prp_output)
    #     output_data_model_json = json.loads(output_data_model.model_dump_json())
    #     assert prp_output == output_data_model_json


def test_cdm_cmd(ecoli_sample_conf_path: Path, ecoli_cdm_input: list[dict[str, Any]]):
    """Test command for creating CDM input."""

    # TODO reinstate the test when implementation of manifest v2 is done

    # output_file = "test_output.json"
    # runner = CliRunner()
    # with runner.isolated_filesystem():
    #     args: list[str] = [
    #         "--sample",
    #         str(ecoli_sample_conf_path),
    #         "--output",
    #         output_file,
    #     ]
    #     result = runner.invoke(format_cdm, args)

    #     # test successful execution of command
    #     assert result.exit_code == 0

    #     # test correct output format
    #     with open(output_file, "rb") as inpt:
    #         cdm_output = json.load(inpt)
    #         assert cdm_output == ecoli_cdm_input

def test_bootstrap_happy_path_calls_ensure_methods(monkeypatch, bootstap_config_valid):
    """Test that bootstrap cli calls the expected paths"""
    # --- Fake client ---
    class FakeClient:
        def authenticate_user(self, username, password):
            assert username == "admin"
            assert password == "secret"
            return True

    # --- Capture calls ---
    calls = {"users": [], "groups": [], "reference_genomes": []}

    class FakeService:
        def __init__(self, client, state_store, dry_run=False, **kwargs):
            self.client = client
            self.state_store = state_store
            self.dry_run = dry_run

        def ensure_user_exists(self, user_id, **user_data):
            calls["users"].append((user_id, user_data))
            return {"username": user_id}

        def ensure_group_exists(self, group_id, **group_data):
            calls["groups"].append((group_id, group_data))
            return {"id": group_id}
        
        def ensure_reference_genome_exists(self, genome_data):
            calls["ref_genome"] = genome_data
            return {"id": genome_data}

        def ensure_reference_genome_exists(self, reference_genome, **ref_data):
            calls["reference_genomes"].append((reference_genome, ref_data))
            return {"id": getattr(reference_genome, "accession", None)}

    # Monkeypatch wiring in CLI module

    # 1. make_bonsai_client() returns our fake client
    monkeypatch.setattr("prp.cli.bonsai_api.make_bonsai_client", lambda base_url: FakeClient())
    # 2. BonsaiUploadService is replaced with our fake service
    monkeypatch.setattr("prp.cli.bonsai_api.BonsaiUploadService", FakeService)

    runner = CliRunner()
    with runner.isolated_filesystem():
        # invoke: use default config_file path
        cfg_path = str(bootstap_config_valid.absolute())
        result = runner.invoke(
            bonsai_bootstrap,
            [cfg_path, "-a", "http://api:8000", "-u", "admin", "-p", "secret"],
        )

    assert result.exit_code == 0, result.output

    # --- Verify calls ---
    assert isinstance(calls["users"][0][0], CreateUserInput)
    assert isinstance(calls["groups"][0][0], CreateGroupInput)
    assert isinstance(calls["reference_genomes"][0][0], CreateReferenceGenomeInput)
