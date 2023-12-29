"""Parse TBprofiler result."""
import logging
from typing import Any, Dict, Tuple

from ...models.metadata import SoupVersions
from ...models.phenotype import ElementTypeResult, ElementType, PhenotypeInfo
from ...models.phenotype import PredictionSoftware as Software
from ...models.phenotype import ResistanceVariant
from ...models.sample import MethodIndex
from .utils import _default_variant, _default_amr_phenotype

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


def _parse_tbprofiler_amr_variants(tbprofiler_result) -> Tuple[ResistanceVariant, ...]:
    """Get resistance genes from tbprofiler result."""
    results = []

    for hit in tbprofiler_result["dr_variants"]:
        var_type = "substitution"

        variant = ResistanceVariant(
            variant_type=var_type,
            genes=[hit["gene"]],
            phenotypes=[_default_amr_phenotype()],
            position=int(hit["genome_pos"]),
            ref_nt=hit["ref"],
            alt_nt=hit["alt"],
            depth=hit["depth"],
            ref_database=tbprofiler_result["db_version"]["name"],
            type=hit["type"],
            nucleotide_change=hit["nucleotide_change"],
            protein_change=hit["protein_change"],
            annotation=hit["annotation"],
            drugs=hit["drugs"],
        )
        results.append(variant)

    if not results:
        results = _default_variant().mutations
        return results

    return results


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
