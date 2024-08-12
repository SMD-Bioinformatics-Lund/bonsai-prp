"""Test fixtures."""

from .fixtures import *
from prp.models import PipelineResult
from prp.models.metadata import RunMetadata, RunInformation
from datetime import datetime


@pytest.fixture()
def simple_pipeline_result():
    """Return a basic analysis result."""

    mock_run_info = RunInformation(
        pipeline="Jasen",
        version="0.0.1",
        commit="commit-hash",
        analysis_profile="",
        configuration_files=[],
        workflow_name="workflow-name",
        sample_name="sample-name",
        lims_id="limbs id",
        sequencing_run="run-id",
        sequencing_platform="sequencing plattform",
        sequencing_type="illumina",
        command="nextflow run ...",
        date=datetime.now(),
    )
    # add run into to metadata model
    metadata = RunMetadata(run=mock_run_info, databases=[])
    return PipelineResult(
        sample_id="mock-sample-001",
        run_metadata=metadata,
        qc=[],
        species_prediction=[],
        typing_result=[],
        element_type_result=[],
    )
