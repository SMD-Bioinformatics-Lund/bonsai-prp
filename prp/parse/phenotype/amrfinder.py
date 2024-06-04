"""Parse AMRfinder plus result."""
import logging

import numpy as np
import pandas as pd

from ...models.phenotype import (
    AmrFinderResistanceGene,
    AmrFinderVirulenceGene,
    AMRMethodIndex,
    AnnotationType,
    ElementType,
    ElementTypeResult,
    PhenotypeInfo,
)
from ...models.phenotype import PredictionSoftware as Software
from ...models.phenotype import (
    StressMethodIndex,
    VirulenceElementTypeResult,
    VirulenceMethodIndex,
)

LOG = logging.getLogger(__name__)


def _parse_amrfinder_amr_results(
    predictions: dict,
) -> tuple[AmrFinderResistanceGene, ...]:
    """Parse amrfinder prediction results from amrfinderplus."""
    genes = []
    for prediction in predictions:
        element_type = ElementType(prediction["element_type"])
        res_class = prediction["Class"]
        res_sub_class = prediction["Subclass"]

        # classification to phenotype object
        phenotypes = []
        if res_class is None:
            phenotypes.append(
                PhenotypeInfo(
                    type=element_type,
                    group=element_type,
                    name=element_type,
                    annotation_type=AnnotationType.TOOL,
                    annotation_author=Software.AMRFINDER.value,
                )
            )
        elif isinstance(res_sub_class, str):
            phenotypes.extend(
                [
                    PhenotypeInfo(
                        type=element_type,
                        group=res_class.lower(),
                        name=annot.lower(),
                        annotation_type=AnnotationType.TOOL,
                    )
                    for annot in res_sub_class.split("/")
                ]
            )
        # store resistance gene
        gene = AmrFinderResistanceGene(
            # info
            gene_symbol=prediction["gene_symbol"],
            accession=prediction["close_seq_accn"],
            sequence_name=prediction["sequence_name"],
            # gene classification
            element_type=element_type,
            element_subtype=prediction["element_subtype"],
            phenotypes=phenotypes,
            # position
            contig_id=prediction["contig_id"],
            query_start_pos=prediction["Start"],
            query_end_pos=prediction["Stop"],
            strand=prediction["Strand"],
            ref_gene_length=prediction["ref_seq_len"],
            alignment_length=prediction["align_len"],
            # prediction
            method=prediction["Method"],
            identity=prediction["ref_seq_identity"],
            coverage=prediction["ref_seq_cov"],
        )
        genes.append(gene)

    # concat resistance profile
    sr_profile = {
        "susceptible": [],
        "resistant": list({pheno.name for gene in genes for pheno in gene.phenotypes}),
    }
    # sort genes
    genes = sorted(genes, key=lambda entry: (entry.gene_symbol, entry.coverage))
    return ElementTypeResult(phenotypes=sr_profile, genes=genes, variants=[])


def parse_amrfinder_amr_pred(file: str, element_type: ElementType) -> AMRMethodIndex:
    """Parse amrfinder resistance prediction results."""
    LOG.info("Parsing amrfinder amr prediction")
    hits = (
        pd.read_csv(file, delimiter="\t")
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
    )
    # group predictions based on their element type
    predictions = hits.loc[lambda row: row.element_type == element_type.value].to_dict(
        orient="records"
    )
    results: ElementTypeResult = _parse_amrfinder_amr_results(predictions)
    if element_type == ElementType.AMR:
        result = AMRMethodIndex(
            type=element_type, result=results, software=Software.AMRFINDER
        )
    else:
        result = StressMethodIndex(
            type=element_type, result=results, software=Software.AMRFINDER
        )
    return result


def _parse_amrfinder_vir_results(predictions: dict) -> VirulenceElementTypeResult:
    """Parse amrfinder prediction results from amrfinderplus."""
    genes = []
    for prediction in predictions:
        gene = AmrFinderVirulenceGene(
            # info
            gene_symbol=prediction["gene_symbol"],
            accession=prediction["close_seq_accn"],
            sequence_name=prediction["sequence_name"],
            # gene classification
            element_type=prediction["element_type"],
            element_subtype=prediction["element_subtype"],
            # position
            contig_id=prediction["contig_id"],
            query_start_pos=prediction["Start"],
            query_end_pos=prediction["Stop"],
            strand=prediction["Strand"],
            ref_gene_length=prediction["ref_seq_len"],
            alignment_length=prediction["align_len"],
            # prediction
            method=prediction["Method"],
            identity=prediction["ref_seq_identity"],
            coverage=prediction["ref_seq_cov"],
        )
        genes.append(gene)
    # sort genes
    genes = sorted(genes, key=lambda entry: (entry.gene_symbol, entry.coverage))
    return VirulenceElementTypeResult(phenotypes={}, genes=genes, variants=[])


def parse_amrfinder_vir_pred(file: str) -> VirulenceMethodIndex:
    """Parse amrfinder virulence prediction results."""
    LOG.info("Parsing amrfinder virulence prediction")
    hits = (
        pd.read_csv(file, delimiter="\t")
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
    )
    predictions = hits[hits["element_type"] == "VIRULENCE"].to_dict(orient="records")
    results: VirulenceElementTypeResult = _parse_amrfinder_vir_results(predictions)
    return VirulenceMethodIndex(
        type=ElementType.VIR, software=Software.AMRFINDER, result=results
    )
