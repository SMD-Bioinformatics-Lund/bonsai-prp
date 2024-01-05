"""Parse TBprofiler result."""
import logging
from typing import Any, Dict, Tuple, List

from ...models.metadata import SoupVersions
from ...models.phenotype import (
    ElementTypeResult,
    TbProfilerVariant,
    VariantType,
    PhenotypeInfo,
    ElementType,
)
from ...models.phenotype import PredictionSoftware as Software
from ...models.sample import MethodIndex

LOG = logging.getLogger(__name__)


def _get_tbprofiler_amr_sr_profie(tbprofiler_result):
    """Get tbprofiler susceptibility/resistance profile."""
    susceptible = set()
    resistant = set()
    drugs = [
        "ofloxacin",
        "moxifloxacin",
        "isoniazid",
        "delamanid",
        "kanamycin",
        "amikacin",
        "ethambutol",
        "ethionamide",
        "streptomycin",
        "ciprofloxacin",
        "levofloxacin",
        "pyrazinamide",
        "linezolid",
        "rifampicin",
        "capreomycin",
    ]

    if not tbprofiler_result:
        return {}

    for hit in tbprofiler_result["dr_variants"]:
        for drug in hit["gene_associated_drugs"]:
            resistant.add(drug)
    susceptible = [drug for drug in drugs if drug not in resistant]
    return {"susceptible": list(susceptible), "resistant": list(resistant)}


def _parse_tbprofiler_amr_variants(tbprofiler_result) -> Tuple[TbProfilerVariant, ...]:
    """Get resistance genes from tbprofiler result."""
    results = []

    for hit in tbprofiler_result["dr_variants"]:
        ref_nt = hit["ref"]
        alt_nt = hit["alt"]
        if len(ref_nt) == len(alt_nt):
            var_type = VariantType.SUBSTITUTION
        elif len(ref_nt) > len(alt_nt):
            var_type = VariantType.DELETION
        else:
            var_type = VariantType.INSERTION

        variant = TbProfilerVariant(
            variant_type=var_type,
            gene_symbol=hit["gene"],
            phenotypes=[],
            position=int(hit["genome_pos"]),
            ref_nt=ref_nt,
            alt_nt=alt_nt,
            depth=hit["depth"],
            frequency=float(hit["freq"]),
            ref_database=tbprofiler_result["db_version"]["name"],
            type=hit["type"],
            nucleotide_change=hit["nucleotide_change"],
            protein_change=hit["protein_change"],
            annotation=hit["annotation"],
            phenotype=hit["drugs"],
        )
        results.append(variant)
    return results


def parse_drug_resistance_info(drugs: List[Dict[str, str]]) -> List[PhenotypeInfo]:
    """Parse drug info into the standard format.

    :param drugs: TbProfiler drug info
    :type drugs: List[Dict[str, str]]
    :return: Formatted phenotype info
    :rtype: List[PhenotypeInfo]
    """
    phenotypes = []
    for drug in drugs:
        # assign element type
        if drug["type"] == "drug" and drug["confers"] == "resistance":
            drug_type = ElementType.AMR
        else:
            drug_type = ElementType.AMR
            LOG.warning(
                "Unknown TbProfiler drug; drug: %s, confers: %s; default to %s",
                drug["type"],
                drug["confers"],
                drug_type,
            )
        phenotypes.append(
            PhenotypeInfo(
                name=drug["drug"],
                type=drug_type,
                reference=[drug["litterature"]],
                note=drug["who confidence"],
            )
        )
    return phenotypes


def parse_tbprofiler_amr_pred(
    prediction: Dict[str, Any], resistance_category
) -> Tuple[SoupVersions, ElementTypeResult]:
    """Parse tbprofiler resistance prediction results."""
    LOG.info("Parsing tbprofiler prediction")
    resistance = ElementTypeResult(
        phenotypes=_get_tbprofiler_amr_sr_profie(prediction),
        genes=[],
        mutations=_parse_tbprofiler_amr_variants(prediction),
    )
    return MethodIndex(
        type=resistance_category, software=Software.TBPROFILER, result=resistance
    )
