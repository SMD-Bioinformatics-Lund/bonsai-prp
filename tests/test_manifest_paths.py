"""Tests for how manifest paths reach the upload."""

import os
from pathlib import Path

import pytest

from prp.bonsai.steps import _format_suffix
from prp.io.manifest import read_manifest
from prp.pipeline.loader import to_internal_artifacts


@pytest.mark.parametrize(
    ("uri", "expected"),
    [("tbdb.bed.gz", "bed"), ("calls.vcf.gz", "vcf"), ("sample.bam", "bam"), ("noext", "")],
)
def test_format_suffix_looks_past_gz(uri, expected):
    assert _format_suffix(uri) == expected


def _write_manifest(directory: Path, index_artifacts: str) -> Path:
    (directory / "run_info.json").write_text("{}")
    (directory / "sig.sourmash").write_text("x")
    (directory / "access").mkdir()
    (directory / "access" / "sample.bam").write_text("x")
    manifest = directory / "manifest.yml"
    manifest.write_text(
        f"""
sample_id: sample1
sample_name: sample1
lims_id: l1
nextflow_run_info: ./run_info.json
igv_annotations:
  - name: Read coverage
    type: alignment
    uri: ./access/sample.bam
    index_uri: /abs/sample.bam.bai
analysis_result: []
{index_artifacts}
"""
    )
    return manifest


def test_igv_paths_are_relative_to_manifest(tmp_path):
    manifest = read_manifest(_write_manifest(tmp_path, ""))
    track = manifest.igv_annotations[0]
    assert track.uri == os.path.join(str(tmp_path), "access", "sample.bam")
    assert track.index_uri == "/abs/sample.bam.bai"


def test_igv_paths_keep_symlinked_directories(tmp_path):
    real = tmp_path / "backup"
    real.mkdir()
    link = tmp_path / "link"
    link.symlink_to(real, target_is_directory=True)
    manifest_path = _write_manifest(real, "")
    manifest = read_manifest(link / manifest_path.name)
    assert manifest.igv_annotations[0].uri == os.path.join(str(link), "access", "sample.bam")


def test_index_artifacts_without_ska_index(tmp_path):
    manifest = read_manifest(_write_manifest(tmp_path, "index_artifacts:\n  sourmash_signature: ./sig.sourmash"))
    artifacts = to_internal_artifacts(manifest.index_artifacts)
    assert artifacts.ska_index is None
    assert Path(artifacts.sourmash_signature).name == "sig.sourmash"


@pytest.mark.parametrize(
    ("fields", "expected"),
    [
        ("reference_genome_accession: GCF_000012045.1", "GCF_000012045.1"),
        ("reference_genome_id: ref-uuid-1", "ref-uuid-1"),
        ("reference_genome_accession: GCF_000012045.1\nreference_genome_id: ref-uuid-1", "GCF_000012045.1"),
        ("", None),
    ],
)
def test_reference_genome_prefers_the_accession(tmp_path, fields, expected):
    manifest_path = _write_manifest(tmp_path, fields)
    assert read_manifest(manifest_path).reference_genome() == expected
