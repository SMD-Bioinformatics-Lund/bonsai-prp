"""Base data models."""

from typing import Any, Self
from prp.models.enums import AnalysisType
from pydantic import BaseModel, Field, model_validator

from prp.models.base import RWModel
from .enums import AnnotationType, ElementAmrSubtype, ElementSerotypeSubtype, ElementStressSubtype, ElementType, ElementVirulenceSubtype, ResultStatus, SoupType, VariantSubType, VariantType

class ResultEnvelope(BaseModel):
    """Describe if a analysis result was successfully generated.

    status describe how a result was generated.
    
    PARSED - Assay exists and was parsed
    SKIPPED - Assay exists but user didnt request it
    EMPTY - Assay exists but contains no findings
    ABSENT - Assay doesnt exist in the input
    """

    status: ResultStatus
    value: Any | None = None
    reason: str | None = None
    meta: dict[str, Any] = Field(default_factory=dict)


class ParserOutput(BaseModel):
    """Common output data structure for all parsers."""

    software: str
    software_version: str | None = None
    parser_name: str
    parser_version: int
    schema_version: int = 1

    results: dict[AnalysisType, ResultEnvelope]


class PhenotypeInfo(RWModel):
    """Phenotype information."""

    name: str
    group: str | None = Field(None, description="Name of the group a trait belongs to.")
    type: ElementType = Field(
        ..., description="Trait category, for example AMR, STRESS etc."
    )
    # annotation of the expected resistance level
    resistance_level: str | None = None
    # how was the annotation made
    annotation_type: AnnotationType = Field(..., description="Annotation type")
    annotation_author: str | None = Field(None, description="Annotation author")
    # what information substansiate the annotation
    reference: list[str] = Field(default_factory=list, description="References supporting trait")
    note: str | None = Field(None, description="Note, can be used for confidence score")
    source: str | None = Field(None, description="Source of variant")


class DatabaseReferenceMixin(RWModel):
    """Reference to a database."""

    ref_database: str | None = None
    ref_id: str | None = None


class GeneBase(RWModel):
    """Container for gene information"""

    # basic info
    gene_symbol: str | None = None
    accession: str | None = None
    sequence_name: str | None = Field(
        None, description="Reference sequence name"
    )
    element_type: ElementType = Field(
        description="The predominant function of the gene."
    )
    element_subtype: (
        ElementStressSubtype
        | ElementAmrSubtype
        | ElementVirulenceSubtype
        | ElementSerotypeSubtype
    ) = Field(description="Further functional categorization of the genes.")
    # position
    ref_start_pos: int | None = Field(
        None, description="Alignment start in reference"
    )
    ref_end_pos: int | None = Field(None, description="Alignment end in reference")
    ref_gene_length: int | None = Field(
        None,
        description="The length of the reference protein or gene.",
    )

    # prediction
    method: str | None = Field(None, description="Method used to predict gene")
    identity: float | None = Field(
        None, description="Identity to reference sequence"
    )
    coverage: float | None = Field(
        None, description="Ratio reference sequence covered"
    )
    depth: float | None = Field(
        None, description="Amount of sequence data supporting the gene."
    )

class PhenotypeModelMixin(BaseModel):
    """Mix in phenotype field into data model."""

    phenotypes: list[PhenotypeInfo] = Field(default_factory=list)


class VariantBase(RWModel):
    """Container for mutation information"""

    # classification
    id: int
    variant_type: VariantType
    variant_subtype: VariantSubType
    phenotypes: list[PhenotypeInfo] = Field(default_factory=list)

    # variant location
    reference_sequence: str | None = Field(
        None,
        description="Reference sequence such as chromosome, gene or contig id.",
        alias="gene_symbol",
    )
    accession: str | None = None
    start: int
    end: int
    ref_nt: str | None = None
    alt_nt: str | None = None
    ref_aa: str | None = None
    alt_aa: str | None = None

    # prediction info
    depth: float | None = Field(None, description="Total depth, ref + alt.")
    frequency: float | None = Field(None, description="Alt allele frequency.")
    confidence: float | None = Field(None, description="Genotype confidence.")
    method: str | None = Field(
        ..., description="Prediction method used to call variant"
    )
    passed_qc: bool | None = Field(
        ..., description="Describe if variant has passed the tool qc check"
    )

    @model_validator(mode="after")
    def check_assigned_ref_alt(self) -> Self:
        """Check that either ref/alt nt or aa was assigned."""
        unassigned_nt = self.ref_nt is None and self.alt_nt is None
        unassigned_aa = self.ref_aa is None and self.alt_aa is None
        if unassigned_nt and unassigned_aa:
            raise ValueError("Either ref and alt NT or AA must be assigned.")
        return self


class ElementTypeResult(BaseModel):
    """Phenotype result data model.

    A phenotype result is a generic data structure that stores predicted genes,
    mutations and phenotyp changes.
    """

    phenotypes: dict[str, list[str]] = Field(default_factory=dict)
    genes: list[Any] = Field(default_factory=list)
    variants: list[Any] = Field(default_factory=list)


class BaseSpeciesPrediction(RWModel):
    """Species prediction results."""

    scientific_name: str
    taxonomy_id: int | None = None


class SoupVersion(BaseModel):
    """Version of Software of Unknown Provenance."""

    name: str
    version: str
    type: SoupType