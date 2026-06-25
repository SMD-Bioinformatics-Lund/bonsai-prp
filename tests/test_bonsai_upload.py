"""Tests for the Bonsai upload service, focused on result-only (`--only`) uploads."""

from pathlib import Path
from types import SimpleNamespace

from prp.bonsai.service import BonsaiUploadService
from prp.bonsai.state_store import UploadStateStore
from prp.models.manifest import URI
from prp.pipeline.types import MinimalAnalysisRecord


class _Resp(SimpleNamespace):
    """Stand-in for the bonsai-libs UploadAnalysisResultResponse."""


class FakeClient:
    """Captures the calls the upload service makes."""

    def __init__(self):
        self.created_samples = 0
        self.pipeline_runs = 0
        self.uploaded = []  # list of (software, force)

    def create_sample(self, *args, **kwargs):
        self.created_samples += 1
        return _Resp(internal_sample_id="should-not-be-used")

    def add_pipeline_run(self, *args, **kwargs):
        self.pipeline_runs += 1

    def upload_analysis_result(self, payload, *, headers=None, force=False):
        self.uploaded.append((payload.software, force))
        return _Resp(
            analysis_id="an-1",
            software=payload.software,
            software_version=payload.software_version,
            envelopes={},
        )


def _record(tmp_path: Path, software: str) -> MinimalAnalysisRecord:
    fpath = tmp_path / f"{software}.tsv"
    fpath.write_text("placeholder\n")
    return MinimalAnalysisRecord(
        software=software,
        software_version="1.0.0",
        uri=URI(scheme="file", path=str(fpath)),
    )


def _results(tmp_path: Path) -> SimpleNamespace:
    return SimpleNamespace(
        sample_id="018f9c2a-internal-uuid",
        analysis_results=[_record(tmp_path, "chewbbaca"), _record(tmp_path, "mlst")],
        pipeline=SimpleNamespace(pipeline_run_id="run-1"),
        annotation_tracks=[],
    )


def test_only_uploads_selected_software_and_skips_sample_creation(tmp_path: Path):
    """`--only chewbbaca` uploads just chewbbaca with force and creates no sample."""
    client = FakeClient()
    service = BonsaiUploadService(
        client=client,
        state_store=UploadStateStore(root=tmp_path / "state"),
        workflow_id="wf-test",
    )

    service.upload_sample(_results(tmp_path), force=True, only={"chewbbaca"})

    # Only chewbbaca is uploaded (mlst filtered out), with force, and no sample
    # creation / pipeline-run steps run.
    assert client.uploaded == [("chewbbaca", True)]
    assert client.created_samples == 0
    assert client.pipeline_runs == 0
