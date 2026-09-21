"""Tests for resolving manifest group names to Bonsai group ids."""

import pytest
from bonsai_libs.api_client.bonsai.models import GroupResponse

from prp.bonsai.groups import resolve_group_ids
from prp.exceptions import UploadError


def _group(group_id: str, display_name: str, group: str | None = None) -> GroupResponse:
    return GroupResponse(
        group_id=group_id, group=group, display_name=display_name, sample_count=0,
        created_at="2026-01-01T00:00:00", modified_at="2026-01-01T00:00:00",
    )


GROUPS = [
    _group("uuid-sa", "S. aureus", "saureus"),
    _group("uuid-mtb", "M. tuberculosis", "mtuberculosis"),
    _group("uuid-strep", "Streptococcus"),
]


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("uuid-sa", "uuid-sa"),
        ("S. aureus", "uuid-sa"),
        ("saureus", "uuid-sa"),
        ("mtuberculosis", "uuid-mtb"),
        ("streptococcus", "uuid-strep"),
    ],
)
def test_resolves_by_group_key_id_or_display_name(name, expected):
    assert resolve_group_ids(GROUPS, [name]) == [expected]


def test_duplicate_names_resolve_once():
    assert resolve_group_ids(GROUPS, ["saureus", "S. aureus"]) == ["uuid-sa"]


def test_unknown_group_raises():
    with pytest.raises(UploadError, match="klebsiella"):
        resolve_group_ids(GROUPS, ["saureus", "klebsiella"])


def test_ambiguous_display_names_raise():
    groups = [_group("uuid-sa", "S. aureus"), _group("uuid-sa2", "S.aureus")]
    with pytest.raises(UploadError, match="more than one"):
        resolve_group_ids(groups, ["saureus"])


def test_group_key_wins_over_a_display_name_that_also_matches():
    groups = [_group("uuid-sa", "Saureus"), _group("uuid-other", "Another group", "saureus")]
    assert resolve_group_ids(groups, ["saureus"]) == ["uuid-other"]


def test_unknown_group_lists_group_keys_when_present():
    with pytest.raises(UploadError, match="saureus"):
        resolve_group_ids(GROUPS, ["klebsiella"])
