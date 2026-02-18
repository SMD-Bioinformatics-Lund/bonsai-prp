"""Test functions for parsing metadata."""

from datetime import datetime
from pathlib import Path

import yaml

from prp.models.manifest import SampleManifest
from prp.pipeline.metadata import parse_date_from_run_id, process_custom_metadata


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


def test_process_custom_metadata(saureus_sample_conf_path: str):
    """Test that custom metadata fields are handled properly."""

    # TODO migrate to new manifest format and then fix test.
    # cnf_path = Path(saureus_sample_conf_path)
    # with cnf_path.open(encoding="utf-8") as cfile:
    #     data = yaml.safe_load(cfile)

    # # cast metadata records as expcected data type
    # cnf = SampleManifest.model_validate(data, context=saureus_sample_conf_path)
    # # run process function
    # proc_meta = process_custom_metadata(cnf.metadata)

    # # TEST that three records was returned
    # assert len(proc_meta) == 3

    # # TEST that TableMetadataEntry contains a stringed csv
    # assert isinstance(proc_meta[-1].value, str)
