"""Test fixtures."""

from datetime import datetime

from prp.models import PipelineResult
from prp.models.metadata import PipelineInfo, SequencingInfo

from .fixtures import *


@pytest.fixture()
def simple_pipeline_result():
    """Return a basic analysis result."""

    mock_pipeline_info = PipelineInfo(
        pipeline="Jasen",
        version="0.0.1",
        commit="commit-hash",
        analysis_profile=["test_profile"],
        assay="test_assay",
        release_life_cycle="test_release_life_cycle",
        configuration_files=[],
        workflow_name="workflow-name",
        command="nextflow run ...",
        softwares=[],
        date=datetime.now(),
    )
    seq_info = SequencingInfo(
        run_id="run-id",
        platform="sequencing plattform",
        instrument="illumina",
        date=datetime.now(),
    )
    # add run into to metadata model
    return PipelineResult(
        sample_id="mock-sample-001",
        sample_name="sample-name",
        lims_id="limbs id",
        sequencing=seq_info,
        pipeline=mock_pipeline_info,
        qc=[],
        species_prediction=[],
        typing_result=[],
        element_type_result=[],
    )
