"""Kleborate specific models."""

from typing import Any, Literal

from pydantic import BaseModel, Field

from .base import RWModel
from .phenotype import ElementTypeResult
from .typing import LineageMixin, TypingResultMlst


class KleborateQcResult(BaseModel):
    """QC metrics reported by Kleborate."""

    n_contigs: int
    n50: int
    largest_contig: int
    total_length: int
    ambigious_bases: bool
    qc_warnings: None | bool


class KleboreateSppResult(BaseModel):
    """Species prediction results."""

    scientific_name: str = Field(..., alias="scientificName")
    match: Literal["strong", "weak"] = Field(
        ..., description="Strength of the species call depending on the Mash didstance."
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


class KleborateAmrPrediction(RWModel):
    """Store Kleborate AMR results."""

    score: int = Field(..., ge=0, le=6)


class KleborateMethodIndex(RWModel):
    """Indexing of Kleborate data."""

    software: Literal["kleborate"] = "kleborate"
    version: str
    result: KleborateQcResult | KleboreateSppResult | KleborateMlstLikeResults | KleborateKaptiveTypingResult | KleborateVirulenceScore | ElementTypeResult
