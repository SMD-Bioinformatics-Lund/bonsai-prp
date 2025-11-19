"""Kleborate specific models."""

from typing import Annotated, Any, Literal

from pydantic import BaseModel, Field

from .base import MethodIndexBase, RWModel, VersionMixin
from .constants import PredictionSoftware, ElementType
from .species import SppPredictionSoftware
from .qc import QcSoftware
from .typing import LineageMixin, TypingResultMlst, TypingMethod


class KleborateQcResult(BaseModel):
    """QC metrics reported by Kleborate."""

    n_contigs: int
    n50: int
    largest_contig: int
    total_length: int
    ambigious_bases: bool
    qc_warnings: None | bool


class KleboreateSppResult(RWModel):
    """Species prediction results."""

    scientific_name: str = Field(..., alias="scientificName")
    match: Literal["strong", "weak"] = Field(
        ..., description="Strength of the species call depending on the Mash distance."
    )


class KleborateMlstLikeResults(TypingResultMlst, LineageMixin):
    """Kleborate MLST-like analysis"""


class KleborateVirulenceScore(RWModel):
    """Records and validate virulence score."""

    score: int = Field(..., ge=0, le=5)
    spurious_hits: Any


class KleborateKaptiveLocus(RWModel):
    """Kleboraete curation of Kaptive typing."""

    locus: str
    type: str
    identity: float = Field(..., ge=0, le=1)
    confidence: Literal["typeable", "untypeable"]
    problems: Any
    missing_genes: Any


class KleborateKaptiveTypingResult(RWModel):
    k_type: KleborateKaptiveLocus
    o_type: KleborateKaptiveLocus


class KleborateAmrScoreResult(RWModel):
    """Store Kleborate AMR results."""

    score: int = Field(..., ge=0, le=6)


class KleborateAmrResult(RWModel):
    """Store Kleborate AMR results."""

    score: int = Field(..., ge=0, le=6)


KleborateTypingResult = Annotated[KleborateMlstLikeResults | KleborateKaptiveTypingResult, Field()]


class KleborateTypingIndex(MethodIndexBase[KleborateTypingResult], VersionMixin):
    type: Literal[TypingMethod.ABST, TypingMethod.CBST]
    software: Literal[PredictionSoftware.KLEBORATE] = PredictionSoftware.KLEBORATE


class KleborateVirulenceIndex(MethodIndexBase[KleborateVirulenceScore], VersionMixin):
    type: Literal[ElementType.VIR] = ElementType.VIR
    software: Literal[PredictionSoftware.KLEBORATE] = PredictionSoftware.KLEBORATE


class KleborateAmrScoreIndex(MethodIndexBase[KleborateAmrScoreResult], VersionMixin):
    type: Literal[ElementType.AMR] = ElementType.AMR
    software: Literal[PredictionSoftware.KLEBORATE] = PredictionSoftware.KLEBORATE


class KleborateAmrIndex(MethodIndexBase[KleborateAmrResult], VersionMixin):
    type: Literal[ElementType.AMR] = ElementType.AMR
    software: Literal[PredictionSoftware.KLEBORATE] = PredictionSoftware.KLEBORATE


class KleborateQcIndex(MethodIndexBase[KleborateQcResult], VersionMixin):
    software: Literal[QcSoftware.KLEBORATE] = QcSoftware.KLEBORATE

class KleborateSppIndex(MethodIndexBase[KleboreateSppResult], VersionMixin):
    software: Literal[SppPredictionSoftware.KLEBORATE] = SppPredictionSoftware.KLEBORATE
