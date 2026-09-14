"""Tests for reading database version files listed in a manifest."""
import json

from prp.pipeline.loader import read_database_info


def _write(path, content):
    path.write_text(json.dumps(content) if not isinstance(content, str) else content)
    return str(path)


def test_list_file_yields_every_database(tmp_path):
    path = _write(tmp_path / "resfinder_meta.json", [
        {"name": "resfinder", "version": "2.4.0", "type": "database"},
        {"name": "pointfinder", "version": "4.1.1", "type": "database"},
    ])
    assert [(db.name, db.version) for db in read_database_info([path])] == [
        ("resfinder", "2.4.0"), ("pointfinder", "4.1.1"),
    ]


def test_single_object_file(tmp_path):
    path = _write(tmp_path / "virulencefinder_meta.json",
                  {"name": "virulencefinder", "version": "041b8b3", "type": "database"})
    assert [db.name for db in read_database_info([path])] == ["virulencefinder"]


def test_bad_files_skipped_without_losing_good_ones(tmp_path):
    good = _write(tmp_path / "good.json", {"name": "serotypefinder", "version": "1.0"})
    broken = _write(tmp_path / "broken.json", "{not json")
    malformed = _write(tmp_path / "malformed.json", [{"name": "x"}])
    missing = str(tmp_path / "missing.json")
    names = [db.name for db in read_database_info([broken, malformed, missing, good])]
    assert names == ["serotypefinder"]
