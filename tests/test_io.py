"""Tests for prp.io.utils."""

from types import SimpleNamespace

import pytest

from prp.io.utils import convert_rel_to_abs_path


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
