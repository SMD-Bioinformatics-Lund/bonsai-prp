"""Data model definition of input/ output data"""
from typing import Dict, List, Optional, Union

from pydantic import Field

from .base import RWModel
from .metadata import RunMetadata
from .phenotype import ElementType, ElementTypeResult, PredictionSoftware, VariantBase
from .qc import QcMethodIndex
from .species import SppMethodIndex
from .typing import (
    TypingMethod,
    TypingResultCgMlst,
    TypingResultGeneAllele,
    TypingResultLineage,
    TypingResultMlst,
    TypingSoftware,
)


class MethodIndex(RWModel):
    """Container for key-value lookup of analytical results."""

    type: Union[ElementType, TypingMethod]
    software: PredictionSoftware | TypingSoftware | None
    result: Union[
        ElementTypeResult,
        TypingResultMlst,
        TypingResultCgMlst,
        TypingResultLineage,
        TypingResultGeneAllele,
    ]


class SampleBase(RWModel):
    """Base datamodel for sample data structure"""

    run_metadata: RunMetadata = Field(..., alias="runMetadata")
    qc: List[QcMethodIndex] = Field(...)
    species_prediction: List[SppMethodIndex] = Field(..., alias="speciesPrediction")


class ReferenceGenome(RWModel):
    """Reference genome."""

    name: str
    accession: str
    fasta: str
    fasta_index: Optional[str] = None
    genes: str


class PipelineResult(SampleBase):
    """Input format of sample object from pipeline."""

    schema_version: int = Field(..., alias="schemaVersion", gt=0)
    # optional typing
    typing_result: List[MethodIndex] = Field(..., alias="typingResult")
    # optional phenotype prediction
    element_type_result: List[MethodIndex] = Field(..., alias="elementTypeResult")
    # optional variant info
    snv_variants: Optional[List[VariantBase]] = None
    sv_variants: Optional[List[VariantBase]] = None
    # optional alignment info
    reference_genome: Optional[ReferenceGenome] = None
    read_mapping: Optional[str] = None
    genome_annotation: Optional[List[Dict[str, str]]] = None
