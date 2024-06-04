"""Data model definition of input/ output data"""

from typing import Literal, Optional, Union

from pydantic import Field

from .base import RWModel
from .metadata import RunMetadata
from .phenotype import (
    AMRMethodIndex,
    StressMethodIndex,
    VariantBase,
    VirulenceMethodIndex,
)
from .qc import QcMethodIndex
from .species import SppMethodIndex
from .typing import (
    ResultLineageBase,
    ShigaTypingMethodIndex,
    TbProfilerLineage,
    TypingMethod,
    TypingResultCgMlst,
    TypingResultGeneAllele,
    TypingResultMlst,
    TypingSoftware,
)


class MethodIndex(RWModel):
    """Container for key-value lookup of analytical results."""

    type: TypingMethod
    software: TypingSoftware | None
    result: Union[
        TypingResultMlst,
        TypingResultCgMlst,
        TypingResultGeneAllele,
        TbProfilerLineage,
        ResultLineageBase,
    ]


class SampleBase(RWModel):
    """Base datamodel for sample data structure"""

    run_metadata: RunMetadata = Field(..., alias="runMetadata")
    qc: list[QcMethodIndex] = Field(...)
    species_prediction: list[SppMethodIndex] = Field(..., alias="speciesPrediction")


class ReferenceGenome(RWModel):
    """Reference genome."""

    name: str
    accession: str
    fasta: str
    fasta_index: Optional[str] = None
    genes: str


class PipelineResult(SampleBase):
    """Input format of sample object from pipeline."""

    schema_version: Literal[1] = 1
    # optional typing
    typing_result: list[Union[ShigaTypingMethodIndex, MethodIndex]] = Field(
        ..., alias="typingResult"
    )
    # optional phenotype prediction
    element_type_result: list[
        Union[VirulenceMethodIndex, AMRMethodIndex, StressMethodIndex, MethodIndex]
    ] = Field(..., alias="elementTypeResult")
    # optional variant info
    snv_variants: Optional[list[VariantBase]] = None
    sv_variants: Optional[list[VariantBase]] = None
    # optional alignment info
    reference_genome: Optional[ReferenceGenome] = None
    read_mapping: Optional[str] = None
    genome_annotation: Optional[list[dict[str, str]]] = None
