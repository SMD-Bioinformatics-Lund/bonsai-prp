"""Functions to convert results to a new schema version."""

import logging
from copy import copy
from typing import Any, Callable

from prp.models import PipelineResult

LOG = logging.getLogger(__name__)

UnformattedResult = dict[str, Any]


def migrate_result(old_result: UnformattedResult) -> PipelineResult:
    """Migrate old JASEN result to the current schema."""
    ALL_FUNCS: dict[int, Callable[..., UnformattedResult]] = {2: v1_to_v2}

    # verify input
    input_schema_version = old_result["schema_version"]
    LOG.info("Migrating result from version %d", input_schema_version)
    if input_schema_version not in ALL_FUNCS:
        all_versions = ", ".join([str(ver) for ver in ALL_FUNCS])
        raise ValueError(
            f"Unknown result version, found {input_schema_version} expected any of {all_versions}"
        )

    # migrate
    temp_result = copy(old_result)
    for to_version, func in ALL_FUNCS.items():
        temp_result = func(temp_result)

    return PipelineResult.model_validate(temp_result)


def v1_to_v2(result: UnformattedResult) -> UnformattedResult:
    """Convert result in json format from v1 to v2."""
    input_schema_version = result["schema_version"]
    if input_schema_version != 1:
        raise ValueError(f"Invalid schema version '{input_schema_version}' expected 1")

    LOG.info("Migrating from v%d to v%d", input_schema_version, 2)
    upd_result = copy(result)
    # split analysis profile into a list and strip white space
    upd_profile: list[str] = [
        prof.strip() for prof in result["pipeline"]["analysis_profile"].split(",")
    ]
    upd_result["pipeline"]["analysis_profile"] = upd_profile
    # update schema version
    upd_result["schema_version"] = 2
    return upd_result
