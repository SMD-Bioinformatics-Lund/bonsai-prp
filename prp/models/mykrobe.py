"""Mykrobe specific data models."""

from typing import Literal
from pydantic import Field

from .base import MethodIndexBase
from .species import SppPredictionSoftware, SpeciesPrediction


class MykrobeSpeciesPrediction(SpeciesPrediction):
    """Mykrobe species prediction results."""

    phylogenetic_group: str = Field(
        ..., description="Group with phylogenetic related species."
    )
    phylogenetic_group_coverage: float = Field(
        ..., description="Kmer converage for phylo group."
    )
    species_coverage: float = Field(..., description="Species kmer converage.")


class MykrobeSppIndex(MethodIndexBase[MykrobeSpeciesPrediction]):
    software: Literal[SppPredictionSoftware.MYKROBE] = SppPredictionSoftware.MYKROBE
