"""Parse Mykrobe results."""

import logging
import re
from typing import Any, Union

from ...models.phenotype import (
    AMRMethodIndex,
    AnnotationType,
    ElementType,
    ElementTypeResult,
    MykrobeVariant,
    PhenotypeInfo,
)
from ...models.phenotype import PredictionSoftware as Software
from ...models.phenotype import VariantSubType, VariantType
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


def get_mutation_type(var_nom: str) -> tuple[str, Union[VariantSubType, str, int]]:
    """Extract mutation type from Mykrobe mutation description.

    GCG7569GTG -> mutation type, ref_nt, alt_nt, pos

    :param var_nom: Mykrobe mutation description
    :type var_nom: str
    :return: Return variant type, ref_nt, alt_ntt and position
    :rtype: dict[str, Union[VariantSubType, str, int]]
    """
    mut_type = None
    ref_nt = None
    alt_nt = None
    position = None
    try:
        ref_idx = re.search(r"\d", var_nom, 1).start()
        alt_idx = re.search(r"\d(?=[^\d]*$)", var_nom).start() + 1
    except AttributeError:
        return mut_type, ref_nt, alt_nt, position

    ref_nt = var_nom[:ref_idx]
    alt_nt = var_nom[alt_idx:]
    position = int(var_nom[ref_idx:alt_idx])
    var_len = abs(len(ref_nt) - len(alt_nt))
    if var_len >= 50:
        var_type = VariantType.SV
    elif 1 < var_len < 50:
        var_type = VariantType.INDEL
    else:
        var_type = VariantType.SNV
    if len(ref_nt) > len(alt_nt):
        var_sub_type = VariantSubType.DELETION
    elif len(ref_nt) < len(alt_nt):
        var_sub_type = VariantSubType.INSERTION
    else:
        var_sub_type = VariantSubType.SUBSTITUTION
    return {
        "type": var_type,
        "subtype": var_sub_type,
        "ref": ref_nt,
        "alt": alt_nt,
        "pos": position,
    }


def _parse_mykrobe_amr_variants(mykrobe_result) -> tuple[MykrobeVariant, ...]:
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
        pattern = re.compile(
            r"(?P<gene>.+)_(?P<aa_change>.+)-(?P<dna_change>.+)"
            r":(?P<ref_depth>\d+):(?P<alt_depth>\d+):(?P<conf>\d+)",
            re.I,
        )
        for var_id, variant in enumerate(variants, start=1):
            # extract variant info using regex
            match_obj = re.search(pattern, variant).groupdict()

            # get type of variant
            var_aa = get_mutation_type(match_obj["aa_change"])
            # var_type, var_sub_type, ref_aa, alt_aa, _ = get_mutation_type(aa_change)

            # reduce codon to nt change for substitutions
            var_dna = get_mutation_type(match_obj["dna_change"])
            ref_nt, alt_nt = (var_dna["ref"], var_dna["alt"])
            if var_aa["subtype"] == VariantSubType.SUBSTITUTION:
                ref_nt, alt_nt = get_nt_change(ref_nt, alt_nt)

            # cast to variant object
            has_aa_change = all([len(var_aa["ref"]) == 1, len(var_aa["alt"]) == 1])
            variant = MykrobeVariant(
                # classification
                id=var_id,
                variant_type=var_aa["type"],
                variant_subtype=var_aa["subtype"],
                phenotypes=phenotype,
                # location
                reference_sequence=match_obj["gene"],
                start=var_dna["pos"],
                end=var_dna["pos"] + len(alt_nt),
                ref_nt=ref_nt,
                alt_nt=alt_nt,
                ref_aa=var_aa["ref"] if has_aa_change else None,
                alt_aa=var_aa["alt"] if has_aa_change else None,
                # variant info
                method=element_type["genotype_model"],
                depth=int(match_obj["ref_depth"]) + int(match_obj["alt_depth"]),
                frequency=int(match_obj["alt_depth"])
                / (int(match_obj["ref_depth"]) + int(match_obj["alt_depth"])),
                confidence=int(match_obj["conf"]),
                passed_qc=True,
            )
            results.append(variant)
    # sort variants
    variants = sorted(
        results, key=lambda entry: (entry.reference_sequence, entry.start)
    )
    return variants


def parse_mykrobe_amr_pred(prediction: dict[str, Any]) -> AMRMethodIndex | None:
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
        result = AMRMethodIndex(
            type=ElementType.AMR, software=Software.MYKROBE, result=resistance
        )
    return result
