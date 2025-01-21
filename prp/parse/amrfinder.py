"""Parse AMRfinder plus result."""

import logging
from typing import Dict, Tuple, Sequence, Any
import re
import itertools

import numpy as np
import pandas as pd

from ..models.phenotype import (
    AmrFinderResistanceGene,
    AmrFinderGene,
    AmrFinderVirulenceGene,
    AMRMethodIndex,
    AnnotationType,
    ElementType,
    ElementTypeResult,
    PhenotypeInfo,
    AmrFinderVariant
)
from ..models.phenotype import PredictionSoftware as Software
from ..models.phenotype import (
    StressMethodIndex,
    VirulenceElementTypeResult,
    VirulenceMethodIndex,
)
from .utils import classify_variant_type

LOG = logging.getLogger(__name__)

AmrFinderGenes = Sequence[
    AmrFinderGene | AmrFinderVirulenceGene | AmrFinderVirulenceGene
]
AmrFinderVariants = Sequence[AmrFinderVariant]


def _read_result(path: str) -> Tuple[AmrFinderGenes, AmrFinderVariants]:
    """Read AMRfinder output file."""
    result = (
        pd.read_csv(path, delimiter="\t")
        .rename(
            columns={
                "Contig id": "contig_id",
                "Gene symbol": "gene_symbol",
                "Sequence name": "sequence_name",
                "Element type": "element_type",
                "Element subtype": "element_subtype",
                "Target length": "target_length",
                "Reference sequence length": "ref_seq_len",
                "% Coverage of reference sequence": "ref_seq_cov",
                "% Identity to reference sequence": "ref_seq_identity",
                "Alignment length": "align_len",
                "Accession of closest sequence": "close_seq_accn",
                "Name of closest sequence": "close_seq_name",
            }
        )
        .drop(columns=["Protein identifier", "HMM id", "HMM description"])
        .replace(np.nan, None)
        .to_dict(orient="records")  # cast to list of rows
    )
    # cast rows as model objects
    genes = []
    variants = []
    var_no = 1
    for row in result:
        if row["element_subtype"] == "POINT":
            variants.append(_format_variant(row, variant_no=var_no))
            var_no += 1
        else:
            genes.append(_format_gene(row))
    return genes, variants


def _format_gene(
    hit: Dict[str, Any]
) -> AmrFinderGene | AmrFinderVirulenceGene | AmrFinderResistanceGene:
    """Format AMRfinder gene."""
    element_type = ElementType(hit["element_type"])
    match element_type:
        case ElementType.VIR:
            gene_type = AmrFinderVirulenceGene
        case ElementType.AMR:
            gene_type = AmrFinderResistanceGene
        case _:
            gene_type = AmrFinderGene

    # cast base gene
    gene = gene_type(
        # info
        gene_symbol=hit["gene_symbol"],
        accession=hit["close_seq_accn"],
        sequence_name=hit["sequence_name"],
        # gene classification
        element_type=element_type,
        element_subtype=hit["element_subtype"],
        # position
        contig_id=hit["contig_id"],
        query_start_pos=hit["Start"],
        query_end_pos=hit["Stop"],
        strand=hit["Strand"],
        ref_gene_length=hit["ref_seq_len"],
        alignment_length=hit["align_len"],
        # prediction
        method=hit["Method"],
        identity=hit["ref_seq_identity"],
        coverage=hit["ref_seq_cov"],
    )
    # add phenotype to AMR object
    if element_type == ElementType.AMR:
        # classification to phenotype object
        phenotypes = [
            PhenotypeInfo(
                type=element_type,
                group=hit["Class"].lower(),
                name=annot.lower(),
                annotation_type=AnnotationType.TOOL,
                ) for annot in hit["Subclass"].split("/") ]
        gene = gene.model_copy(update={"phenotypes": phenotypes})
    return gene


def _format_variant(hit: Dict[str, Any], variant_no: int) -> AmrFinderVariant:
    gene_name, variant = hit["gene_symbol"].split("_")
    match = re.match(r"([a-z]+)([0-9]+)([a-z]+)", variant, re.I)
    if not match:
        raise ValueError(f"Unrecognized variant format: {variant}")
    ref_aa, pos, alt_aa = match.groups()
    var_type, var_subtype = classify_variant_type(ref_aa, alt_aa, nucleotide=False)

    # add phenotypes
    phenotypes = [
        PhenotypeInfo(
            type=ElementType.AMR,
            group=hit["Class"].lower(),
            name=annot.lower(),
            annotation_type=AnnotationType.TOOL,
            ) for annot in hit["Subclass"].split("/") ]

    return AmrFinderVariant(
        id=variant_no,
        variant_type=var_type,
        variant_subtype=var_subtype,
        # variant location
        reference_sequence=gene_name,
        accession=hit["close_seq_accn"],
        ref_aa=ref_aa,
        alt_aa=alt_aa,
        start=int(pos),
        end=int(pos) + (len(alt_aa) - 1),  # SNVs hav
        # position
        contig_id=hit["contig_id"],
        query_start_pos=hit["Start"],
        query_end_pos=hit["Stop"],
        strand=hit["Strand"],
        ref_gene_length=hit["ref_seq_len"],
        alignment_length=hit["align_len"],
        # prediction
        method=hit["Method"],
        identity=hit["ref_seq_identity"],
        coverage=hit["ref_seq_cov"],
        passed_qc=True,
        phenotypes=phenotypes,
    )


def parse_amr_pred(path: str) -> AMRMethodIndex:
    raw_genes, variants = _read_result(path)
    # sort genes
    element_type = ElementType.AMR
    genes = [
        gene
        for gene in sorted(
            raw_genes, key=lambda entry: (entry.gene_symbol, entry.coverage)
        )
        if gene.element_type == element_type
    ]
    # concat resistance profile
    sr_profile = {
        "susceptible": [],
        "resistant": list(
            {
                pheno.name
                for elem in itertools.chain(genes, variants)
                for pheno in elem.phenotypes
            }
        ),
    }
    result = ElementTypeResult(
        phenotypes=sr_profile,
        genes=genes,
        variants=variants,
    )
    return AMRMethodIndex(type=element_type, software=Software.AMRFINDER, result=result)


def parse_stress_pred(path: str) -> StressMethodIndex:
    """Parse amrfinder stress tolerance results."""
    LOG.info("Parsing amrfinder stress tolerance prediction")
    raw_genes, _ = _read_result(path)
    element_type = ElementType.STRESS
    results = ElementTypeResult(
        genes=[gene for gene in raw_genes if gene.element_type == element_type]
    )
    return StressMethodIndex(
        type=element_type, software=Software.AMRFINDER, result=results
    )


def parse_vir_pred(path: str) -> VirulenceMethodIndex:
    """Parse amrfinder virulence prediction results."""
    LOG.info("Parsing amrfinder virulence prediction")
    raw_genes, _ = _read_result(path)
    element_type = ElementType.VIR
    genes = [
        gene
        for gene in sorted(
            raw_genes, key=lambda entry: (entry.gene_symbol, entry.coverage)
        )
        if gene.element_type == element_type
    ]
    # sort genes
    result = VirulenceElementTypeResult(
        phenotypes={},
        genes=genes,
        variants=[],
    )
    return VirulenceMethodIndex(
        type=element_type, software=Software.AMRFINDER, result=result
    )
