"""Types for generating pipeline results."""

from typing import Any, Literal

from pydantic import Field

from prp.parse.models.base import VariantBase
from prp.models.base import RWModel
from prp.models.metadata import PipelineRun, SequencingInfo

SCHEMA_VERSION: int = 2


class MethodIndex(RWModel):
    """Container for key-value lookup of analytical results."""

    type: str
    software: str
    result: Any


class SampleBase(RWModel):
    """Base datamodel for sample data structure"""

    sample_id: str = Field(..., min_length=3, max_length=100)
    sample_name: str
    lims_id: str

    # metadata
    sequencing: SequencingInfo
    pipeline: PipelineRun

    # quality
    qc: list[Any] = Field(..., default_factory=list)

    # species identification
    species_prediction: list[Any] = Field(..., default_factory=list)


class ReferenceGenome(RWModel):
    """Reference genome."""

    name: str
    accession: str
    fasta: str
    fasta_index: str
    genes: str


class IgvAnnotationTrack(RWModel):
    """IGV annotation track data."""

    name: str  # track name to display
    file: str  # path to the annotation file


class PipelineResult(SampleBase):
    """Input format of sample object from pipeline."""

    schema_version: Literal[2] = SCHEMA_VERSION
    # optional typing
    typing_result: list[MethodIndex] = Field(..., default_factory=list)
    # optional phenotype prediction
    element_type_result: list[MethodIndex] = Field(..., default_factory=list)
    # optional variant info
    snv_variants: list[VariantBase] | None = None
    sv_variants: list[VariantBase] | None = None
    indel_variants: list[VariantBase] | None = None
    # optional alignment info
    reference_genome: ReferenceGenome | None = None
    read_mapping: str | None = None
    genome_annotation: list[IgvAnnotationTrack] | None = None


class QcMethodIndex(RWModel):
    """QC results container.

    Based on Mongo db Attribute pattern.
    Reference: https://www.mongodb.com/developer/products/mongodb/attribute-pattern/
    """

    software: str
    version: str | None = None
    result: Any


class CdmQcMethodIndex(QcMethodIndex):
    """Qc results container for CDM"""

    id: str