"""Parsers for various typing tools."""

import csv
import json
import logging
from typing import List

from ..models.sample import MethodIndex
from ..models.typing import (
    LineageInformation,
    TypingMethod,
    TypingResultCgMlst,
    TypingResultGeneAllele,
    TypingResultLineage,
    TypingResultMlst,
)
from ..models.typing import TypingSoftware as Software
from .phenotype.virulencefinder import parse_vir_gene

LOG = logging.getLogger(__name__)


def _process_allele_call(allele: str) -> str | List[str] | None:
    if allele.isdigit():
        result = int(allele)
    elif "," in allele:
        result = allele.split(",")
    elif "?" in allele:
        result = "partial"
    elif "~" in allele:
        result = "novel"
    elif allele == "-":
        result = None
    else:
        raise ValueError(f"MLST allele {allele} not expected format")
    return result


def parse_mlst_results(path: str) -> TypingResultMlst:
    """Parse mlst results from mlst to json object."""
    LOG.info("Parsing mlst results")
    result = json.load(path)[0]
    result_obj = TypingResultMlst(
        scheme=result["scheme"],
        sequence_type=None
        if result["sequence_type"] == "-"
        else result["sequence_type"],
        alleles={
            gene: _process_allele_call(allele)
            for gene, allele in result["alleles"].items()
        },
    )
    return MethodIndex(
        type=TypingMethod.MLST, software=Software.MLST, result=result_obj
    )


def parse_cgmlst_results(
    file: str, include_novel_alleles: bool = True, correct_alleles: bool = False
) -> TypingResultCgMlst:
    """Parse chewbbaca cgmlst prediction results to json results.

    Chewbbaca reports errors in allele profile.
    See: https://github.com/B-UMMI/chewBBACA
    -------------------
    INF-<allele name>, inferred new allele
    LNF, loci not found
    PLOT, loci contig tips
    NIPH, non-informative paralogous hits
    NIPHEM,
    ALM, alleles larger than locus length
    ASM, alleles smaller than locus length
    """
    errors = ("LNF", "PLOT3", "PLOT5", "NIPH", "NIPHEM", "ALM", "ASM")

    def replace_errors(allele):
        """Replace errors and novel alleles with null values."""
        if any(
            [
                correct_alleles and allele in errors,
                correct_alleles
                and allele.startswith("INF")
                and not include_novel_alleles,
            ]
        ):
            return None

        if allele.startswith("INF") and include_novel_alleles:
            try:
                allele = int(allele.split("-")[1])
            except ValueError:
                allele = str(allele.split("-")[1])
        # try convert to an int
        try:
            allele = int(allele)
        except ValueError:
            allele = str(allele)
        return allele

    LOG.info(
        "Parsing cgmslt results, %s including novel alleles",
        "not" if not include_novel_alleles else "",
    )

    creader = csv.reader(file, delimiter="\t")
    _, *allele_names = (colname.rstrip(".fasta") for colname in next(creader))
    # parse alleles
    _, *alleles = next(creader)
    corrected_alleles = (replace_errors(a) for a in alleles)
    results = TypingResultCgMlst(
        n_novel=sum(1 for a in alleles if a.startswith("INF")),
        n_missing=sum(1 for a in alleles if a in errors),
        alleles=dict(zip(allele_names, corrected_alleles)),
    )
    return MethodIndex(
        type=TypingMethod.CGMLST, software=Software.CHEWBBACA, result=results
    )


def parse_tbprofiler_lineage_results(pred_res: dict, method) -> TypingResultLineage:
    """Parse tbprofiler results for lineage object."""
    LOG.info("Parsing lineage results")
    result_obj = TypingResultLineage(
        main_lin=pred_res["main_lin"],
        sublin=pred_res["sublin"],
        lineages=pred_res["lineage"],
    )
    return MethodIndex(type=method, software=Software.TBPROFILER, result=result_obj)


def parse_mykrobe_lineage_results(pred_res: dict, method) -> TypingResultLineage | None:
    """Parse mykrobe results for lineage object."""
    LOG.info("Parsing lineage results")
    if len(pred_res) > 0:
        lineage = pred_res[0]
        split_lin = lineage["lineage"].split(".")
        main_lin = split_lin[0]
        sublin = lineage["lineage"]
        lin_idxs = lineage["lineage"].lstrip("lineage").split(".")
        lineages = [
            LineageInformation(lineage="lineage" + ".".join(lin_idxs[: idx + 1]))
            for idx in range(len(lin_idxs))
        ]
        # cast to lineage object
        result_obj = TypingResultLineage(
            main_lin=main_lin,
            sublin=sublin,
            lineages=lineages,
        )
        return MethodIndex(type=method, software=Software.MYKROBE, result=result_obj)


def parse_virulencefinder_stx_typing(path: str) -> MethodIndex | None:
    """Parse virulencefinder's output re stx typing"""
    with open(path, "rb") as inpt:
        pred_obj = json.load(inpt)
        # if has valid results
        pred_result = None
        if "virulencefinder" in pred_obj:
            results = pred_obj["virulencefinder"]["results"]
            species = list(results)
            for assay, result in results[species[0]].items():
                # skip non typing results
                if not assay == "stx":
                    continue

                # if no stx gene was identified
                if isinstance(result, str):
                    continue

                # take first result as the valid prediction
                hit = next(iter(result.values()))
                vir_gene = parse_vir_gene(hit)
                gene = TypingResultGeneAllele(**vir_gene.model_dump())
                pred_result = MethodIndex(
                    type=TypingMethod.STX,
                    software=Software.VIRULENCEFINDER,
                    result=gene,
                )
    return pred_result
