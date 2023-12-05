"""Parse Mykrobe results."""
import logging
import re
from typing import Any, Dict, Tuple

from ...models.phenotype import ElementTypeResult, ElementType, ElementAmrSubtype
from ...models.phenotype import PredictionSoftware as Software
from ...models.phenotype import ResistanceGene, ResistanceVariant, VariantType
from ...models.sample import MethodIndex
from .utils import is_prediction_result_empty

LOG = logging.getLogger(__name__)


def _get_mykrobe_amr_sr_profie(mykrobe_result):
    """Get mykrobe susceptibility/resistance profile."""
    susceptible = set()
    resistant = set()

    if not mykrobe_result:
        return {}

    for element_type in mykrobe_result:
        if mykrobe_result[element_type]["predict"].upper() == "R":
            resistant.add(element_type)
        else:
            susceptible.add(element_type)
    return {"susceptible": list(susceptible), "resistant": list(resistant)}


def _parse_mykrobe_amr_genes(mykrobe_result) -> Tuple[ResistanceGene, ...]:
    """Get resistance genes from mykrobe result."""
    results = []
    for element_type in mykrobe_result:
        # skip non-resistance yeilding
        if not mykrobe_result[element_type]["predict"].upper() == "R":
            continue

        hits = mykrobe_result[element_type]["called_by"]
        for hit_name, hit in hits.items():
            gene = ResistanceGene(
                gene_symbol=hit_name.split("_")[0],
                accession=None,
                depth=hit["info"]["coverage"]["alternate"]["median_depth"],
                identity=None,
                coverage=hit["info"]["coverage"]["alternate"]["percent_coverage"],
                phenotypes=[element_type.lower()],
                element_type=ElementType.AMR,
                element_subtype=ElementAmrSubtype.AMR,
            )
            results.append(gene)
    return results


def get_mutation_type(var_nom: str) -> Tuple[VariantType, str, str, int]:
    """Extract mutation type from Mykrobe mutation description.

    GCG7569GTG -> mutation type, ref_nt, alt_nt, pos

    :param var_nom: Mykrobe mutation description
    :type var_nom: str
    :return: Return variant type, ref_codon, alt_codont and position
    :rtype: Tuple[VariantType, str, str, int]
    """
    mut_type = None
    ref_codon = None
    alt_codon = None
    position = None
    try:
        ref_idx = re.search(r"\d", var_nom, 1).start()
        alt_idx = re.search(r"\d(?=[^\d]*$)", var_nom).start() + 1
    except AttributeError:
        return mut_type, ref_codon, alt_codon, position

    ref_codon = var_nom[:ref_idx]
    alt_codon = var_nom[alt_idx:]
    position = int(var_nom[ref_idx:alt_idx])
    if len(ref_codon) > len(alt_codon):
        mut_type = VariantType.DELETION
    elif len(ref_codon) < len(alt_codon):
        mut_type = VariantType.INSERTION
    else:
        mut_type = VariantType.SUBSTITUTION
    return mut_type, ref_codon, alt_codon, position


def _parse_mykrobe_amr_variants(mykrobe_result) -> Tuple[ResistanceVariant, ...]:
    """Get resistance genes from mykrobe result."""
    results = []

    for element_type in mykrobe_result:
        # skip non-resistance yeilding
        if not mykrobe_result[element_type]["predict"].upper() == "R":
            continue

        hits = mykrobe_result[element_type]["called_by"]
        for hit in hits:
            if hits[hit]["variant"] is not None:
                continue

            var_info = hit.split("-")[1]
            _, ref_nt, alt_nt, position = get_mutation_type(var_info)
            var_nom = hit.split("-")[0].split("_")[1]
            var_type, *_ = get_mutation_type(var_nom)
            variant = ResistanceVariant(
                variant_type=var_type,
                genes=[hit.split("_")[0]],
                phenotypes=[element_type],
                position=position,
                ref_nt=ref_nt,
                alt_nt=alt_nt,
                depth=hits[hit]["info"]["coverage"]["alternate"]["median_depth"],
                ref_database=None,
                ref_id=None,
                type=None,
                change=var_nom,
                nucleotide_change=None,
                protein_change=None,
                annotation=None,
                drugs=None,
            )
            results.append(variant)
    return results


def parse_mykrobe_amr_pred(
    prediction: Dict[str, Any], resistance_category
) -> ElementTypeResult | None:
    """Parse mykrobe resistance prediction results."""
    LOG.info("Parsing mykrobe prediction")
    pred = prediction["susceptibility"]
    resistance = ElementTypeResult(
        phenotypes=_get_mykrobe_amr_sr_profie(pred),
        genes=_parse_mykrobe_amr_genes(pred),
        mutations=_parse_mykrobe_amr_variants(pred),
    )

    # verify prediction result
    if is_prediction_result_empty(resistance):
        result = None
    else:
        result = MethodIndex(
            type=resistance_category, software=Software.MYKROBE, result=resistance
        )
    return result
