"""Species related data models."""

from enum import StrEnum
from typing import Annotated, Literal

from pydantic import Field

from .base import MethodIndexBase, RWModel
from .kleborate import KleboreateSppResult


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


class MykrobeSpeciesPrediction(SpeciesPrediction):
    """Mykrobe species prediction results."""

    phylogenetic_group: str = Field(
        ..., description="Group with phylogenetic related species."
    )
    phylogenetic_group_coverage: float = Field(
        ..., description="Kmer converage for phylo group."
    )
    species_coverage: float = Field(..., description="Species kmer converage.")


class BrackenSppIndex(MethodIndexBase[BrackenSpeciesPrediction]):
    software = SppPredictionSoftware.BRACKEN


class MykrobeSppIndex(MethodIndexBase[MykrobeSpeciesPrediction]):
    software = SppPredictionSoftware.MYKROBE


class KleborateSppIndex(MethodIndexBase[KleboreateSppResult]):
    software = SppPredictionSoftware.KLEBORATE


SppMethodIndex = Annotated[
    BrackenSppIndex | MykrobeSppIndex | KleborateSppIndex,
    Field(discriminator="software"),
]
