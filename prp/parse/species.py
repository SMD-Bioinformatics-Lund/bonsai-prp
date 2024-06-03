"""Parsers for species prediction tools."""

import logging
from typing import Any

import pandas as pd

from prp.models.species import (
    MykrobeSpeciesPrediction,
    SppMethodIndex,
    SppPredictionSoftware,
)

LOG = logging.getLogger(__name__)


def parse_kraken_result(file: str, cutoff: float = 0.0001) -> SppMethodIndex:
    """parse_species_pred""Parse species prediciton result"""
    tax_lvl_dict = {
        "P": "phylum",
        "C": "class",
        "O": "order",
        "F": "family",
        "G": "genus",
        "S": "species",
    }
    columns = {"name": "scientific_name"}
    species_pred: pd.DataFrame = (
        pd.read_csv(file, sep="\t")
        .sort_values("fraction_total_reads", ascending=False)
        .rename(columns=columns)
        .replace({"taxonomy_lvl": tax_lvl_dict})
        .loc[lambda df: df["fraction_total_reads"] >= cutoff]
    )
    # cast as method index
    return SppMethodIndex(
        software=SppPredictionSoftware.BRACKEN,
        result=species_pred.to_dict(orient="records"),
    )


def get_mykrobe_spp_prediction(prediction: list[dict[str, Any]]) -> SppMethodIndex:
    """Get species prediction result from Mykrobe."""
    LOG.info("Parsing Mykrobe spp result.")
    spp_pred = MykrobeSpeciesPrediction(
        scientific_name=prediction[0]["species"].replace("_", " "),
        taxonomy_id=None,
        phylogenetic_group=prediction[0]["phylo_group"].replace("_", " "),
        phylogenetic_group_coverage=prediction[0]["phylo_group_per_covg"],
        species_coverage=prediction[0]["species_per_covg"],
    )
    return SppMethodIndex(software=SppPredictionSoftware.MYKROBE, result=[spp_pred])
