"""Resfinder specific data models."""

from typing import Literal
from pydantic import Field

from .base import MethodIndexBase
from .constants import PredictionSoftware, ElementType
from .phenotype import ElementTypeBase, ResistanceGene, VariantBase

class ResfinderGene(ResistanceGene):
    """Container for Resfinder gene prediction information"""

    depth: float | None = Field(
        None, description="Amount of sequence data supporting the gene."
    )


class ResfinderVariant(VariantBase):
    """Container for ResFinder variant information"""


class ResFinderResult(ElementTypeBase):
    genes: list[ResfinderGene]
    variants: list[ResfinderVariant] = []


class ResFinderIndex(MethodIndexBase[ResFinderResult]):
    type: Literal[ElementType.AMR, ElementType.STRESS]
    software: Literal[PredictionSoftware.RESFINDER] = PredictionSoftware.RESFINDER
