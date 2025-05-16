"""Parse sccmec results."""

import pandas as pd
import logging

from ..models.sample import SccmecTypingMethodIndex
from ..models.typing import (TypingMethod, TypingResultSccmec)
from ..models.typing import TypingSoftware as Software

LOG = logging.getLogger(__name__)


def parse_sccmec_results(path: str) -> SccmecTypingMethodIndex:
    """Read sccmec output file."""
    LOG.info("Parsing sccmec results")

    result_loa = (
        pd.read_csv(path, delimiter="\t")
        .apply(lambda col: col.map(lambda x: '' if pd.isna(x) else x))
        .to_dict(orient="records") 
    )

    result = result_loa[0] if result_loa else {}

    result_obj = TypingResultSccmec(
        type=result.get("type"),
        subtype=result.get("subtype"),
        mecA=result.get("mecA"),
        targets=result.get("targets"),
        regions=result.get("regions"),
        coverage=result.get("coverage"),
        hits=result.get("hits"),
        target_comment=result.get("target_comment"),
        region_comment=result.get("region_comment"),
        comment=result.get("comment")
    )

    return SccmecTypingMethodIndex(
        type=TypingMethod.SCCMECTYPE,
        software=Software.SCCMEC,
        result=result_obj
    )