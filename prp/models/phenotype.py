"""Datamodels used for prediction results."""

from enum import StrEnum 
from typing import Union

from pydantic import BaseModel, Field, model_validator
from typing_extensions import Self

from .base import RWModel
from .constants import ElementType


class SequenceStrand(StrEnum):
    """Definition of DNA strand."""

    FORWARD = "+"
    REVERSE = "-"


class VariantType(StrEnum):
    """Types of variants."""

    SNV = "SNV"
    MNV = "MNV"
    SV = "SV"
    INDEL = "INDEL"
    STR = "STR"


class VariantSubType(StrEnum):
    """Variant subtypes."""

    INSERTION = "INS"
    DELETION = "DEL"
    SUBSTITUTION = "SUB"
    TRANSISTION = "TS"
    TRANSVERTION = "TV"
    INVERSION = "INV"
    DUPLICATION = "DUP"
    TRANSLOCATION = "BND"


class ElementStressSubtype(StrEnum):
    """Categories of resistance and virulence genes."""

    ACID = "ACID"
    BIOCIDE = "BIOCIDE"
    METAL = "METAL"
    HEAT = "HEAT"


class ElementAmrSubtype(StrEnum):
    """Categories of resistance genes."""

    AMR = "AMR"
    POINT = "POINT"


class ElementVirulenceSubtype(StrEnum):
    """Categories of resistance and virulence genes."""

    VIR = "VIRULENCE"
    ANTIGEN = "ANTIGEN"
    TOXIN = "TOXIN"


class AnnotationType(StrEnum):
    """Valid annotation types."""

    TOOL = "tool"
    USER = "user"


class ElementSerotypeSubtype(StrEnum):
    """Categories of serotype genes."""

    ANTIGEN = "ANTIGEN"


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
    reference: list[str] = Field([], description="References supporting trait")
    note: str | None = Field(None, description="Note, can be used for confidence score")
    source: str | None = Field(None, description="Source of variant")


class DatabaseReference(RWModel):
    """Reference to a database."""

    ref_database: str | None = None
    ref_id: str | None = None


class GeneBase(RWModel):
    """Container for gene information"""

    # basic info
    gene_symbol: str | None = None
    accession: str | None = None
    sequence_name: str | None = Field(
        default=None, description="Reference sequence name"
    )
    element_type: ElementType = Field(
        description="The predominant function of the gene."
    )
    element_subtype: Union[
        ElementStressSubtype,
        ElementAmrSubtype,
        ElementVirulenceSubtype,
        ElementSerotypeSubtype,
    ] = Field(description="Further functional categorization of the genes.")
    # position
    ref_start_pos: int | None = Field(
        None, description="Alignment start in reference"
    )
    ref_end_pos: int | None = Field(None, description="Alignment end in reference")
    ref_gene_length: int | None = Field(
        default=None,
        alias="target_length",
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


class ResistanceGene(GeneBase):
    """Container for resistance gene information"""

    phenotypes: list[PhenotypeInfo] = []


class SerotypeGene(GeneBase):
    """Container for serotype gene information"""


class VirulenceGene(GeneBase, DatabaseReference):
    """Container for virulence gene information"""

    depth: float | None = Field(
        None, description="Amount of sequence data supporting the gene."
    )


class VariantBase(RWModel):
    """Container for mutation information"""

    # classification
    id: int
    variant_type: VariantType
    variant_subtype: VariantSubType
    phenotypes: list[PhenotypeInfo] = []

    # variant location
    reference_sequence: str | None = Field(
        ...,
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


class MykrobeVariant(VariantBase):
    """Container for Mykrobe variant information"""


class ElementTypeBase(BaseModel):
    """Base element type model used exmple to store AMR and virulence prediction."""
    phenotypes: dict[str, list[str]] = {}
