"""Test fixtures."""

from datetime import datetime

from prp.models.metadata import PipelineInfo, PipelineProvenance, PipelineRun, SequencingInfo
from prp.models.sample import PipelineResult
from prp.parse.core.registry import _PARSER_REGISTRY, _RESULT_MODEL_REGISTRY

from .fixtures import *


@pytest.fixture()
def data_path() -> Path:
    """Get path of this file"""
    return Path(__file__).parent / "fixtures"


@pytest.fixture(autouse=True)
def clear_registry_before_each_test():
    """Ensure a clean registry for each test."""
    _PARSER_REGISTRY.clear()
    _RESULT_MODEL_REGISTRY.clear()
    yield
    _PARSER_REGISTRY.clear()
    _RESULT_MODEL_REGISTRY.clear()


@pytest.fixture()
def simple_pipeline_result():
    """Return a basic analysis result."""

    mock_pipeline_info = PipelineInfo(
        pipeline_name="Jasen",
        pipeline_version="0.0.1",
        commit="commit-hash",
        analysis_profile=["test_profile"],
        release_life_cycle="test_release_life_cycle",
        command="nextflow run ...",
        provenance=PipelineProvenance()
    )
    run_info = PipelineRun(
        pipeline_run_id="run-id",
        executed_at=datetime.now(),
        assay="test-assay",
        pipeline_info=mock_pipeline_info,
    )
    seq_info = SequencingInfo(
        sequencing_run_id="run-id",
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
        pipeline=run_info,
        qc=[],
        species_prediction=[],
        typing_result=[],
        element_type_result=[],
    )


@pytest.fixture()
def bootstap_config_valid(tmp_path: Path) -> Path:
    """Create a valid bootstrap config."""
    cfg = tmp_path / "default.yaml"
    cfg.write_text(
        """
        users:
          - username: user
            email: user@mail.com
            password: user123
            role: [user]
        groups:
          - group_id: mtuberculosis
            display_name: "M. tuberculosis"
            description: "Tuberculosis test samples"
    """, encoding="utf-8")
    return cfg