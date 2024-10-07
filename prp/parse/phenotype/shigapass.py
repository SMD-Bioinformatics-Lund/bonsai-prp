"""Functions for parsing shigapass result."""

import logging
import re

import pandas as pd

from ...models.phenotype import (ShigatypeGene)

LOG = logging.getLogger(__name__)


def _extract_percentage(rfb_hits: str) -> float:
    pattern = r"([0-9\.]+)%"
    match = re.search(pattern, rfb_hits)
    if match:
        percentile_value = float(match.group(1))
    else:
        percentile_value = 0.0
    return percentile_value


def parse_shiga_gene(predictions: pd.DataFrame, row: int) -> ShigatypeGene:
    return ShigatypeGene(
        rfb=predictions.loc[row, "rfb"],
        rfb_hits=_extract_percentage(str(predictions.loc[row, "rfb_hits"])),
        mlst=predictions.loc[row, "mlst"],
        flic=predictions.loc[row, "flic"],
        crispr=predictions.loc[row, "crispr"],
        ipah=predictions.loc[row, "ipah"],
        predicted_serotype=predictions.loc[row, "predicted_serotype"],
        predicted_flex_serotype=predictions.loc[row, "predicted_flex_serotype"],
        comments=predictions.loc[row, "comments"],
    )
