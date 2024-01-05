"""Datamodels used for prediction results."""
from enum import Enum
from typing import Dict, List, Optional, Union, Any

from pydantic import BaseModel, Field

from .base import RWModel


class SequenceStand(Enum):
    """Definition of DNA strand."""

    FORWARD = "+"
    REVERSE = "-"


class PredictionSoftware(Enum):
    """Container for prediciton software names."""

    AMRFINDER = "amrfinder"
    RESFINDER = "resfinder"
    VIRFINDER = "virulencefinder"
    MYKROBE = "mykrobe"
    TBPROFILER = "tbprofiler"


class VariantType(Enum):
    """Types of variants."""

    SUBSTITUTION = "substitution"
    INSERTION = "insertion"
    DELETION = "deletion"


class ElementType(Enum):
    """Categories of resistance and virulence genes."""

    AMR = "AMR"
    STRESS = "STRESS"
    VIR = "VIRULENCE"


class ElementStressSubtype(Enum):
    """Categories of resistance and virulence genes."""

    ACID = "ACID"
    BIOCIDE = "BIOCIDE"
    METAL = "METAL"
    HEAT = "HEAT"


class ElementAmrSubtype(Enum):
    """Categories of resistance and virulence genes."""

    AMR = "AMR"


class ElementVirulenceSubtype(Enum):
    """Categories of resistance and virulence genes."""

    VIR = "VIRULENCE"
    ANTIGEN = "ANTIGEN"
    TOXIN = "TOXIN"


class PhenotypeInfo(RWModel):
    """Phenotype information."""

    name: str
    group: str | None = Field(None, description="Name of the group a trait belongs to.")
    type: ElementType = Field(
        ..., description="Trait category, for example AMR, STRESS etc."
    )
    reference: List[str] = Field([], description="References supporting trait")
    note: str | None = Field(None, description="Note, can be used for confidence score")


class DatabaseReference(RWModel):
    """Refernece to a database."""

    ref_database: Optional[str] = None
    ref_id: Optional[str] = None


class GeneBase(BaseModel):
    """Container for gene information"""

    accession: Optional[str] = None
    # prediction info
    depth: Optional[float] = None
    identity: Optional[float] = None
    coverage: Optional[float] = None
    ref_start_pos: Optional[int] = None
    ref_end_pos: Optional[int] = None
    drugs: Optional[List[Union[Dict, str]]] = None
    ref_gene_length: Optional[int] = Field(
        default=None,
        alias="target_length",
        description="The length of the query protein or gene.",
    )
    alignment_length: Optional[int] = None
    # amrfinder extra info
    contig_id: Optional[str] = None
    gene_symbol: Optional[str] = None
    sequence_name: Optional[str] = Field(
        default=None, description="Reference sequence name"
    )
    ass_start_pos: Optional[int] = Field(
        default=None, description="Start position on the assembly"
    )
    ass_end_pos: Optional[int] = Field(
        default=None, description="End position on the assembly"
    )
    strand: Optional[SequenceStand] = None
    element_type: ElementType = Field(
        description="The predominant function fo the gene."
    )
    element_subtype: Union[
        ElementStressSubtype, ElementAmrSubtype, ElementVirulenceSubtype
    ] = Field(description="Further functional categorization of the genes.")
    res_class: Optional[str] = None
    res_subclass: Optional[str] = None
    method: Optional[str] = Field(
        default=None, description="Generic description of the prediction method"
    )
    close_seq_name: Optional[str] = Field(
        default=None,
        description=(
            "Name of the closest competing hit if there "
            "are multiple equaly good hits"
        ),
    )


class ResistanceGene(GeneBase, DatabaseReference):
    """Container for resistance gene information"""

    phenotypes: List[PhenotypeInfo] = []


class VirulenceGene(GeneBase, DatabaseReference):
    """Container for virulence gene information"""


class VariantBase(DatabaseReference):
    """Container for mutation information"""

    variant_type: VariantType
    position: int
    ref_nt: str
    alt_nt: str
    ref_aa: Optional[str] = None
    alt_aa: Optional[str] = None
    # prediction info
    depth: Optional[float] = Field(None, description="Total depth, ref + alt.")
    frequency: Optional[float] = Field(None, description="Alt allele frequency.")
    contig_id: Optional[str] = None
    gene_symbol: Optional[str] = None
    sequence_name: Optional[str] = Field(
        default=None, description="Reference sequence name"
    )
    ass_start_pos: Optional[int] = Field(
        default=None, description="Assembly start position"
    )
    ass_end_pos: Optional[int] = Field(
        default=None, description="Assembly end position"
    )
    strand: Optional[SequenceStand] = None
    element_type: Optional[ElementType] = None
    element_subtype: Optional[str] = None
    target_length: Optional[int] = None
    res_class: Optional[str] = None
    res_subclass: Optional[str] = None
    method: Optional[str] = None
    close_seq_name: Optional[str] = None
    change: Optional[str] = None
    phenotypes: List[PhenotypeInfo] = []


class ResfinderVariant(VariantBase):
    """Container for ResFinder variant information"""


class MykrobeVariant(VariantBase):
    """Container for Mykrobe variant information"""

    confidence: int


class TbProfilerVariant(VariantBase):
    """Container for TbProfiler variant information"""

    type: str
    annotation: List[Any]

class ElementTypeResult(BaseModel):
    """Phenotype result data model.

    A phenotype result is a generic data structure that stores predicted genes,
    mutations and phenotyp changes.
    """

    phenotypes: Dict[str, List[str]]
    genes: List[Union[ResistanceGene, VirulenceGene]]
    mutations: List[Union[ResfinderVariant, TbProfilerVariant, MykrobeVariant]]
