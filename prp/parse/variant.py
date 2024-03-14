"""Parse variant from VCF files."""

import re
import logging
from typing import List
from cyvcf2 import VCF, Variant
from prp.models.phenotype import VariantBase, VariantType

LOG = logging.getLogger(__name__)
SOURCE_PATTERN = r"##source=(.+)\n"


def _get_variant_type(variant) -> VariantType:
    """Parse variant type."""
    match variant.var_type:
        case "snp":
            var_type = VariantType.SNV
        case "mnp":
            var_type = VariantType.MNV
        case other:
            var_type = VariantType(variant.var_type.upper())
    return var_type


def parse_variant(variant: Variant, var_id: int, caller: str | None=None):
    """Parse variant info from VCF row."""
    # get major category
    depth = variant.gt_depths
    frequency = variant.gt_alt_freqs
    confidence = variant.gt_quals
    start = variant.start
    end = variant.end

    # check if variant passed qc filtering
    if len(variant.FILTERS) == 0:
        passed_qc = None
    elif "PASS" in variant.FILTERS:
        passed_qc = True
    else:
        passed_qc = False

    var_type: VariantType = _get_variant_type(variant)

    var_obj = VariantBase(
            id=var_id,
            variant_type=var_type,
            variant_subtype=variant.var_subtype.upper(),
            gene_symbol=variant.CHROM,
            start=variant.start,
            end=variant.end,
            ref_nt=variant.REF,
            alt_nt=variant.ALT[0], # haploid
            method=variant.INFO.get("SVMETHOD", caller),
            confidence=variant.QUAL,
            passed_qc=passed_qc,
    )
    return var_obj


def _get_variant_caller(vcf_obj: VCF) -> str | None:
    """Get source from VCF header to get variant caller sw if possible."""
    match = re.search(SOURCE_PATTERN, vcf_obj.raw_header)
    if match:
        return match.group(1)


def load_variants(variant_file: str) -> List[VariantBase]:
    """Load variants."""
    vcf_obj = VCF(variant_file)
    try:
        next(vcf_obj)
    except StopIteration as error:
        LOG.warning("Variant file %s does not include any variants", variant_file)
        return None
    # re-read the variant file
    vcf_obj = VCF(variant_file)

    variant_caller = _get_variant_caller(vcf_obj)

    # parse header from vcf file
    variants = []
    for var_id, variant in enumerate(vcf_obj, start=1):
        variants.append(parse_variant(variant, var_id=var_id, caller=variant_caller))

    return variants
