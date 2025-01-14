"""Test functions for parsing metadata."""

from datetime import datetime

from prp.parse.metadata import parse_date_from_run_id


def test_parse_sequence_date_from_run_id():
    """Test parsing of sequencing run id."""

    # test that a run id from illumina works
    date = parse_date_from_run_id("220214_NB501699_0302_AHJLM7AFX3")
    assert date == datetime(2022, 2, 14)

    # test that an unknown id does not work
    date = parse_date_from_run_id("my-unknown-run-id")
    assert date == None

    # test that an unknown id does not work
    date = parse_date_from_run_id("my_unknown_run_id")
    assert date == None
