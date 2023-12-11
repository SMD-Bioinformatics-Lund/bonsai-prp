"""Parse resfinder results."""
import logging
from itertools import chain
from typing import Any, Dict, List, Tuple

from ...models.metadata import SoupVersions
from ...models.phenotype import (
    ElementAmrSubtype,
    ElementStressSubtype,
    ElementType,
    ElementTypeResult,
)
from ...models.phenotype import PredictionSoftware as Software
from ...models.phenotype import ResistanceGene, ResistanceVariant, VariantType
from ...models.sample import MethodIndex
from .utils import _default_resistance

LOG = logging.getLogger(__name__)

STRESS_FACTORS = {
    ElementStressSubtype.BIOCIDE: [
        "formaldehyde",
        "benzylkonium chloride",
        "ethidium bromide",
        "chlorhexidine",
        "cetylpyridinium chloride",
        "hydrogen peroxide",
    ],
    ElementStressSubtype.HEAT: ["temperature"],
}


def _assign_res_subtype(
    prediction: Dict[str, Any], element_type: ElementType
) -> ElementStressSubtype | None:
    """Assign element subtype from resfindere prediction."""
    assigned_subtype = None
    if element_type == ElementType.STRESS:
        for sub_type, phenotypes in STRESS_FACTORS.items():
            # get intersection of subtype phenotypes and predicted phenos
            intersect = set(phenotypes) & set(prediction["phenotypes"])
            if len(intersect) > 0:
                assigned_subtype = sub_type
    elif element_type == ElementType.AMR:
        assigned_subtype = ElementAmrSubtype.AMR
    else:
        LOG.warning("Dont know how to assign subtype for %s", element_type)
    return assigned_subtype


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
) -> List[ResistanceGene]:
    """Get resistance genes from resfinder result."""
    results = []
    if not "seq_regions" in resfinder_result:
        return _default_resistance().genes

    for info in resfinder_result["seq_regions"].values():
        # Get only acquired resistance genes
        if not info["ref_database"][0].startswith("Res"):
            continue

        # Get only genes of desired phenotype
        if limit_to_phenotypes is not None:
            intersect = set(info["phenotypes"]) & set(limit_to_phenotypes)
            if len(intersect) == 0:
                continue

        # get element type by peeking at first phenotype
        pheno = info["phenotypes"][0]
        res_category = resfinder_result["phenotypes"][pheno]["category"].upper()
        category = ElementType(res_category)

        # store results
        gene = ResistanceGene(
            gene_symbol=info["name"],
            accession=info["ref_acc"],
            depth=info["depth"],
            identity=info["identity"],
            coverage=info["coverage"],
            ref_start_pos=info["ref_start_pos"],
            ref_end_pos=info["ref_end_pos"],
            ref_gene_length=info["ref_seq_length"],
            alignment_length=info["alignment_length"],
            phenotypes=info["phenotypes"],
            ref_database=info["ref_database"][0],
            ref_id=info["ref_id"],
            element_type=category,
            element_subtype=_assign_res_subtype(info, category),
        )
        results.append(gene)
    return results


def get_nt_change(ref_codon: str, alt_codon: str) -> Tuple[str, str]:
    """Get nucleotide change from codons

    Ref: TCG, Alt: TTG => Tuple[C, T]

    :param ref_codon: Reference codeon
    :type ref_codon: str
    :param str: Alternatve codon
    :type str: str
    :return: Returns nucleotide changed from the reference.
    :rtype: Tuple[str, str]
    """    
    ref_nt = ""
    alt_nt = ""
    for ref, alt in zip(ref_codon, alt_codon):
        if not ref == alt:
            ref_nt += ref
            alt_nt += alt
    return ref_nt.upper(), alt_nt.upper()


def format_nt_change(ref: str, alt: str, var_type: VariantType, start_pos: int, end_pos: int = None, ) -> str:
    """Format nucleotide change

    :param ref: Reference sequence
    :type ref: str
    :param alt: Alternate sequence
    :type alt: str
    :param pos: Position
    :type pos: int
    :param var_type: Type of change
    :type var_type: VariantType
    :return: Formatted nucleotide
    :rtype: str
    """
    fmt_change = ""
    match var_type:
        case VariantType.SUBSTITUTION:
            f"g.{start_pos}{ref}>{alt}"
        case VariantType.DELETION:
            f"g.{start_pos}_{end_pos}del"
        case VariantType.INSERTION:
            f"g.{start_pos}_{end_pos}ins{alt}"
    return fmt_change


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
            var_type = VariantType.SUBSTITUTION
        elif info["insertion"]:
            var_type = VariantType.INSERTION
        elif info["deletion"]:
            var_type = VariantType.DELETION
        else:
            raise ValueError("Output has no known mutation type")
        if not "seq_regions" in info:
            # igenes = _default_resistance().genes
            igenes = [""]
        
        # get gene symbol and accession nr
        gene_symbol, _, gene_accnr = info['seq_regions'][0].split(';;')

        ref_nt, alt_nt = get_nt_change(info["ref_codon"], info["var_codon"])
        nt_change = format_nt_change(ref=ref_nt, alt=alt_nt, start_pos=info['ref_start_pos'], end_pos=info['ref_end_pos'], var_type=var_type)
        variant = ResistanceVariant(
            variant_type=var_type,
            gene_symbol=gene_symbol,
            close_seq_name=gene_accnr,
            genes=igenes,
            phenotypes=info["phenotypes"],
            position=info["ref_start_pos"],
            ref_nt=ref_nt,
            alt_nt=alt_nt,
            ref_aa=info['ref_aa'],
            alt_aa=info['var_aa'],
            nucleotide_change=nt_change,
            protein_change=info['seq_var'],
            depth=info["depth"],
            ref_database=info["ref_database"],
            ref_id=info["ref_id"],
        )
        results.append(variant)
    return results


def parse_resfinder_amr_pred(
    prediction: Dict[str, Any], resistance_category: ElementType
) -> Tuple[SoupVersions, ElementTypeResult]:
    """Parse resfinder resistance prediction results."""
    # resfinder missclassifies resistance the param amr_category by setting all to amr
    LOG.info("Parsing resistance prediction")
    # parse resistance based on the category
    stress_factors = list(chain(*STRESS_FACTORS.values()))
    categories = {
        ElementType.STRESS: stress_factors,
        ElementType.AMR: list(set(prediction["phenotypes"]) - set(stress_factors)),
    }
    # parse resistance
    sr_profile = _get_resfinder_amr_sr_profie(
        prediction, categories[resistance_category]
    )
    res_genes = _parse_resfinder_amr_genes(prediction, categories[resistance_category])
    res_mut = _parse_resfinder_amr_variants(prediction, categories[resistance_category])
    resistance = ElementTypeResult(
        phenotypes=sr_profile, genes=res_genes, mutations=res_mut
    )
    return MethodIndex(
        type=resistance_category, software=Software.RESFINDER, result=resistance
    )
