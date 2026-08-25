"""Tests for prp.pipeline.loader: normalizing manifest/run data into internal models."""

import json
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

import pytest

from prp.models.manifest import (
    URI,
    AnalysisResult,
    IgvAnnotation,
    IndexArtifacts,
    SampleManifest,
)
from prp.models.metadata import StrMetadataEntry, TableMetadataEntry
from prp.pipeline.loader import (
    parse_base_results_from_manifest,
    parse_date_from_run_id,
    parse_manifest_for_upload,
    to_generic_metadata_record,
    to_internal_artifacts,
    to_internal_run_info,
    to_internal_sequencing_info,
    to_table_record,
)
from prp.pipeline.types import FullAnalysisResult, MinimalAnalysisRecord


def _fake_analysis_result(software: str) -> SimpleNamespace:
    return SimpleNamespace(
        software=software,
        software_version="1.0.0",
        uri=URI(scheme="file", path=f"/data/{software}.tsv"),
    )


def test_to_internal_run_info_maps_fields():
    run_info = {
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
    }
    analysis_results = [_fake_analysis_result("mlst")]

    result = to_internal_run_info(run_info=run_info, analysis_results=analysis_results)

    assert result.pipeline_run_id == "run-42"
    assert result.assay == "saureus"
    assert result.pipeline_info.definition.name == "jasen"
    assert result.pipeline_info.definition.version == "2.1.0"
    assert result.pipeline_info.definition.commit == "abc123"
    assert result.pipeline_info.definition.release_life_cycle == "production"
    assert result.pipeline_info.run_config.command == "nextflow run jasen"
    assert len(result.pipeline_info.artifacts) == 1
    assert result.pipeline_info.artifacts[0].software_name == "mlst"


def test_to_internal_run_info_applies_defaults():
    """No version (falls back to commit), commit="null" (-> None), no release_life_cycle (-> unknown)."""
    run_info = {
        "pipeline": "jasen",
        "commit": "null",
        "workflow_name": "run-1",
        "assay": "generic",
        "date": "2026-01-01T00:00:00",
        "command": "cmd",
        "analysis_profile": [],
    }

    result = to_internal_run_info(run_info=run_info, analysis_results=[])

    assert result.pipeline_info.definition.version == "null"
    assert result.pipeline_info.definition.commit is None
    assert result.pipeline_info.definition.release_life_cycle == "unknown"


@pytest.mark.parametrize(
    "run_id,expected",
    [
        ("240112_A00001", datetime(2024, 1, 12)),
        ("240199_A00001", None),  # invalid day, unparsable
        ("noUnderscoreHere", None),  # no "_" separator at all
    ],
)
def test_parse_date_from_run_id(run_id, expected):
    assert parse_date_from_run_id(run_id) == expected


def test_to_internal_sequencing_info_maps_fields():
    run_info = {
        "sequencing_run": "240112_A00001",
        "sequencing_platform": "illumina",
        "sequencing_type": "paired-end",
    }

    info = to_internal_sequencing_info(run_info)

    assert info.sequencing_run_id == "240112_A00001"
    assert info.platform == "illumina"
    assert info.sequencing_method == "paired-end"
    assert info.sequenced_at == datetime(2024, 1, 12)


def test_to_internal_sequencing_info_defaults_run_id_to_unknown():
    # An empty (but present) sequencing_run falls back to "unknown"; a
    # genuinely missing key would crash parse_date_from_run_id on `None`.
    info = to_internal_sequencing_info(
        {"sequencing_run": "", "sequencing_platform": "illumina"}
    )

    assert info.sequencing_run_id == "unknown"
    assert info.sequenced_at is None


def test_to_generic_metadata_record_maps_fields():
    entry = StrMetadataEntry(
        fieldname="host", value="human", category="clinical", type="string"
    )

    record = to_generic_metadata_record(entry)

    assert record.fieldname == "host"
    assert record.value == "human"
    assert record.category == "clinical"
    assert record.data_type == "string"


