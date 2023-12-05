"""Parse Mykrobe results."""
import logging
import re
from typing import Any, Dict, Tuple

from ...models.metadata import SoupVersions
from ...models.phenotype import ElementTypeResult
from ...models.phenotype import PredictionSoftware as Software
from ...models.phenotype import ResistanceGene, ResistanceVariant
from ...models.sample import MethodIndex
from .utils import _default_resistance, _default_variant

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

    if not mykrobe_result:
        results = _default_resistance().genes
        return results

    for element_type in mykrobe_result:
        if mykrobe_result[element_type]["predict"].upper() == "R":
            hits = mykrobe_result[element_type]["called_by"]
            for hit in hits:
                gene = ResistanceGene(
                    gene_symbol=hit.split("_")[0],
                    accession=None,
                    depth=hits[hit]["info"]["coverage"]["alternate"]["median_depth"],
                    identity=None,
                    coverage=hits[hit]["info"]["coverage"]["alternate"][
                        "percent_coverage"
                    ],
                    ref_start_pos=None,
                    ref_end_pos=None,
                    ref_gene_length=None,
                    alignment_length=None,
                    phenotypes=element_type,
                    ref_database=None,
                    ref_id=None,
                    contig_id=None,
                    sequence_name=None,
                    ass_start_pos=None,
                    ass_end_pos=None,
                    strand=None,
                    element_type=None,
                    element_subtype=None,
                    target_length=None,
                    res_class=None,
                    res_subclass=None,
                    method=None,
                    close_seq_name=None,
                )
                results.append(gene)
    return results


def _parse_mykrobe_amr_variants(mykrobe_result) -> Tuple[ResistanceVariant, ...]:
    """Get resistance genes from mykrobe result."""
    results = []

    def get_mutation_type(var_nom):
        try:
            ref_idx = re.search(r"\d", var_nom, 1).start()
            alt_idx = re.search(r"\d(?=[^\d]*$)", var_nom).start() + 1
        except AttributeError:
            return [None] * 4
        ref = var_nom[:ref_idx]
        alt = var_nom[alt_idx:]
        position = int(var_nom[ref_idx:alt_idx])
        if len(ref) > len(alt):
            mut_type = "deletion"
        elif len(ref) < len(alt):
            mut_type = "insertion"
        else:
            mut_type = "substitution"
        return mut_type, ref, alt, position

    for element_type in mykrobe_result:
        if mykrobe_result[element_type]["predict"].upper() == "R":
            hits = mykrobe_result[element_type]["called_by"]
            for hit in hits:
                if hits[hit]["variant"] is None:
                    var_info = hit.split("-")[1]
                    _, ref_nt, alt_nt, position = get_mutation_type(var_info)
                    var_nom = hit.split("-")[0].split("_")[1]
                    var_type, _, _, _ = get_mutation_type(var_nom)
                    variant = ResistanceVariant(
                        variant_type=var_type,
                        genes=[hit.split("_")[0]],
                        phenotypes=[element_type],
                        position=position,
                        ref_nt=ref_nt,
                        alt_nt=alt_nt,
                        depth=hits[hit]["info"]["coverage"]["alternate"][
                            "median_depth"
                        ],
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
    if not results:
        results = _default_variant().mutations
        return results

    return results


def parse_mykrobe_amr_pred(
    prediction: Dict[str, Any], resistance_category
) -> Tuple[SoupVersions, ElementTypeResult]:
    """Parse mykrobe resistance prediction results."""
    LOG.info("Parsing mykrobe prediction")
    pred = prediction["susceptibility"]
    resistance = ElementTypeResult(
        phenotypes=_get_mykrobe_amr_sr_profie(pred),
        genes=[],  # _parse_mykrobe_amr_genes(pred),
        mutations=_parse_mykrobe_amr_variants(pred),
    )
    return MethodIndex(
        type=resistance_category, software=Software.MYKROBE, result=resistance
    )
