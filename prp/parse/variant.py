"""Parse variant from VCF files."""

from cyvcf2 import VCF, Variant
from prp.models.phenotype import VariantBase
import logging

LOG = logging.getLogger(__name__)


def parse_variant(variant: Variant):
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

    var_obj = VariantBase(
            variant_type=variant.var_type.upper(),
            variant_subtype=variant.var_subtype.upper(),
            gene_symbol=variant.CHROM,
            start=variant.start,
            end=variant.end,
            ref_nt=variant.REF,
            alt_nt=variant.ALT[0], # haploid
            method=variant.INFO.get("SVMETHOD"),
            confidence=variant.QUAL,
            passed_qc=passed_qc,
    )
    return var_obj


def load_variants(variant_file):
    """Load variants."""
    vcf_obj = VCF(variant_file)
    try:
        next(vcf_obj)
    except StopIteration as error:
        LOG.warning("Variant file %s does not include any variants", variant_file)
        return None
    # re-read the variant file
    vcf_obj = VCF(variant_file)

    # parse header from vcf file
    for variant_no, variant in enumerate(vcf_obj):
        parse_variant(variant)