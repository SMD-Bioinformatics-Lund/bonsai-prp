"""Resolve the group names used in manifests to Bonsai's generated group ids."""

from bonsai_libs.api_client.bonsai.models import GroupResponse

from prp.exceptions import UploadError


def _normalise(name: str) -> str:
    return "".join(char for char in name.lower() if char.isalnum())


def _match(groups: list[GroupResponse], name: str) -> set[str]:
    by_key = {group.group_id for group in groups if group.group == name}
    if by_key:
        return by_key
    if any(group.group_id == name for group in groups):
        return {name}
    exact = {group.group_id for group in groups if group.display_name == name}
    if exact:
        return exact
    return {group.group_id for group in groups if _normalise(group.display_name) == _normalise(name)}


def resolve_group_ids(groups: list[GroupResponse], names: list[str]) -> list[str]:
    """Map each name to a group by its group key, its id, or its display name.

    A display name matches with case and punctuation ignored, so "saureus" also
    matches a group displayed as "S. aureus" that has no group key.
    """
    resolved: list[str] = []
    unknown: list[str] = []
    for name in names:
        matches = _match(groups, name)
        if len(matches) > 1:
            raise UploadError(f"Group '{name}' matches more than one Bonsai group: {sorted(matches)}")
        if not matches:
            unknown.append(name)
            continue
        resolved.append(matches.pop())
    if unknown:
        available = sorted(group.group or group.display_name for group in groups)
        raise UploadError(f"No Bonsai group matches {unknown}; groups are {available}")
    return list(dict.fromkeys(resolved))
