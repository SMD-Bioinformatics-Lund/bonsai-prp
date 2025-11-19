"""AmrFinder results"""

from pydantic import Field
from typing import Literal

from .base import MethodIndexBase
from .constants import PredictionSoftware, ElementType
from .phenotype import VariantBase, SequenceStrand, GeneBase, PhenotypeInfo, ElementTypeBase


class AmrFinderGene(GeneBase):
    """Container for Resfinder gene prediction information"""

    contig_id: str
    query_start_pos: int | None = Field(
        default=None, description="Start position on the assembly"
    )
    query_end_pos: int | None = Field(default=None, description="End position on the assembly")
    strand: SequenceStrand | None


class AmrFinderVirulenceGene(AmrFinderGene):
    """Container for a virulence gene for AMRfinder."""


class AmrFinderResistanceGene(AmrFinderGene):
    """AMRfinder resistance gene information."""

    phenotypes: list[PhenotypeInfo] = []


class AmrFinderVariant(VariantBase):
    """Container for AmrFinder variant information."""

    contig_id: str
    query_start_pos: int = Field(..., description="Alignment start in contig")
    query_end_pos: int = Field(..., description="Alignment start in contig")
    ref_gene_length: int | None = Field(
        default=None,
        alias="target_length",
        description="The length of the reference protein or gene.",
    )
    strand: SequenceStrand | None
    coverage: float
    identity: float


class AmrFinderResult(ElementTypeBase):
    genes: list[AmrFinderGene | AmrFinderResistanceGene]
    variants: list[AmrFinderVariant] = []


class AmrFinderIndex(MethodIndexBase[AmrFinderResult]):
    type: Literal[ElementType.AMR, ElementType.STRESS, ElementType.VIR]
    software: Literal[PredictionSoftware.AMRFINDER] = PredictionSoftware.AMRFINDER
