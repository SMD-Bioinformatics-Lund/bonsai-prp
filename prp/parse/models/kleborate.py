"""Kleborate specific models."""

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

from prp.models.base import RWModel
from .enums import VariantSubType
from .typing import LineageMixin, TypingResultMlst


class KleborateQcResult(BaseModel):
    """QC metrics reported by Kleborate."""

    n_contigs: int
    n50: int
    largest_contig: int
    total_length: int
    ambigious_bases: bool
    qc_warnings: None | bool = None


class KleboreateSppResult(RWModel):
    """Species prediction results."""

    scientific_name: str = Field(..., alias="scientificName")
    match: Literal["strong", "weak"] = Field(
        ..., description="Strength of the species call depending on the Mash distance."
    )


class KleborateMlstLikeResults(TypingResultMlst, LineageMixin):
    """Kleborate MLST-like analysis"""


class KleborateEtScore(RWModel):
    """Records and validate score."""

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


class ParsedVariant(BaseModel):
    """Structured output of a Kleborate HGVS-like variant string."""

    ref: str = Field(default="", min_length=0, max_length=10)
    alt: str = Field(default="", min_length=0, max_length=20)
    start: int = Field(..., ge=1)
    end: int | None = Field(default=None, ge=1)
    residue: Literal["nucleotide", "protein"]
    type: VariantSubType

    @field_validator("ref", "alt", mode="before")
    @classmethod
    def strip_whitespace(cls, v: Any):
        return v.strip() if isinstance(v, str) else v
