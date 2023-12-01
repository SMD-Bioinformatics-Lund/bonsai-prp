"""Parse resfinder results."""
import logging
from typing import Any, Dict, Tuple

from ...models.metadata import SoupVersions
from ...models.phenotype import ElementType, ElementTypeResult
from ...models.phenotype import PredictionSoftware as Software
from ...models.phenotype import ResistanceGene, ResistanceVariant
from ...models.sample import MethodIndex
from .utils import _default_resistance

LOG = logging.getLogger(__name__)


def _get_resfinder_amr_sr_profie(resfinder_result, limit_to_phenotypes=None):
    """Get resfinder susceptibility/resistance profile."""
    susceptible = set()
    resistant = set()
    for phenotype in resfinder_result["phenotypes"].values():
        # skip phenotype if its not part of the desired category
        if (
            limit_to_phenotypes is not None
            and phenotype["key"] not in limit_to_phenotypes
        ):
            continue

        if "amr_resistant" in phenotype.keys():
            if phenotype["amr_resistant"]:
                resistant.add(phenotype["amr_resistance"])
            else:
                susceptible.add(phenotype["amr_resistance"])
    return {"susceptible": list(susceptible), "resistant": list(resistant)}


def _parse_resfinder_amr_genes(
    resfinder_result, limit_to_phenotypes=None
) -> Tuple[ResistanceGene, ...]:
    """Get resistance genes from resfinder result."""
    results = []

    if not "seq_regions" in resfinder_result:
        results = _default_resistance().genes
        return results

    for info in resfinder_result["seq_regions"].values():
        # Get only acquired resistance genes
        if not info["ref_database"][0].startswith("Res"):
            continue

        # Get only genes of desired phenotype
        if limit_to_phenotypes is not None:
            intersect = set(info["phenotypes"]) & set(limit_to_phenotypes)
            if len(intersect) == 0:
                continue

        # store results
        gene = ResistanceGene(
            gene_symbol=info["name"],
            accession=info["ref_acc"],
            depth=info["depth"],
            identity=info["identity"],
            coverage=info["coverage"],
            ref_start_pos=info["ref_start_pos"],
            ref_end_pos=info["ref_end_pos"],
            ref_gene_length=info["ref_seq_lenght"],
            alignment_length=info["alignment_length"],
            phenotypes=info["phenotypes"],
            ref_database=info["ref_database"][0],
            ref_id=info["ref_id"],
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


def _parse_resfinder_amr_variants(
    resfinder_result, limit_to_phenotypes=None
) -> Tuple[ResistanceVariant, ...]:
    """Get resistance genes from resfinder result."""
    results = []
    igenes = []
    for info in resfinder_result["seq_variations"].values():
        # Get only variants from desired phenotypes
        if limit_to_phenotypes is not None:
            intersect = set(info["phenotypes"]) & set(limit_to_phenotypes)
            if len(intersect) == 0:
                continue
        # get gene depth
        if "seq_regions" in resfinder_result:
            info["depth"] = resfinder_result["seq_regions"][info["seq_regions"][0]][
                "depth"
            ]
        else:
            info["depth"] = 0
        # translate variation type bools into classifier
        if info["substitution"]:
            var_type = "substitution"
        elif info["insertion"]:
            var_type = "insertion"
        elif info["deletion"]:
            var_type = "deletion"
        else:
            raise ValueError("Output has no known mutation type")
        if not "seq_regions" in info:
            # igenes = _default_resistance().genes
            igenes = [""]
        variant = ResistanceVariant(
            variant_type=var_type,
            genes=igenes,
            phenotypes=info["phenotypes"],
            position=info["ref_start_pos"],
            ref_nt=info["ref_codon"],
            alt_nt=info["var_codon"],
            depth=info["depth"],
            ref_database=info["ref_database"],
            ref_id=info["ref_id"],
        )
        results.append(variant)
    return results


def parse_resfinder_amr_pred(
    prediction: Dict[str, Any], resistance_category
) -> Tuple[SoupVersions, ElementTypeResult]:
    """Parse resfinder resistance prediction results."""
    # resfinder missclassifies resistance the param amr_category by setting all to amr
    LOG.info("Parsing resistance prediction")
    # parse resistance based on the category
    categories = {
        ElementType.BIOCIDE: [
            "formaldehyde",
            "benzylkonium chloride",
            "ethidium bromide",
            "chlorhexidine",
            "cetylpyridinium chloride",
            "hydrogen peroxide",
        ],
        ElementType.HEAT: ["temperature"],
    }
    categories[ElementType.AMR] = list(
        set(prediction["phenotypes"])
        - set(categories[ElementType.BIOCIDE] + categories[ElementType.HEAT])
    )

    # parse resistance
    resistance = ElementTypeResult(
        phenotypes=_get_resfinder_amr_sr_profie(
            prediction, categories[resistance_category]
        ),
        genes=_parse_resfinder_amr_genes(prediction, categories[resistance_category]),
        mutations=_parse_resfinder_amr_variants(
            prediction, categories[resistance_category]
        ),
    )
    return MethodIndex(
        type=resistance_category, software=Software.RESFINDER, result=resistance
    )
