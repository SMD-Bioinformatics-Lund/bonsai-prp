"""Kleborate specific models."""

from typing import Literal
from pydantic import BaseModel, Field
from .base import RWModel
from .qc import QcSoftware
from .typing import TypingResultMlst


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
    match: Literal['strong', 'weak'] = Field(..., description="Strength of the species call depending on the Mash didstance.")


class KleborateMethodIndex(RWModel):
    """Indexing of Kleborate data."""

    software: Literal[QcSoftware.KLEBORATE]
    version: str
    result: KleborateQcResult | KleboreateSppResult | TypingResultMlst
