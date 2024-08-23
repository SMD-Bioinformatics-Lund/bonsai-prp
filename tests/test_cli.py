"""Test PRP cli functions."""

import json
from typing import Literal

from click.testing import CliRunner

from prp.cli import (
    annotate_delly,
    create_bonsai_input,
    create_cdm_input,
    add_igv_annotation_track,
)
from prp.models import PipelineResult
from prp.models.base import RWModel
from prp.models.phenotype import ElementType


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
        args = [
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
            "--output",
            output_file,
        ]
        result = runner.invoke(create_bonsai_input, args)
        assert result.exit_code == 0

        # test that the correct output was generated
        with open(output_file) as inpt:
            prp_output = json.load(inpt)
        # get prediction softwares in ouptut
        prediction_sw = {res["software"] for res in prp_output["element_type_result"]}

        # Test
        # ====

        # 1. that resfinder, amrfinder and virulence finder result is in output
        assert len({"resfinder", "amrfinder", "virulencefinder"} & prediction_sw) == 3

        # 2. that the output datamodel can be used to format input data as well
        output_data_model = PipelineResult(**prp_output)
        assert prp_output == json.loads(output_data_model.model_dump_json())


def test_create_output_ecoli(
    ecoli_analysis_meta_path,
    ecoli_quast_path,
    ecoli_bwa_path,
    ecoli_amrfinder_path,
    ecoli_resfinder_path,
    ecoli_resfinder_meta_path,
    ecoli_virulencefinder_stx_pred_no_stx_path,
    ecoli_virulencefinder_meta_path,
    ecoli_serotypefinder_path,
    ecoli_serotypefinder_meta_path,
    ecoli_mlst_path,
    ecoli_chewbbaca_path,
    ecoli_shigapass_path,
):
    """Test creating a analysis summary using E.coli data.

    The test is intended as an end-to-end test.
    """
    sample_id = "test_ecoli_1"
    output_file = f"{sample_id}.json"
    runner = CliRunner()
    with runner.isolated_filesystem():
        args = [
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
            ecoli_virulencefinder_stx_pred_no_stx_path,
            "--serotypefinder",
            ecoli_serotypefinder_path,
            "--process-metadata",
            ecoli_resfinder_meta_path,
            "--process-metadata",
            ecoli_virulencefinder_meta_path,
            "--process-metadata",
            ecoli_serotypefinder_meta_path,
            "--mlst",
            ecoli_mlst_path,
            "--cgmlst",
            ecoli_chewbbaca_path,
            "--shigapass",
            ecoli_shigapass_path,
            "--output",
            output_file,
        ]
        result = runner.invoke(create_bonsai_input, args)
        # test successful execution
        assert result.exit_code == 0

        # test that the correct output was generated
        with open(output_file) as inpt:
            prp_output = json.load(inpt)

        # get prediction softwares in ouptut
        prediction_sw = {res["software"] for res in prp_output["element_type_result"]}

        # Test
        # ====

        # 1. that resfinder, amrfinder and virulence finder result is in output
        assert len({"resfinder", "amrfinder", "virulencefinder"} & prediction_sw) == 3

        # 2. that the output datamodel can be used to format input data as well
        output_data_model = PipelineResult(**prp_output)
        assert prp_output == json.loads(output_data_model.model_dump_json())


def test_cdm_input_cmd(
    ecoli_quast_path, ecoli_bwa_path, ecoli_chewbbaca_path, ecoli_cdm_input
):
    """Test command for creating CDM input."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        output_fname = "test_ouptut"
        args = [
            "--quast",
            ecoli_quast_path,
            "--quality",
            ecoli_bwa_path,
            "--cgmlst",
            ecoli_chewbbaca_path,
            "--output",
            output_fname,
        ]
        result = runner.invoke(create_cdm_input, args)

        # test successful execution of command
        assert result.exit_code == 0

        # test correct output format
        with open(output_fname, "rb") as inpt:
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
        with open(
            output_fname, "r", encoding="utf-8"
        ) as test_annotated_delly_output, open(
            annotated_delly_path, "r", encoding="utf-8"
        ) as annotated_delly_output:
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


def test_create_output_mtuberculosis(
    mtuberculosis_analysis_meta_path,
    mtuberculosis_bracken_path,
    mtuberculosis_bwa_path,
    mtuberculosis_mykrobe_path,
    mtuberculosis_snv_vcf_path,
    mtuberculosis_sv_vcf_path,
    mtuberculosis_quast_path,
    mtuberculosis_tbprofiler_path,
):
    """Test creating a analysis summary using M. tuberculosis data.

    The test is intended as an end-to-end test.
    """
    sample_id = "test_mtuberculosis_1"
    output_file = f"{sample_id}.json"
    runner = CliRunner()
    with runner.isolated_filesystem():
        args = [
            "-i",
            sample_id,
            "--run-metadata",
            mtuberculosis_analysis_meta_path,
            "--kraken",
            mtuberculosis_bracken_path,
            "--quality",
            mtuberculosis_bwa_path,
            "--mykrobe",
            mtuberculosis_mykrobe_path,
            "--snv-vcf",
            mtuberculosis_snv_vcf_path,
            "--sv-vcf",
            mtuberculosis_sv_vcf_path,
            "--quast",
            mtuberculosis_quast_path,
            "--tbprofiler",
            mtuberculosis_tbprofiler_path,
            "--output",
            output_file,
        ]
        result = runner.invoke(create_bonsai_input, args)
        assert result.exit_code == 0

        # test that the correct output was generated
        with open(output_file) as inpt:
            prp_output = json.load(inpt)
        # get prediction softwares in ouptut
        prediction_sw = {res["software"] for res in prp_output["element_type_result"]}

        # Test
        # ====

        # 1. that resfinder, amrfinder and virulence finder result is in output
        assert len({"mykrobe", "tbprofiler"} & prediction_sw) == 2

        # 2. that the output datamodel can be used to format input data as well
        output_data_model = PipelineResult(**prp_output)
        assert prp_output == json.loads(output_data_model.model_dump_json())
