"""Parse Mykrobe results."""
import logging
import re
from typing import Any, Dict, Tuple

from ...models.phenotype import ElementType, ElementTypeResult, MykrobeVariant, VariantType, PhenotypeInfo
from ...models.phenotype import PredictionSoftware as Software
from ...models.sample import MethodIndex
from .utils import is_prediction_result_empty, get_nt_change

LOG = logging.getLogger(__name__)


def _get_mykrobe_amr_sr_profie(mykrobe_result):
    """Get mykrobe susceptibility/resistance profile."""
    susceptible = set()
    resistant = set()

    if not mykrobe_result:
        return {}

    for element_type in mykrobe_result:
        if element_type["susceptibility"].upper() == "R":
            resistant.add(element_type["drug"])
        else:
            susceptible.add(element_type["drug"])
    return {"susceptible": list(susceptible), "resistant": list(resistant)}


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


def _parse_mykrobe_amr_variants(mykrobe_result) -> Tuple[MykrobeVariant, ...]:
    """Get resistance genes from mykrobe result."""
    results = []

    for element_type in mykrobe_result:
        # skip non-resistance yeilding
        if not element_type["susceptibility"].upper() == "R":
            continue

        if element_type["variants"] is None:
            continue

        # generate phenotype info
        phenotype = [PhenotypeInfo(
            name=element_type['drug'], type=ElementType.AMR
        )]

        variants = element_type["variants"].split(";")
        # Mykrobe CSV variant format
        # <gene>_<amino acid change>-<dna change>:<ref depth>:<alt depth>:<genotype confidence>
        # ref: https://github.com/Mykrobe-tools/mykrobe/wiki/AMR-prediction-output
        PATTERN = re.compile(
            r"(.+)_(.+)-(.+):(\d+):(\d+):(\d+)", re.I
        )
        for variant in variants:
            # extract variant info using regex
            match = re.search(PATTERN, variant)
            gene, aa_change, dna_change, ref_depth, alt_depth, conf = match.groups()

            # get type of variant
            var_type, ref_aa, alt_aa, _ = get_mutation_type(aa_change)

            # reduce codon to nt change for substitutions
            _, ref_nt, alt_nt, position = get_mutation_type(dna_change)
            if var_type == VariantType.SUBSTITUTION:
                ref_nt, alt_nt = get_nt_change(ref_nt, alt_nt)

            # cast to variant object
            variant = MykrobeVariant(
                variant_type=var_type,
                gene_symbol=gene,
                position=position,
                ref_nt=ref_nt,
                alt_nt=alt_nt,
                ref_aa=ref_aa if len(ref_aa) == 1 and len(alt_aa) == 1 else None,
                alt_aa=alt_aa if len(ref_aa) == 1 and len(alt_aa) == 1 else None,
                depth=int(ref_depth) + int(alt_depth),
                frequency=int(alt_depth) / (int(ref_depth) + int(alt_depth)),
                passed_qc=True,
                confidence=int(conf),
                change=aa_change,
                element_type=ElementType.AMR,
                method=element_type["genotype_model"],
                phenotype=phenotype,
            )
            results.append(variant)
    return results


def parse_mykrobe_amr_pred(
    prediction: Dict[str, Any], resistance_category
) -> ElementTypeResult | None:
    """Parse mykrobe resistance prediction results."""
    LOG.info("Parsing mykrobe prediction")
    resistance = ElementTypeResult(
        phenotypes=_get_mykrobe_amr_sr_profie(prediction),
        genes=[],
        mutations=_parse_mykrobe_amr_variants(prediction),
    )

    # verify prediction result
    if is_prediction_result_empty(resistance):
        result = None
    else:
        result = MethodIndex(
            type=resistance_category, software=Software.MYKROBE, result=resistance
        )
    return result
