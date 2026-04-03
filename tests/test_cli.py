"""Test PRP cli functions."""

import json
from pathlib import Path
from typing import Any

import pytest
from click.testing import CliRunner

from prp.cli.parse import format_cdm, format_results
from prp.models.sample import PipelineResult


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

