"""Parsers for various typing tools."""

import csv
import json
import logging

from ..models.sample import MethodIndex
from ..models.typing import (
    LineageInformation,
    ResultLineageBase,
    TbProfilerLineage,
    TypingMethod,
    TypingResultCgMlst,
    TypingResultGeneAllele,
    TypingResultMlst,
    ChewbbacaErrors,
)
from ..models.typing import TypingSoftware as Software
from .phenotype.serotypefinder import parse_serotype_gene
from .phenotype.virulencefinder import parse_vir_gene

LOG = logging.getLogger(__name__)


def _process_allele_call(allele: str) -> str | list[str] | None:
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


def parse_mlst_results(mlst_fpath: str) -> TypingResultMlst:
    """Parse mlst results from mlst to json object."""
    LOG.info("Parsing mlst results")
    with open(mlst_fpath, "r", encoding="utf-8") as jsonfile:
        result = json.load(jsonfile)[0]
        result_obj = TypingResultMlst(
            scheme=result["scheme"],
            sequence_type=(
                None if result["sequence_type"] == "-" else result["sequence_type"]
            ),
            alleles={
                gene: _process_allele_call(allele)
                for gene, allele in result["alleles"].items()
            },
        )
    return MethodIndex(
        type=TypingMethod.MLST, software=Software.MLST, result=result_obj
    )


def replace_cgmlst_errors(
    allele: str, include_novel_alleles: bool = True, correct_alleles: bool = False
) -> int | str | None:
    """Replace errors and novel allele calls with null values."""
    errors = [err.value for err in ChewbbacaErrors]
    if any(
        [
            correct_alleles and allele in errors,
            correct_alleles and allele.startswith("INF") and not include_novel_alleles,
        ]
    ):
        return None

    if include_novel_alleles:
        if allele.startswith("INF"):
            allele = allele.split("-")[1]
        else:
            allele = allele.replace("*", "")

    # try convert to an int
    try:
        allele = int(allele)
    except ValueError:
        allele = str(allele)
        LOG.warning(
            "Possible cgMLST parser error, allele could not be cast as an integer: %s",
            allele,
        )
    return allele


def parse_cgmlst_results(
    chewbacca_res_path: str,
    include_novel_alleles: bool = True,
    correct_alleles: bool = False,
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
    EXC, Total number of CDSs classified as EXC
    LOTSC, Total number of CDSs classified as LOTSC
    PAMA, Total number of PAMA classifications
    """

    errors = [err.value for err in ChewbbacaErrors]
    LOG.info(
        "Parsing cgmslt results, %s including novel alleles",
        "not" if not include_novel_alleles else "",
    )

    with open(chewbacca_res_path, encoding="utf-8") as fileh:
        creader = csv.reader(fileh, delimiter="\t")
        _, *allele_names = (colname.rstrip(".fasta") for colname in next(creader))
        # parse alleles
        _, *alleles = next(creader)

    # setup counters for counting novel and missing alleles before correction
    n_novel = 0
    n_missing = 0
    corrected_alleles = []
    for allele in alleles:
        if allele.startswith("INF") or allele.startswith("*"):
            n_novel += 1
        if allele in errors:
            n_missing += 1
        corrected_alleles.append(replace_cgmlst_errors(allele))

    results = TypingResultCgMlst(
        n_novel=n_novel,
        n_missing=n_missing,
        alleles=dict(zip(allele_names, corrected_alleles)),
    )
    return MethodIndex(
        type=TypingMethod.CGMLST, software=Software.CHEWBBACA, result=results
    )


def parse_tbprofiler_lineage_results(pred_res: dict) -> MethodIndex:
    """Parse tbprofiler results for lineage object."""
    LOG.info("Parsing lineage results")
    # lineages
    lineages = [
        LineageInformation(
            lineage=lin["lineage"],
            family=lin["family"],
            rd=lin["rd"],
            fraction=lin["fraction"],
            support=lin["support"],
        )
        for lin in pred_res["lineage"]
    ]
    # combine into result
    result_obj = TbProfilerLineage(
        main_lineage=pred_res["main_lineage"],
        sublineage=pred_res["sub_lineage"],
        lineages=lineages,
    )
    # store result as a method index
    return MethodIndex(
        type=TypingMethod.LINEAGE,
        software=Software.TBPROFILER,
        result=result_obj,
    )


def parse_mykrobe_lineage_results(pred_res: dict) -> MethodIndex | None:
    """Parse mykrobe results for lineage object."""
    LOG.info("Parsing lineage results")
    if pred_res:
        lineage = pred_res[0]["lineage"]
        # cast to lineage object
        result_obj = ResultLineageBase(
            main_lineage=lineage.split(".")[0],
            sublineage=lineage,
        )
        return MethodIndex(
            type=TypingMethod.LINEAGE, software=Software.MYKROBE, result=result_obj
        )
    return None


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


def parse_serotypefinder_oh_typing(path: str) -> MethodIndex | None:
    """Parse serotypefinder's output re OH typing"""
    with open(path, "rb") as inpt:
        pred_obj = json.load(inpt)
        # if has valid results
        pred_result = []
        if "serotypefinder" in pred_obj:
            results = pred_obj["serotypefinder"]["results"]
            for serotype in results:
                # if no serotype gene was identified
                if isinstance(results[serotype], str) or results[serotype] == {}:
                    continue

                # take first result as the valid prediction
                hit = next(iter(results[serotype].values()))
                vir_gene = parse_serotype_gene(hit)
                gene = TypingResultGeneAllele(**vir_gene.model_dump())
                pred_result.append(
                    MethodIndex(
                        type=serotype,
                        software=Software.SEROTYPEFINDER,
                        result=gene,
                    )
                )
    return pred_result
