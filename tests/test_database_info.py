"""Tests for database_info in sample manifests."""

import pytest
from pydantic import ValidationError

from prp.models.manifest import DatabaseRecord, SampleManifest
from prp.pipeline.loader import to_internal_run_info

RUN_INFO = {
    "pipeline": "jasen",
    "version": "1.3.0",
    "commit": "abc",
    "release_life_cycle": "production",
    "command": "nextflow run",
    "analysis_profile": ["staphylococcus_aureus"],
    "configuration_files": ["nextflow.config"],
    "workflow_name": "run1",
    "assay": "wgs",
    "date": "2026-01-01T00:00:00",
}


def _manifest(tmp_path, **extra):
    run_info = tmp_path / "analysis_meta.json"
    run_info.write_text("{}")
    return {
        "sample_id": "sample1",
        "sample_name": "sample1",
        "lims_id": "L1",
        "nextflow_run_info": str(run_info),
        **extra,
    }


def test_manifest_parses_database_info(tmp_path):
    manifest = SampleManifest.model_validate(_manifest(tmp_path, database_info=[
        {"software": "resfinder", "database": "pointfinder", "database_version": "4.1.1"},
    ]))
    assert manifest.database_info == [
        DatabaseRecord(software="resfinder", database="pointfinder", database_version="4.1.1")
    ]


def test_manifest_rejects_software_info(tmp_path):
    with pytest.raises(ValidationError, match="replaced by database_info"):
        SampleManifest.model_validate(_manifest(tmp_path, software_info=["x_meta.json"]))


def test_database_info_reaches_pipeline_run():
    run = to_internal_run_info(
        run_info=RUN_INFO,
        analysis_results=[],
        database_info=[
            DatabaseRecord(software="resfinder", database="resfinder", database_version="2.6.0"),
            DatabaseRecord(software="tbprofiler", database="tbdb", database_version="4907915"),
        ],
    )
    assert [(db.software, db.name, db.version) for db in run.pipeline_info.databases] == [
        ("resfinder", "resfinder", "2.6.0"),
        ("tbprofiler", "tbdb", "4907915"),
    ]
