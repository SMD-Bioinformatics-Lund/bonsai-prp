"""Datamodels used for prediction results."""
from enum import Enum
from typing import Dict, List, Optional, Union

from pydantic import BaseModel

from .base import RWModel


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
    ACID = "STRESS_ACID"
    BIOCIDE = "STRESS_BIOCIDE"
    METAL = "STRESS_METAL"
    HEAT = "STRESS_HEAT"
    VIR = "VIRULENCE"


class DatabaseReference(RWModel):
    """Refernece to a database."""

    ref_database: Optional[str]
    ref_id: Optional[str]


class GeneBase(BaseModel):
    """Container for gene information"""

    accession: Optional[str]
    # prediction info
    depth: Optional[float]
    identity: Optional[float]
    coverage: Optional[float]
    ref_start_pos: Optional[int]
    ref_end_pos: Optional[int]
    ref_gene_length: Optional[int]
    alignment_length: Optional[int]
    # amrfinder extra info
    contig_id: Optional[str]
    gene_symbol: Optional[str]
    sequence_name: Optional[str]
    ass_start_pos: Optional[int]
    ass_end_pos: Optional[int]
    strand: Optional[str]
    element_type: Optional[str]
    element_subtype: Optional[str]
    target_length: Optional[int]
    res_class: Optional[str]
    res_subclass: Optional[str]
    method: Optional[str]
    close_seq_name: Optional[str]


class ResistanceGene(GeneBase, DatabaseReference):
    """Container for resistance gene information"""

    phenotypes: List[str]


class VirulenceGene(GeneBase, DatabaseReference):
    """Container for virulence gene information"""

    virulence_category: Optional[str]


class VariantBase(DatabaseReference):
    """Container for mutation information"""

    variant_type: Optional[VariantType]
    genes: Optional[List[str]]
    position: Optional[int]
    ref_nt: Optional[str]
    alt_nt: Optional[str]
    # prediction info
    depth: Optional[float]
    contig_id: Optional[str]
    gene_symbol: Optional[str]
    sequence_name: Optional[str]
    ass_start_pos: Optional[int]
    ass_end_pos: Optional[int]
    strand: Optional[str]
    element_type: Optional[str]
    element_subtype: Optional[str]
    target_length: Optional[int]
    res_class: Optional[str]
    res_subclass: Optional[str]
    method: Optional[str]
    close_seq_name: Optional[str]
    type: Optional[str]
    change: Optional[str]
    nucleotide_change: Optional[str]
    protein_change: Optional[str]
    annotation: Optional[List[Dict]]
    drugs: Optional[List[Dict]]


class ResistanceVariant(VariantBase):
    """Container for resistance variant information"""

    phenotypes: List[str]


class ElementTypeResult(BaseModel):
    """Phenotype result data model.

    A phenotype result is a generic data structure that stores predicted genes,
    mutations and phenotyp changes.
    """

    phenotypes: Dict[str, List[str]]
    genes: List[Union[ResistanceGene, VirulenceGene]]
    mutations: List[ResistanceVariant]
