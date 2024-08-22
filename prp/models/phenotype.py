"""Datamodels used for prediction results."""
from enum import Enum
from typing import Literal, Optional, Union

from pydantic import BaseModel, Field

from .base import RWModel


class SequenceStand(str, Enum):
    """Definition of DNA strand."""

    FORWARD = "+"
    REVERSE = "-"


class PredictionSoftware(str, Enum):
    """Container for prediciton software names."""

    AMRFINDER = "amrfinder"
    RESFINDER = "resfinder"
    VIRFINDER = "virulencefinder"
    SEROTYPEFINDER = "serotypefinder"
    MYKROBE = "mykrobe"
    TBPROFILER = "tbprofiler"


class VariantType(str, Enum):
    """Types of variants."""

    SNV = "SNV"
    MNV = "MNV"
    SV = "SV"
    INDEL = "INDEL"
    STR = "STR"


class VariantSubType(str, Enum):
    """Variant subtypes."""

    INSERTION = "INS"
    DELETION = "DEL"
    SUBSTITUTION = "SUB"
    TRANSISTION = "TS"
    TRANSVERTION = "TV"
    INVERSION = "INV"
    DUPLICATION = "DUP"
    TRANSLOCATION = "BND"


class ElementType(str, Enum):
    """Categories of resistance and virulence genes."""

    AMR = "AMR"
    STRESS = "STRESS"
    VIR = "VIRULENCE"
    ANTIGEN = "ANTIGEN"


class ElementStressSubtype(str, Enum):
    """Categories of resistance and virulence genes."""

    ACID = "ACID"
    BIOCIDE = "BIOCIDE"
    METAL = "METAL"
    HEAT = "HEAT"


class ElementAmrSubtype(str, Enum):
    """Categories of resistance genes."""

    AMR = "AMR"
    POINT = "POINT"


class ElementVirulenceSubtype(str, Enum):
    """Categories of resistance and virulence genes."""

    VIR = "VIRULENCE"
    ANTIGEN = "ANTIGEN"
    TOXIN = "TOXIN"


class AnnotationType(str, Enum):
    """Valid annotation types."""

    TOOL = "tool"
    USER = "user"


class ElementSerotypeSubtype(str, Enum):
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

    ref_database: Optional[str] = None
    ref_id: Optional[str] = None


class GeneBase(BaseModel):
    """Container for gene information"""

    # basic info
    gene_symbol: Optional[str] = None
    accession: Optional[str] = None
    sequence_name: Optional[str] = Field(
        default=None, description="Reference sequence name"
    )
    element_type: ElementType = Field(
        description="The predominant function fo the gene."
    )
    element_subtype: Union[
        ElementStressSubtype,
        ElementAmrSubtype,
        ElementVirulenceSubtype,
        ElementSerotypeSubtype,
    ] = Field(description="Further functional categorization of the genes.")
    # position
    ref_start_pos: Optional[int] = Field(
        None, description="Alignment start in reference"
    )
    ref_end_pos: Optional[int] = Field(None, description="Alignment end in reference")
    ref_gene_length: Optional[int] = Field(
        default=None,
        alias="target_length",
        description="The length of the reference protein or gene.",
    )

    # prediction
    method: Optional[str] = Field(None, description="Method used to predict gene")
    identity: Optional[float] = Field(
        None, description="Identity to reference sequence"
    )
    coverage: Optional[float] = Field(
        None, description="Ratio reference sequence covered"
    )


class AmrFinderGene(GeneBase):
    """Container for Resfinder gene prediction information"""

    contig_id: str
    query_start_pos: int = Field(
        default=None, description="Start position on the assembly"
    )
    query_end_pos: int = Field(default=None, description="End position on the assembly")
    strand: SequenceStand


class AmrFinderVirulenceGene(AmrFinderGene):
    """Container for a virulence gene for AMRfinder."""


class AmrFinderResistanceGene(AmrFinderGene):
    """AMRfinder resistance gene information."""

    phenotypes: list[PhenotypeInfo] = []


class ResistanceGene(GeneBase):
    """Container for resistance gene information"""

    phenotypes: list[PhenotypeInfo] = []


class SerotypeGene(GeneBase):
    """Container for serotype gene information"""


class VirulenceGene(GeneBase, DatabaseReference):
    """Container for virulence gene information"""

    depth: Optional[float] = Field(
        None, description="Amount of sequence data supporting the gene."
    )


class ResfinderGene(ResistanceGene):
    """Container for Resfinder gene prediction information"""

    depth: Optional[float] = Field(
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
    accession: Optional[str] = None
    start: int
    end: int
    ref_nt: str
    alt_nt: str
    ref_aa: Optional[str] = None
    alt_aa: Optional[str] = None

    # prediction info
    depth: Optional[float] = Field(None, description="Total depth, ref + alt.")
    frequency: Optional[float] = Field(None, description="Alt allele frequency.")
    confidence: Optional[float] = Field(None, description="Genotype confidence.")
    method: Optional[str] = Field(
        ..., description="Prediction method used to call variant"
    )
    passed_qc: Optional[bool] = Field(
        ..., description="Describe if variant has passed the tool qc check"
    )


class ResfinderVariant(VariantBase):
    """Container for ResFinder variant information"""


class MykrobeVariant(VariantBase):
    """Container for Mykrobe variant information"""


class TbProfilerVariant(VariantBase):
    """Container for TbProfiler variant information"""

    variant_effect: str | None = None
    hgvs_nt_change: Optional[str] = Field(..., description="DNA change in HGVS format")
    hgvs_aa_change: Optional[str] = Field(
        ..., description="Protein change in HGVS format"
    )


class VirulenceElementTypeResult(BaseModel):
    """Phenotype result data model.

    A phenotype result is a generic data structure that stores predicted genes,
    mutations and phenotyp changes.
    """

    phenotypes: dict[str, list[str]]
    genes: list[AmrFinderVirulenceGene | VirulenceGene]
    variants: list


class ElementTypeResult(BaseModel):
    """Phenotype result data model.

    A phenotype result is a generic data structure that stores predicted genes,
    mutations and phenotyp changes.
    """

    phenotypes: dict[str, list[str]]
    genes: list[Union[AmrFinderResistanceGene, AmrFinderGene, ResfinderGene]]
    variants: list[Union[TbProfilerVariant, MykrobeVariant, ResfinderVariant]]


class AMRMethodIndex(RWModel):
    """Container for key-value lookup of analytical results."""

    type: Literal[ElementType.AMR]
    software: PredictionSoftware
    result: ElementTypeResult


class AntigenMethodIndex(RWModel):
    """Container for key-value lookup of analytical results."""

    type: Literal[ElementType.ANTIGEN]
    software: PredictionSoftware
    result: ElementTypeResult


class StressMethodIndex(RWModel):
    """Container for key-value lookup of analytical results."""

    type: Literal[ElementType.STRESS]
    software: PredictionSoftware
    result: ElementTypeResult


class VirulenceMethodIndex(RWModel):
    """Container for key-value lookup of analytical results."""

    type: Literal[ElementType.VIR]
    software: PredictionSoftware
    result: VirulenceElementTypeResult
