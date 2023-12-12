"""Parse AMRfinder plus result."""
import logging
from typing import Tuple

import pandas as pd

from ...models.phenotype import ElementType, ElementTypeResult
from ...models.phenotype import PredictionSoftware as Software
from ...models.phenotype import ResistanceGene, VirulenceGene, PhenotypeInfo
from ...models.sample import MethodIndex

LOG = logging.getLogger(__name__)


def _parse_amrfinder_amr_results(predictions: dict) -> Tuple[ResistanceGene, ...]:
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
                    res_class=element_type,
                    name=element_type,
                ))
        elif isinstance(res_sub_class, str):
            phenotypes.extend([
                PhenotypeInfo(
                    type=element_type,
                    res_class=res_class.lower(),
                    name=annot.lower(),
                ) for annot in res_sub_class.split("/")])
        # store resistance gene
        gene = ResistanceGene(
            accession=prediction["close_seq_accn"],
            identity=prediction["ref_seq_identity"],
            coverage=prediction["ref_seq_cov"],
            ref_gene_length=prediction["ref_seq_len"],
            alignment_length=prediction["align_len"],
            contig_id=prediction["contig_id"],
            gene_symbol=prediction["gene_symbol"],
            sequence_name=prediction["sequence_name"],
            ass_start_pos=prediction["Start"],
            ass_end_pos=prediction["Stop"],
            strand=prediction["Strand"],
            element_type=element_type,
            element_subtype=prediction["element_subtype"],
            target_length=prediction["target_length"],
            res_class=res_class,
            res_subclass=res_sub_class,
            method=prediction["Method"],
            close_seq_name=prediction["close_seq_name"],
            phenotypes=phenotypes,
        )
        genes.append(gene)
        
    # concat resistance profile
    sr_profile = {
        "susceptible": [],
        "resistant": [pheno.name for gene in genes for pheno in gene.phenotypes]
    }
    return ElementTypeResult(phenotypes=sr_profile, genes=genes, mutations=[])


def parse_amrfinder_amr_pred(file: str, element_type: ElementType) -> ElementTypeResult:
    """Parse amrfinder resistance prediction results."""
    LOG.info("Parsing amrfinder amr prediction")
    with open(file, "rb") as tsvfile:
        hits = pd.read_csv(tsvfile, delimiter="\t")
        hits = hits.rename(
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
        hits = hits.drop(columns=["Protein identifier", "HMM id", "HMM description"])
        hits = hits.where(pd.notnull(hits), None)
        # group predictions based on their element type
        predictions = hits.loc[lambda row: row.element_type == element_type.value].to_dict(
            orient="records"
        )
        results: ElementTypeResult = _parse_amrfinder_amr_results(predictions)
    return MethodIndex(type=element_type, result=results, software=Software.AMRFINDER)


def _parse_amrfinder_vir_results(predictions: dict) -> ElementTypeResult:
    """Parse amrfinder prediction results from amrfinderplus."""
    genes = []
    for prediction in predictions:
        gene = VirulenceGene(
            name=None,
            virulence_category=None,
            accession=prediction["close_seq_accn"],
            depth=None,
            identity=prediction["ref_seq_identity"],
            coverage=prediction["ref_seq_cov"],
            ref_start_pos=None,
            ref_end_pos=None,
            ref_gene_length=prediction["ref_seq_len"],
            alignment_length=prediction["align_len"],
            ref_database=None,
            phenotypes=[],
            ref_id=None,
            contig_id=prediction["contig_id"],
            gene_symbol=prediction["gene_symbol"],
            sequence_name=prediction["sequence_name"],
            ass_start_pos=int(prediction["Start"]),
            ass_end_pos=int(prediction["Stop"]),
            strand=prediction["Strand"],
            element_type=prediction["element_type"],
            element_subtype=prediction["element_subtype"],
            target_length=int(prediction["target_length"]),
            res_class=prediction["Class"],
            res_subclass=prediction["Subclass"],
            method=prediction["Method"],
            close_seq_name=prediction["close_seq_name"],
        )
        genes.append(gene)
    return ElementTypeResult(phenotypes={}, genes=genes, mutations=[])


def parse_amrfinder_vir_pred(file: str):
    """Parse amrfinder virulence prediction results."""
    LOG.info("Parsing amrfinder virulence prediction")
    with open(file, "rb") as tsvfile:
        hits = pd.read_csv(tsvfile, delimiter="\t")
        hits = hits.rename(
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
        hits = hits.drop(columns=["Protein identifier", "HMM id", "HMM description"])
        hits = hits.where(pd.notnull(hits), None)
        predictions = hits[hits["element_type"] == "VIRULENCE"].to_dict(
            orient="records"
        )
        results: ElementTypeResult = _parse_amrfinder_vir_results(predictions)
    return MethodIndex(
        type=ElementType.VIR, software=Software.AMRFINDER, result=results
    )
