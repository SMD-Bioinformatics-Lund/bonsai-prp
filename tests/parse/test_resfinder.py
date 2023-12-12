"""Test functions for the resfinder parser."""

from prp.parse.phenotype.resfinder import get_nt_change


def test_get_nt_changes_from_condons():
    """Test extraction of changed nucleotides from codons."""

    ref_codon = "tcg"
    alt_codon = "ttg"

    ref_nt, alt_nt = get_nt_change(ref_codon, alt_codon)

    assert ref_nt == 'C' and alt_nt == 'T'