"""Functions to migrate from version 1 to version 2."""

from typing import Any
import logging


from prp.models import PipelineResult

LOG = logging.getLogger(__name__)

type OldResult = dict[str, Any]


def v1_to_v2(old_result: OldResult) -> PipelineResult:
    """Convert result in json format from v1 to v2."""

    return