def test_to_table_record_reads_delimited_file(tmp_path: Path):
    csv_path = tmp_path / "sccmec.csv"
    csv_path.write_text("gene,type\nmecA,SCCmec IV\n", encoding="utf-8")
    entry = TableMetadataEntry(
        fieldname="sccmec", value=str(csv_path), category="typing", type="table"
    )

    record = to_table_record(entry)

    assert record.fieldname == "sccmec"
    assert record.columns == ["gene", "type"]
    assert record.cells == [["mecA", "SCCmec IV"]]
    assert record.category == "typing"


def test_to_table_record_rejects_non_table_entry():
    entry = StrMetadataEntry(fieldname="x", value="y", type="string")

    with pytest.raises(ValueError, match="expects TableMetadataEntry"):
        to_table_record(entry)


def test_to_table_record_rejects_unknown_extension(tmp_path: Path):
    bad_path = tmp_path / "data.txt"
    bad_path.write_text("a,b\n1,2\n", encoding="utf-8")
    entry = TableMetadataEntry(fieldname="x", value=str(bad_path), type="table")

    with pytest.raises(ValueError, match="Dont know how to parse"):
        to_table_record(entry)


def test_to_internal_artifacts_resolves_existing_and_missing_files(tmp_path: Path):
    existing = tmp_path / "sig.sourmash"
    existing.write_text("x", encoding="utf-8")
    missing = tmp_path / "missing.ska"

    artifacts = IndexArtifacts(ska_index=str(missing), sourmash_signature=str(existing))

    internal = to_internal_artifacts(artifacts)

    assert internal.ska_index is None
    assert internal.sourmash_signature == existing


def _write_run_info(tmp_path: Path) -> Path:
    run_info_path = tmp_path / "run_info.json"
    run_info_path.write_text(
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
                "sequencing_type": "paired-end",
            }
        ),
        encoding="utf-8",
    )
    return run_info_path


def _build_manifest(tmp_path: Path) -> SampleManifest:
    metadata_csv = tmp_path / "sccmec.csv"
    metadata_csv.write_text("gene,type\nmecA,SCCmec IV\n", encoding="utf-8")

    return SampleManifest(
        sample_id="sample-1",
        sample_name="Sample 1",
        lims_id="lims-1",
        groups=["saureus"],
        metadata=[
            StrMetadataEntry(fieldname="host", value="human", type="string"),
            TableMetadataEntry(
                fieldname="sccmec", value=str(metadata_csv), type="table"
            ),
        ],
        reference_genome_id="ref-1",
        igv_annotations=[IgvAnnotation(type="annotation", uri="/data/track.bed")],
        nextflow_run_info=_write_run_info(tmp_path),
        analysis_result=[
            AnalysisResult(
                software="mlst", software_version="2.0", uri="/data/mlst.tsv"
            )
        ],
        index_artifacts=None,
    )


def test_parse_base_results_from_manifest_builds_full_result(tmp_path: Path):
    manifest = _build_manifest(tmp_path)

    result = parse_base_results_from_manifest(manifest)

    assert result.sample_id == "sample-1"
    assert result.reference_genome_id == "ref-1"
    assert result.pipeline.pipeline_run_id == "run-42"
    assert result.sequencing.sequencing_run_id == "240112_A00001"
    assert len(result.metadata) == 2
    assert result.annotation_tracks[0].name == "track.bed"
    assert result.index_artifacts is None


def test_parse_manifest_for_upload_skips_parsing_analysis_results(tmp_path: Path):
    manifest = _build_manifest(tmp_path)

    result = parse_manifest_for_upload(manifest)

    assert len(result.analysis_results) == 1
    record = result.analysis_results[0]
    assert isinstance(record, MinimalAnalysisRecord)
    assert not isinstance(record, FullAnalysisResult)
    assert record.software == "mlst"
    assert record.software_version == "2.0"
