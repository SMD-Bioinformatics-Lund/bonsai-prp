"""Test PRP cli functions, driven end-to-end through the actual CLI entrypoints."""

import json
from pathlib import Path
from types import SimpleNamespace

from bonsai_libs.api_client.bonsai.models import (
    CreateGroupInput,
    CreateSampleResponse,
    CreateUserInput,
    UploadAnalysisResultResponse,
)
from bonsai_libs.api_client.core.exceptions import ClientError
from click.testing import CliRunner

from prp.cli.bonsai_api import bonsai_bootstrap, bonsai_upload


class _Resp(SimpleNamespace):
    """Stand-in for a bonsai-libs response model."""


class FakeBonsaiClient:
    """Fakes BonsaiApiClient at the HTTP boundary (method signatures match bonsai-libs
    exactly), so the real BonsaiUploadService/steps code runs underneath the CLI."""

    def __init__(self, *, existing_users=(), existing_groups=(), existing_genomes=()):
        self.existing_users = set(existing_users)
        self.existing_groups = set(existing_groups)
        self.existing_genomes = list(existing_genomes)
        self.calls: list[tuple] = []

    def authenticate_user(self, username: str, password: str, *, headers=None) -> bool:
        return True

    # --- users / groups / reference genomes (bootstrap) ---

    def get_user(self, username: str, *, headers=None):
        if username not in self.existing_users:
            raise ClientError("not found", status=404)
        return {"username": username}

    def create_user(self, user: CreateUserInput, *, headers=None):
        self.existing_users.add(user.username)
        self.calls.append(("create_user", user))
        return {"username": user.username}

    def get_group(self, group_id: str, *, headers=None):
        if group_id not in self.existing_groups:
            raise ClientError("not found", status=404)
        return {"id": group_id}

    def create_group(self, group: CreateGroupInput, *, headers=None):
        self.existing_groups.add(group.group_id)
        self.calls.append(("create_group", group))
        return {"id": group.group_id}

    def request_json(self, method, path, *, json=None, expected_status=(200,)):
        assert path == "reference-genomes"
        if method == "GET":
            return _Resp(data=self.existing_genomes)
        self.calls.append(("create_reference_genome", json))
        return _Resp(data={**json, "id": "genome-1"})

    # --- sample upload ---

    def create_sample(self, sample_info, *, headers=None):
        self.calls.append(("create_sample", sample_info))
        return CreateSampleResponse(
            inserted_id="inserted-1",
            internal_sample_id="internal-1",
            external_sample_id=sample_info.sample_id,
        )

    def add_reference_genome_to_sample(
        self, sample_id, *, reference_genome_id, headers=None
    ):
        self.calls.append(("add_reference_genome_to_sample", reference_genome_id))
        return {"reference_genome_id": reference_genome_id}

    def add_annotation_track_to_sample(self, sample_id, *, track, headers=None):
        self.calls.append(("add_annotation_track_to_sample", track))
        return {"ok": True}

    def add_pipeline_run(self, sample_id, *, pipeline_run, headers=None):
        self.calls.append(("add_pipeline_run", pipeline_run))
        return "pipeline-run-1"

    def upload_ska_index(self, sample_id, *, index_path, force=False, headers=None):
        self.calls.append(("upload_ska_index", index_path))
        return "ok"

    def upload_sourmash_signature(
        self, sample_id, *, signature_file, filename="signature.json", headers=None
    ):
        self.calls.append(("upload_sourmash_signature", filename))
        return "ok"

    def upload_analysis_result(self, result, *, headers=None, force=False):
        self.calls.append(("upload_analysis_result", result.software, force))
        return UploadAnalysisResultResponse(
            sample_id=result.sample_id,
            pipeline_run_id=result.pipeline_run_id,
            analysis_id="an-1",
            software=result.software,
            software_version=result.software_version,
            envelopes={},
        )


