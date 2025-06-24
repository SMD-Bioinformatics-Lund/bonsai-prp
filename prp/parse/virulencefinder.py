"""Functions for parsing virulencefinder result."""

import json
import logging
from typing import Any

from ..models.phenotype import ElementType, ElementVirulenceSubtype
from ..models.phenotype import PredictionSoftware as Software
from ..models.phenotype import (
    VirulenceElementTypeResult,
    VirulenceGene,
    VirulenceMethodIndex,
)
from ..models.sample import MethodIndex
from ..models.typing import TypingMethod, TypingResultGeneAllele

LOG = logging.getLogger(__name__)


def parse_vir_gene(
    info: dict[str, Any], subtype: ElementVirulenceSubtype = ElementVirulenceSubtype.VIR, function: str
) -> VirulenceGene:
    """Parse virulence gene prediction results."""
    accnr = None if info["ref_acc"] == "NA" else info["ref_acc"]
   
    return VirulenceGene(
        # info
        gene_symbol=info["name"],
        accession=accnr,
        sequence_name=function,
        # gene classification
        element_type=ElementType.VIR,
        element_subtype=subtype,
        # position
        ref_start_pos=info["ref_start_pos"],
        ref_end_pos=info["ref_end_pos"],
        ref_gene_length=info["ref_seq_length"],
        alignment_length=info["alignment_length"],
        # prediction
        identity=info["identity"],
        coverage=info["coverage"],
    )


def _parse_vir_results(pred: dict[str, Any]) -> VirulenceElementTypeResult:
    """Parse virulence prediction results from virulencefinder."""
    # parse virulence finder results
    vir_genes = []
    
    for key, pheno in phenotypes.items():
        function = pheno.get("function", "")
        ref_dbs = pheno.get("ref_database", [])

        # skip stx typing result # needed? How is it different?
        #if any("stx" in db for db in ref_dbs):
        #    continue

        # assign element subtype
        subtype = ElementVirulenceSubtype.VIR
        if any("toxin" in db for db in ref_dbs):
            subtype = ElementVirulenceSubtype.TOXIN

        # parse genes
        for region_key in pheno.get("seq_regions", []):
            seq_info = seq_regions.get(region_key)
            if not seq_info:
                continue
            vir_genes.append(parse_vir_gene(seq_info, subtype=subtype, function=function))
    # sort genes
    genes = sorted(vir_genes, key=lambda entry: (entry.gene_symbol, entry.coverage))
    return VirulenceElementTypeResult(genes=genes, phenotypes={}, variants=[])


def parse_virulence_pred(path: str) -> VirulenceMethodIndex | None:
    """Parse virulencefinder virulence prediction results.

    :param file: File name
    :type file: str
    :return: Return element type if virulence was predicted else null
    :rtype: ElementTypeResult | None
    """
    LOG.info("Parsing virulencefinder virulence prediction")
    with open(path, "rb") as inpt:
        pred = json.load(inpt)
        if "virulencefinder" in pred:
            results: VirulenceElementTypeResult = _parse_vir_results(pred)
            result = VirulenceMethodIndex(
                type=ElementType.VIR, software=Software.VIRFINDER, result=results
            )
        else:
            result = None
    return result


# def parse_stx_typing(path: str) -> MethodIndex | None:
#     """Parse virulencefinder's output re stx typing"""
#     LOG.info("Parsing virulencefinder stx results")
#     with open(path, "rb") as inpt:
#         pred_obj = json.load(inpt)
#         # if has valid results
#         pred_result = None
#         if "virulencefinder" in pred_obj:
#             results = pred_obj["virulencefinder"]["results"]
#             species = list(results)
#             for assay, result in results[species[0]].items():
#                 # skip non typing results
#                 if not assay == "stx":
#                     continue

#                 # if no stx gene was identified
#                 if isinstance(result, str):
#                     continue

#                 # take first result as the valid prediction
#                 hit = next(iter(result.values()))
#                 vir_gene = parse_vir_gene(hit)
#                 gene = TypingResultGeneAllele(**vir_gene.model_dump())
#                 pred_result = MethodIndex(
#                     type=TypingMethod.STX,
#                     software=Software.VIRFINDER,
#                     result=gene,
#                 )
#     return pred_result
