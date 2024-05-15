"""Parse Mykrobe results."""
import logging
import re
from typing import Any, Dict, Tuple

from ...models.phenotype import (
    AnnotationType,
    ElementType,
    ElementTypeResult,
    MykrobeVariant,
    PhenotypeInfo,
)
from ...models.phenotype import PredictionSoftware as Software
from ...models.phenotype import VariantSubType, VariantType
from ...models.sample import MethodIndex
from ..utils import get_nt_change, is_prediction_result_empty

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
        elif element_type["susceptibility"].upper() == "S":
            susceptible.add(element_type["drug"])
        else:
            # skip rows if no resistance predictions were identified
            continue
    return {"susceptible": list(susceptible), "resistant": list(resistant)}


def get_mutation_type(var_nom: str) -> Tuple[VariantSubType, str, str, int]:
    """Extract mutation type from Mykrobe mutation description.

    GCG7569GTG -> mutation type, ref_nt, alt_nt, pos

    :param var_nom: Mykrobe mutation description
    :type var_nom: str
    :return: Return variant type, ref_codon, alt_codont and position
    :rtype: Tuple[VariantSubType, str, str, int]
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
        var_type = VariantType.SV
        var_sub_type = VariantSubType.DELETION
    elif len(ref_codon) < len(alt_codon):
        var_type = VariantType.SV
        var_sub_type = VariantSubType.INSERTION
    else:
        var_type = VariantType.SNV
        var_sub_type = VariantSubType.SUBSTITUTION
    return var_type, var_sub_type, ref_codon, alt_codon, position


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
        phenotype = [
            PhenotypeInfo(
                name=element_type["drug"],
                type=ElementType.AMR,
                annotation_type=AnnotationType.TOOL,
                annotation_author=Software.MYKROBE.value,
            )
        ]

        variants = element_type["variants"].split(";")
        # Mykrobe CSV variant format
        # <gene>_<aa change>-<nt change>:<ref depth>:<alt depth>:<gt confidence>
        # ref: https://github.com/Mykrobe-tools/mykrobe/wiki/AMR-prediction-output
        pattern = re.compile(r"(.+)_(.+)-(.+):(\d+):(\d+):(\d+)", re.I)
        for var_id, variant in enumerate(variants, start=1):
            # extract variant info using regex
            match = re.search(pattern, variant)
            gene, aa_change, dna_change, ref_depth, alt_depth, conf = match.groups()

            # get type of variant
            var_type, var_sub_type, ref_aa, alt_aa, _ = get_mutation_type(aa_change)

            # reduce codon to nt change for substitutions
            _, _, ref_nt, alt_nt, position = get_mutation_type(dna_change)
            if var_sub_type == VariantSubType.SUBSTITUTION:
                ref_nt, alt_nt = get_nt_change(ref_nt, alt_nt)

            # cast to variant object
            variant = MykrobeVariant(
                # classification
                id=var_id,
                variant_type=var_type,
                variant_subtype=var_sub_type,
                phenotypes=phenotype,
                # location
                reference_sequence=gene,
                start=position,
                end=position + len(alt_nt),
                ref_nt=ref_nt,
                alt_nt=alt_nt,
                ref_aa=ref_aa if len(ref_aa) == 1 and len(alt_aa) == 1 else None,
                alt_aa=alt_aa if len(ref_aa) == 1 and len(alt_aa) == 1 else None,
                # variant info
                method=element_type["genotype_model"],
                depth=int(ref_depth) + int(alt_depth),
                frequency=int(alt_depth) / (int(ref_depth) + int(alt_depth)),
                confidence=int(conf),
                passed_qc=True,
            )
            results.append(variant)
    # sort variants
    variants = sorted(
        results, key=lambda entry: (entry.reference_sequence, entry.start)
    )
    return variants


def parse_mykrobe_amr_pred(
    prediction: Dict[str, Any], resistance_category
) -> ElementTypeResult | None:
    """Parse mykrobe resistance prediction results."""
    LOG.info("Parsing mykrobe prediction")
    resistance = ElementTypeResult(
        phenotypes=_get_mykrobe_amr_sr_profie(prediction),
        genes=[],
        variants=_parse_mykrobe_amr_variants(prediction),
    )

    # verify prediction result
    if is_prediction_result_empty(resistance):
        result = None
    else:
        result = MethodIndex(
            type=resistance_category, software=Software.MYKROBE, result=resistance
        )
    return result
