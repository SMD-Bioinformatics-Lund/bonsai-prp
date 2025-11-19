"""Models specific to VirulenceFinder."""

from typing import Literal, Any

from .base import MethodIndexBase, RWModel
from .constants import ElementType, PredictionSoftware
from .phenotype import VirulenceGene


class VirulenceFinderResult(RWModel):
    genes: list[VirulenceGene] = []
    variants: list[Any] = []


class VirulenceFinderIndex(MethodIndexBase[VirulenceFinderResult]):
    type: Literal[ElementType.VIR] = ElementType.VIR
    software: Literal[PredictionSoftware.VIRFINDER] = PredictionSoftware.VIRFINDER