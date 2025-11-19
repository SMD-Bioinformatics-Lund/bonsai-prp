"""TbProfiler specific data models."""


from typing import Literal
from pydantic import Field

from .base import MethodIndexBase
from .constants import PredictionSoftware, ElementType
from .typing import LineageInformation, ResultLineageBase, TypingMethod, TypingSoftware
from .phenotype import ElementTypeBase, ResistanceGene, VariantBase


class TbProfilerLineage(ResultLineageBase):
    """Base class for storing MLST-like typing results"""

    lineages: list[LineageInformation]


class TbProfilerVariant(VariantBase):
    """Container for TbProfiler variant information"""

    variant_effect: str | None = None
    hgvs_nt_change: str | None = Field(None, description="DNA change in HGVS format")
    hgvs_aa_change: str | None = Field(None, description="Protein change in HGVS format")


class TbProfilerEtResult(ElementTypeBase):
    genes: list[ResistanceGene] = []
    variants: list[TbProfilerVariant] = []


class TbProfilerEtIndex(MethodIndexBase[TbProfilerEtResult]):
    type: Literal[ElementType.AMR, ElementType.STRESS, ElementType.VIR]
    software: Literal[PredictionSoftware.TBPROFILER] = PredictionSoftware.TBPROFILER


class TbProfilerLineageTypingIndex(MethodIndexBase[TbProfilerLineage]):
    software: Literal[TypingSoftware.TBPROFILER] = TypingSoftware.TBPROFILER
    type: Literal[TypingMethod.LINEAGE] = TypingMethod.LINEAGE

