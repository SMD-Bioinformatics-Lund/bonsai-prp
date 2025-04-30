"""Test PRP cli functions."""

import json

import pytest
from click.testing import CliRunner

from prp.cli.parse import format_jasen, format_cdm
from prp.cli.annotate import add_igv_annotation_track, annotate_delly
from prp.models import PipelineResult


@pytest.mark.parametrize(
    "fixture_name,expected_sw",
    [
        ("saureus_sample_conf_path", ["resfinder", "amrfinder", "virulencefinder"]),
        ("ecoli_sample_conf_path", ["resfinder", "amrfinder", "virulencefinder"]),
        ("mtuberculosis_sample_conf_path", ["mykrobe", "tbprofiler"]),
    ],
)
def test_parse_cmd(fixture_name, expected_sw, request):
    """Test creating a analysis summary.

    The test is intended as an end-to-end test.
    """
    sample_conf = request.getfixturevalue(fixture_name)
    output_file = "test_output.json"
    runner = CliRunner()
    with runner.isolated_filesystem():
        args = [
            "--sample",
            sample_conf,
            "--output",
            output_file,
        ]
        result = runner.invoke(format_jasen, args)
        assert result.exit_code == 0

        # test that the correct output was generated
        with open(output_file) as inpt:
            prp_output = json.load(inpt)
        # get prediction softwares in ouptut
        prediction_sw = {res["software"] for res in prp_output["element_type_result"]}

        # Test
        # ====

        # 1. that resfinder, amrfinder and virulence finder result is in output
        assert len(set(expected_sw) & prediction_sw) == len(expected_sw)

        # 2. that the output datamodel can be used to format input data as well
        output_data_model = PipelineResult(**prp_output)
        assert prp_output == json.loads(output_data_model.model_dump_json())


def test_cdm_cmd(ecoli_sample_conf_path, ecoli_cdm_input):
    """Test command for creating CDM input."""
    output_file = "test_output.json"
    runner = CliRunner()
    with runner.isolated_filesystem():
        args = [
            "--sample",
            ecoli_sample_conf_path,
            "--output",
            output_file,
        ]
        result = runner.invoke(format_cdm, args)

        # test successful execution of command
        assert result.exit_code == 0

        # test correct output format
        with open(output_file, "rb") as inpt:
            cdm_output = json.load(inpt)
            assert cdm_output == ecoli_cdm_input


def test_annotate_delly(
    mtuberculosis_delly_bcf_path, converged_bed_path, annotated_delly_path
):
    """Test command for annotating delly output."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        sample_id = "test_mtuberculosis_1"
        output_fname = f"{sample_id}_annotated_delly.vcf"
        result = runner.invoke(
            annotate_delly,
            [
                "--vcf",
                mtuberculosis_delly_bcf_path,
                "--bed",
                converged_bed_path,
                "--output",
                output_fname,
            ],
        )

        # test successful execution of command
        assert result.exit_code == 0

        # test correct output format
        with (
            open(output_fname, "r", encoding="utf-8") as test_annotated_delly_output,
            open(annotated_delly_path, "r", encoding="utf-8") as annotated_delly_output,
        ):
            test_contents = test_annotated_delly_output.read()
            expected_contents = annotated_delly_output.read()
            assert test_contents == expected_contents


def test_add_igv_annotation_track(mtuberculosis_snv_vcf_path, simple_pipeline_result):
    """Test command for adding IGV annotation track to a result file."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        result_fname = "before_update.json"
        # write fixture to file
        with open(result_fname, "w") as outp:
            outp.write(simple_pipeline_result.model_dump_json())

        output_fname = "after_update.json"
        args = [
            "--track-name",
            "snv",
            "--annotation-file",
            mtuberculosis_snv_vcf_path,
            "--bonsai-input-file",
            result_fname,
            "--output",
            output_fname,
        ]
        result = runner.invoke(add_igv_annotation_track, args)

        # test successful execution of command
        assert result.exit_code == 0

        # test correct output format
        with open(output_fname, "r", encoding="utf-8") as file_after:
            test_file_after = json.load(file_after)
            n_tracks_before = (
                0
                if simple_pipeline_result.genome_annotation is None
                else len(simple_pipeline_result.genome_annotation)
            )
            assert len(test_file_after["genome_annotation"]) == n_tracks_before + 1
