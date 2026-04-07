"""Test functions for parsing QC results."""

from prp.parse.qc import parse_postalignqc_results
from prp.models.qc import QcMethodIndex


def test_parse_postalignqc_count_reads_only(streptococcus_postalignqc_path):
    """Test that a count-reads-only postalignqc JSON parses without error."""
    result = parse_postalignqc_results(streptococcus_postalignqc_path)

    assert isinstance(result, QcMethodIndex)
    assert result.result.n_reads == 3014194
    assert result.result.n_read_pairs == 1507097
    assert result.result.mean_cov is None
    assert result.result.pct_above_x is None
    assert result.result.n_mapped_reads is None
