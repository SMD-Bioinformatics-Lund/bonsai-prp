"""Functions for parsing shigapass result."""
import re
import logging
import pandas as pd
import numpy as np
from typing import Tuple

from ...models.phenotype import (
    ElementType,
    ElementTypeResult,
    Shigatype,
)
from ...models.typing import TypingSoftware as Software
from ...models.typing import TypingResultShiga
from ...models.sample import MethodIndex

LOG = logging.getLogger(__name__)

def parse_shigapass_pred(file: str, element_type: ElementType) -> ElementTypeResult:
    """Parse shigapass prediction results."""
    LOG.info("Parsing shigapass prediction")
    pred_result = []
    with open(file, "rb") as csvfile:
        hits = pd.read_csv(csvfile, delimiter=";")
        hits = hits.rename(
            columns={
                "Name": "sample_name",
                "rfb_hits,(%)": "rfb_hits",
                "MLST": "mlst",
                "fliC": "flic",
                "CRISPR": "crispr",
                "ipaH": "ipah",
                "Predicted_Serotype": "predicted_serotype",
                "Predicted_FlexSerotype": "predicted_flex_serotype",
                "Comments": "comments",
            }
        )
        hits.replace(['ND', 'none', np.nan], [None, None, None], inplace=True)
        for row_idx in range(len(hits)):
            shigatype_results = _parse_shigapass_results(hits, row_idx)
            result = TypingResultShiga(**shigatype_results.model_dump())
            pred_result.append(MethodIndex(type=element_type, result=result, software=Software.SHIGAPASS))
    return pred_result

def _extract_percentage(rfb_hits):
    pattern = r'\((\d+\.\d+)%\)'
    match = re.search(pattern, rfb_hits)
    if match:
        percentile_value = match.group(1)
    else:
        percentile_value = 0.0
    return percentile_value

def _parse_shigapass_results(predictions: dict, row: int) -> Shigatype:
    return Shigatype(
            rfb=predictions.loc[row,"rfb"],
            rfb_hits=_extract_percentage(str(predictions.loc[row,"rfb_hits"])),
            mlst=predictions.loc[row,"mlst"],
            flic=predictions.loc[row,"flic"],
            crispr=predictions.loc[row,"crispr"],
            ipah=predictions.loc[row,"ipah"],
            predicted_serotype=predictions.loc[row,"predicted_serotype"],
            predicted_flex_serotype=predictions.loc[row,"predicted_flex_serotype"],
            comments=predictions.loc[row,"comments"],
        )
    