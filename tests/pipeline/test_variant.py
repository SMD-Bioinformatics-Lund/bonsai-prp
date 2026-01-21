"""Test parse variants."""

from prp.pipeline.variant import load_variants


def test_parse_sv_variants(mtuberculosis_sv_vcf_path):
    """Test loading of varians."""

    variants = load_variants(mtuberculosis_sv_vcf_path)
    assert len(variants) == 3


def test_parse_snv_variants(mtuberculosis_snv_vcf_path):
    """Test loading of varians."""

    variants = load_variants(mtuberculosis_snv_vcf_path)
    assert len(variants) == 3
