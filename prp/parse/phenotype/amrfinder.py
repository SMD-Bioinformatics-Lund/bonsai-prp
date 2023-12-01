"""Parse AMRfinder plus result."""
from typing import Tuple

import pandas as pd

from ...models.phenotype import ElementType, ElementTypeResult
from ...models.phenotype import PredictionSoftware as Software
from ...models.phenotype import ResistanceGene, VirulenceGene
from ...models.sample import MethodIndex
from .utils import _default_resistance


def _parse_amrfinder_amr_results(predictions: dict) -> Tuple[ResistanceGene, ...]:
    """Parse amrfinder prediction results from amrfinderplus."""
    genes = []
    for prediction in predictions:
        gene = ResistanceGene(
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
            ass_start_pos=prediction["Start"],
            ass_end_pos=prediction["Stop"],
            strand=prediction["Strand"],
            element_type=prediction["element_type"],
            element_subtype=prediction["element_subtype"],
            target_length=prediction["target_length"],
            res_class=prediction["Class"],
            res_subclass=prediction["Subclass"],
            method=prediction["Method"],
            close_seq_name=prediction["close_seq_name"],
        )
        genes.append(gene)
    return ElementTypeResult(phenotypes=[], genes=genes, mutations=[])


def parse_amrfinder_amr_pred(file, element_type: str) -> ElementTypeResult:
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
        if element_type == ElementType.AMR:
            predictions = hits[hits["element_type"] == "AMR"].to_dict(orient="records")
            results: ElementTypeResult = _parse_amrfinder_amr_results(predictions)
        elif element_type == ElementType.HEAT:
            predictions = hits[(hits["element_subtype"] == "HEAT")].to_dict(
                orient="records"
            )
            results: ElementTypeResult = _parse_amrfinder_amr_results(predictions)
        elif element_type == ElementType.BIOCIDE:
            predictions = hits[
                (hits["element_subtype"] == "ACID")
                & (hits["element_subtype"] == "BIOCIDE")
            ].to_dict(orient="records")
            results: ElementTypeResult = _parse_amrfinder_amr_results(predictions)
        elif element_type == ElementType.METAL:
            predictions = hits[hits["element_subtype"] == "METAL"].to_dict(
                orient="records"
            )
            results: ElementTypeResult = _parse_amrfinder_amr_results(predictions)
        else:
            results = _default_resistance()
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
    return ElementTypeResult(phenotypes=[], genes=genes, mutations=[])


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
