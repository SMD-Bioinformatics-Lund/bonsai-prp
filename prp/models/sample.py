"""Data model definition of input/ output data"""
from typing import List, Union

from pydantic import Field

from .base import RWModel
from .metadata import RunMetadata
from .phenotype import ElementType, ElementTypeResult, PredictionSoftware
from .qc import QcMethodIndex
from .species import SpeciesPredictionResult
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

    sample_id: str = Field(..., alias="sampleId", min_length=3, max_length=100)
    run_metadata: RunMetadata = Field(..., alias="runMetadata")
    qc: List[QcMethodIndex] = Field(...)
    species_prediction: SpeciesPredictionResult = Field(..., alias="speciesPrediction")


class PipelineResult(SampleBase):
    """Input format of sample object from pipeline."""

    schema_version: int = Field(..., alias="schemaVersion", gt=0)
    # optional typing
    typing_result: List[MethodIndex] = Field(..., alias="typingResult")
    # optional phenotype prediction
    element_type_result: List[MethodIndex] = Field(..., alias="elementTypeResult")
