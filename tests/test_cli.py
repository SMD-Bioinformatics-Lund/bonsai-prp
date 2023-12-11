"""Test PRP cli functions."""

import json
from click.testing import CliRunner

from prp.cli import create_bonsai_input, create_cdm_input, print_schema


def test_create_output_saureus(
    saureus_analysis_meta_path,
    saureus_quast_path,
    saureus_bwa_path,
    saureus_amrfinder_path,
    saureus_resfinder_path,
    saureus_resfinder_meta_path,
    saureus_virulencefinder_path,
    saureus_virulencefinder_meta_path,
    saureus_mlst_path,
    saureus_chewbbaca_path,
):
    """Test creating a analysis summary using S.aureus data.

    The test is intended as an end-to-end test.
    """
    sample_id = "test_saureus_1"
    output_file = f"{sample_id}.json"
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(
            create_bonsai_input,
            [
                "-i",
                sample_id,
                "--run-metadata",
                saureus_analysis_meta_path,
                "--quality",
                saureus_bwa_path,
                "--quast",
                saureus_quast_path,
                "--amrfinder",
                saureus_amrfinder_path,
                "--resfinder",
                saureus_resfinder_path,
                "--virulencefinder",
                saureus_virulencefinder_path,
                "--process-metadata",
                saureus_resfinder_meta_path,
                "--process-metadata",
                saureus_virulencefinder_meta_path,
                "--mlst",
                saureus_mlst_path,
                "--cgmlst",
                saureus_chewbbaca_path,
                output_file,
            ],
        )
        assert result.exit_code == 0


def test_create_output_ecoli(
    ecoli_analysis_meta_path,
    ecoli_quast_path,
    ecoli_bwa_path,
    ecoli_amrfinder_path,
    ecoli_resfinder_path,
    ecoli_resfinder_meta_path,
    ecoli_virulencefinder_path,
    ecoli_virulencefinder_meta_path,
    ecoli_mlst_path,
    ecoli_chewbbaca_path,
):
    """Test creating a analysis summary using E.coli data.

    The test is intended as an end-to-end test.
    """
    sample_id = "test_ecoli_1"
    output_file = f"{sample_id}.json"
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(
            create_bonsai_input,
            [
                "-i",
                sample_id,
                "--run-metadata",
                ecoli_analysis_meta_path,
                "--quality",
                ecoli_bwa_path,
                "--quast",
                ecoli_quast_path,
                "--amrfinder",
                ecoli_amrfinder_path,
                "--resfinder",
                ecoli_resfinder_path,
                "--virulencefinder",
                ecoli_virulencefinder_path,
                "--process-metadata",
                ecoli_resfinder_meta_path,
                "--process-metadata",
                ecoli_virulencefinder_meta_path,
                "--mlst",
                ecoli_mlst_path,
                "--cgmlst",
                ecoli_chewbbaca_path,
                output_file,
            ],
        )
        assert result.exit_code == 0


def test_cdm_input_cmd(ecoli_quast_path, ecoli_bwa_path, ecoli_chewbbaca_path, ecoli_cdm_input):
    """Test command for creating CDM input."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        output_fname = "test_ouptut"
        result = runner.invoke(
            create_cdm_input,
            [
                "--quast",
                ecoli_quast_path,
                "--quality",
                ecoli_bwa_path,
                "--cgmlst",
                ecoli_chewbbaca_path,
                output_fname,
            ],
        )

        # test successful execution of command
        assert result.exit_code == 0

        # test correct output format
        with open(output_fname) as inpt:
            cmd_output = json.load(inpt)
            assert cmd_output == ecoli_cdm_input