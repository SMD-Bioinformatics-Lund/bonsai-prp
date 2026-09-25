"""Tests for resolving manifest group keys to Bonsai group ids."""

import pytest
from bonsai_libs.api_client.bonsai.models import GroupResponse

from prp.bonsai.groups import resolve_group_ids
from prp.exceptions import UploadError


def _group(group_id: str, display_name: str, group_key: str | None = None) -> GroupResponse:
    return GroupResponse(
        group_id=group_id, group_key=group_key, display_name=display_name, sample_count=0,
        created_at="2026-01-01T00:00:00", modified_at="2026-01-01T00:00:00",
    )


GROUPS = [
    _group("uuid-sa", "S. aureus", "saureus"),
    _group("uuid-mtb", "M. tuberculosis", "mtuberculosis"),
]


@pytest.mark.parametrize(
    ("name", "expected"),
    [("saureus", "uuid-sa"), ("mtuberculosis", "uuid-mtb"), ("uuid-sa", "uuid-sa")],
)
def test_resolves_by_group_key_or_id(name, expected):
    assert resolve_group_ids(GROUPS, [name]) == [expected]


def test_duplicate_names_resolve_once():
    assert resolve_group_ids(GROUPS, ["saureus", "uuid-sa"]) == ["uuid-sa"]


@pytest.mark.parametrize("name", ["S. aureus", "SAureus", "s aureus"])
def test_display_names_do_not_match(name):
    """Only the group key identifies a group; a display name is free text."""
    with pytest.raises(UploadError, match="No Bonsai group matches"):
        resolve_group_ids(GROUPS, [name])


def test_group_without_a_key_cannot_be_matched():
    with pytest.raises(UploadError, match="No Bonsai group matches"):
        resolve_group_ids([_group("uuid-old", "Legacy group")], ["legacy-group"])


def test_unknown_group_lists_the_known_keys():
    with pytest.raises(UploadError, match=r"group keys are \['mtuberculosis', 'saureus'\]"):
        resolve_group_ids(GROUPS, ["klebsiella"])
