"""Resolve the group keys used in manifests to Bonsai's generated group ids."""

from bonsai_libs.api_client.bonsai.models import GroupResponse

from prp.exceptions import UploadError


def resolve_group_ids(groups: list[GroupResponse], names: list[str]) -> list[str]:
    """Map each manifest group to a Bonsai group id by its group key.

    Bonsai generates group ids, so a manifest names groups by their key, such as
    `saureus`. A group id is accepted as well, for callers that already have one.
    """
    by_key = {group.group: group.group_id for group in groups if group.group}
    ids = {group.group_id for group in groups}

    resolved: list[str] = []
    unknown: list[str] = []
    for name in names:
        if name in by_key:
            resolved.append(by_key[name])
        elif name in ids:
            resolved.append(name)
        else:
            unknown.append(name)

    if unknown:
        raise UploadError(f"No Bonsai group matches {unknown}; group keys are {sorted(by_key)}")
    return list(dict.fromkeys(resolved))
