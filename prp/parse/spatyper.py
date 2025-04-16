"""Parse spaTyper results."""

import pandas as pd
import logging

from ..models.sample import SpatyperTypingMethodIndex
from ..models.typing import (TypingMethod, TypingResultSpatyper)
from ..models.typing import TypingSoftware as Software

LOG = logging.getLogger(__name__)


def parse_spatyper_results(path:str) -> SpatyperTypingMethodIndex:
    """Read spaTyper output file."""
    LOG.info("Parsing spatyper results")
    result = (
        pd.read_csv(path, delimiter="\t")
        .rename(
            columns={
                "Sequence name": "sequence_name",
                "Repeats": "repeats",
                "Type": "type"
            }
        )
    )
    # extract the values from the first row (index 0)
    first_row = result.iloc[0].str.strip()
    
    # create typing result object
    result_obj = TypingResultSpatyper(
        sequence_name = first_row["sequence_name"],
        repeats = first_row["repeats"],
        type = first_row["type"]
    )
    return SpatyperTypingMethodIndex(
    type=TypingMethod.SPATYPE, software=Software.SPATYPER, result=result_obj
    )

     # How does it look if nothing is found? Account for missing result? See below.

     # Sequence name	Repeats	Type
     # nothing in this row

     # do I have to explicitly say that results can be None? 