def _write_manifest(tmp_path: Path, *, only_mode: bool = False) -> Path:
    """Write a full, valid manifest (+ companion files) to tmp_path and return its path."""
    (tmp_path / "run_info.json").write_text(
        json.dumps(
            {
                "pipeline": "jasen",
                "version": "2.1.0",
                "commit": "abc123",
                "release_life_cycle": "production",
                "workflow_name": "run-42",
                "assay": "saureus",
                "date": "2026-01-01T00:00:00",
                "command": "nextflow run jasen",
                "analysis_profile": ["mlst"],
                "configuration_files": ["nextflow.config"],
                "sequencing_run": "240112_A00001",
                "sequencing_platform": "illumina",
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / "mlst.tsv").write_text("placeholder\n", encoding="utf-8")
    (tmp_path / "index.ska").write_text("placeholder\n", encoding="utf-8")
    (tmp_path / "sig.sourmash").write_text("placeholder\n", encoding="utf-8")
    (tmp_path / "track.bed").write_text("placeholder\n", encoding="utf-8")
    (tmp_path / "sccmec.csv").write_text(
        "gene,type\nmecA,SCCmec IV\n", encoding="utf-8"
    )

    manifest = tmp_path / "manifest.yml"
    manifest.write_text(
        f"""
sample_id: {"cli-test-sample-existing" if only_mode else "cli-test-sample-001"}
sample_name: CLI Test Sample
lims_id: lims-cli-1
groups: [saureus]
metadata:
  - fieldname: host
    value: human
    type: string
  - fieldname: sccmec
    value: ./sccmec.csv
    type: table
reference_genome_id: ref-genome-1
nextflow_run_info: ./run_info.json
analysis_result:
  - software: mlst
    software_version: "2.0"
    uri: ./mlst.tsv
index_artifacts:
  ska_index: ./index.ska
  sourmash_signature: ./sig.sourmash
igv_annotations:
  - type: annotation
    uri: ./track.bed
""",
        encoding="utf-8",
    )
    return manifest


def test_bonsai_upload_full_flow(monkeypatch, tmp_path: Path):
    """`bonsai upload` walks the real create_sample/reference_genome/pipeline_run/
    index/annotation_track/analysis_result steps end-to-end."""
    manifest = _write_manifest(tmp_path)
    client = FakeBonsaiClient()
    monkeypatch.setattr(
        "prp.cli.bonsai_api.make_bonsai_client", lambda base_url: client
    )

    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(
            bonsai_upload,
            [str(manifest), "-a", "http://api:8000", "-u", "admin", "-p", "secret"],
        )

    assert result.exit_code == 0, result.output
    called = [c[0] for c in client.calls]
    assert called == [
        "create_sample",
        "add_reference_genome_to_sample",
        "add_pipeline_run",
        "upload_ska_index",
        "upload_sourmash_signature",
        "add_annotation_track_to_sample",
        "upload_analysis_result",
    ]


def test_bonsai_upload_only_flag(monkeypatch, tmp_path: Path):
    """`--only` uploads just the named software, with force, and skips every other step."""
    manifest = _write_manifest(tmp_path, only_mode=True)
    client = FakeBonsaiClient()
    monkeypatch.setattr(
        "prp.cli.bonsai_api.make_bonsai_client", lambda base_url: client
    )

    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(
            bonsai_upload,
            [
                str(manifest),
                "-a",
                "http://api:8000",
                "-u",
                "admin",
                "-p",
                "secret",
                "--only",
                "mlst",
                "--force",
            ],
        )

    assert result.exit_code == 0, result.output
    assert [c[0] for c in client.calls] == ["upload_analysis_result"]
    assert client.calls[0][1:] == ("mlst", True)


def test_bootstrap_happy_path_calls_ensure_methods(monkeypatch, bootstap_config_valid):
    """Bootstrap CLI drives the real BonsaiUploadService.ensure_* methods."""
    client = FakeBonsaiClient()
    monkeypatch.setattr(
        "prp.cli.bonsai_api.make_bonsai_client", lambda base_url: client
    )

    runner = CliRunner()
    with runner.isolated_filesystem():
        cfg_path = str(bootstap_config_valid.absolute())
        result = runner.invoke(
            bonsai_bootstrap,
            [cfg_path, "-a", "http://api:8000", "-u", "admin", "-p", "secret"],
        )

    assert result.exit_code == 0, result.output

    call_types = [c[0] for c in client.calls]
    assert call_types == ["create_user", "create_group", "create_reference_genome"]
    assert isinstance(client.calls[0][1], CreateUserInput)
    assert isinstance(client.calls[1][1], CreateGroupInput)
    assert isinstance(client.calls[2][1], dict)  # genome_data.model_dump()


def test_bootstrap_skips_existing_users_and_groups(monkeypatch, bootstap_config_valid):
    """Bootstrap treats an already-existing user/group/genome as a no-op, not a create."""
    client = FakeBonsaiClient(
        existing_users={"user"},
        existing_groups={"mtuberculosis"},
        existing_genomes=[
            {
                "id": "existing-genome",
                "name": "mtuberculosis",
                "accession": "TEST123",
                "organism": "Mycobacterium tubcerculosis",
            }
        ],
    )
    monkeypatch.setattr(
        "prp.cli.bonsai_api.make_bonsai_client", lambda base_url: client
    )

    runner = CliRunner()
    with runner.isolated_filesystem():
        cfg_path = str(bootstap_config_valid.absolute())
        result = runner.invoke(
            bonsai_bootstrap,
            [cfg_path, "-a", "http://api:8000", "-u", "admin", "-p", "secret"],
        )

    assert result.exit_code == 0, result.output
    assert client.calls == []
