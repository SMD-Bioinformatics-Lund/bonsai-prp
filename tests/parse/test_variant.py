"""Test parse variants."""
from prp.parse.variant import load_variants

def test_parse_variants(mtuberculosis_sv_path):
    load_variants(mtuberculosis_sv_path)