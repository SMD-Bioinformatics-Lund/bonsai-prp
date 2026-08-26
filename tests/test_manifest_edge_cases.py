"""Edge-case tests for prp.pipeline.loader and prp.io.utils that aren't practical
to reach through a single CLI invocation (defaulting logic and error branches).
The happy paths are covered end-to-end by tests/test_cli.py."""

from datetime import datetime
from types import SimpleNamespace

import pytest

from prp.io.utils import convert_rel_to_abs_path
from prp.models.manifest import IndexArtifacts
from prp.models.metadata import StrMetadataEntry, TableMetadataEntry
from prp.pipeline.loader import (
    parse_date_from_run_id,
    to_internal_artifacts,
    to_internal_run_info,
    to_internal_sequencing_info,
    to_table_record,
)


def test_to_internal_run_info_applies_defaults():
    """No version (falls back to commit), commit="null" (-> None), no
    release_life_cycle (-> unknown)."""
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


def test_to_internal_sequencing_info_defaults_run_id_to_unknown():
    # An empty (but present) sequencing_run falls back to "unknown"; a
    # genuinely missing key would crash parse_date_from_run_id on `None`.
    info = to_internal_sequencing_info(
        {"sequencing_run": "", "sequencing_platform": "illumina"}
    )

    assert info.sequencing_run_id == "unknown"
    assert info.sequenced_at is None


def test_to_table_record_rejects_non_table_entry():
    entry = StrMetadataEntry(fieldname="x", value="y", type="string")

    with pytest.raises(ValueError, match="expects TableMetadataEntry"):
        to_table_record(entry)


def test_to_table_record_rejects_unknown_extension(tmp_path):
    bad_path = tmp_path / "data.txt"
    bad_path.write_text("a,b\n1,2\n", encoding="utf-8")
    entry = TableMetadataEntry(fieldname="x", value=str(bad_path), type="table")

    with pytest.raises(ValueError, match="Dont know how to parse"):
        to_table_record(entry)


def test_to_internal_artifacts_resolves_existing_and_missing_files(tmp_path):
    existing = tmp_path / "sig.sourmash"
    existing.write_text("x", encoding="utf-8")
    missing = tmp_path / "missing.ska"

    artifacts = IndexArtifacts(ska_index=str(missing), sourmash_signature=str(existing))

    internal = to_internal_artifacts(artifacts)

    assert internal.ska_index is None
    assert internal.sourmash_signature == existing


def test_convert_rel_to_abs_path_resolves_relative_against_context(tmp_path):
    fpath = tmp_path / "sub" / "file.txt"
    fpath.parent.mkdir()
    fpath.write_text("x", encoding="utf-8")
    info = SimpleNamespace(context=tmp_path / "manifest.yaml")

    result = convert_rel_to_abs_path("sub/file.txt", info)

    assert result == fpath


def test_convert_rel_to_abs_path_raises_without_context_for_relative_path():
    with pytest.raises(ValueError, match="No context defined"):
        convert_rel_to_abs_path("relative/file.txt", SimpleNamespace(context=None))


def test_convert_rel_to_abs_path_raises_if_file_missing(tmp_path):
    missing = tmp_path / "does-not-exist.txt"

    with pytest.raises(AssertionError, match="Invalid path"):
        convert_rel_to_abs_path(str(missing), SimpleNamespace(context=None))
