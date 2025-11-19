"""Species related data models."""

from enum import StrEnum
from typing import Literal
from pydantic import Field

from .base import MethodIndexBase, RWModel


class TaxLevel(StrEnum):
    """Braken phylogenetic level."""

    P = "phylum"
    C = "class"
    O = "order"
    F = "family"
    G = "genus"
    S = "species"


class SppPredictionSoftware(StrEnum):
    """Container for prediciton software names."""

    MYKROBE = "mykrobe"
    TBPROFILER = "tbprofiler"
    BRACKEN = "bracken"
    KLEBORATE = "kleborate"


class SpeciesPrediction(RWModel):
    """Species prediction results."""

    scientific_name: str = Field(..., alias="scientificName")
    taxonomy_id: int | None = Field(..., alias="taxId")


class BrackenSpeciesPrediction(SpeciesPrediction):
    """Species prediction results."""

    taxonomy_lvl: TaxLevel = Field(..., alias="taxLevel")
    kraken_assigned_reads: int = Field(..., alias="krakenAssignedReads")
    added_reads: int = Field(..., alias="addedReads")
    fraction_total_reads: float = Field(..., alias="fractionTotalReads")

class BrackenSppIndex(MethodIndexBase[BrackenSpeciesPrediction]):
    software: Literal[SppPredictionSoftware.BRACKEN] = SppPredictionSoftware.BRACKEN
