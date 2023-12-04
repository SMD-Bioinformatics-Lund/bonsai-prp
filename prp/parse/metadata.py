"""Parse metadata passed to pipeline."""
from ..models.metadata import SoupVersion, RunInformation, RunMetadata
from typing import List, TextIO
import json
import logging

LOG = logging.getLogger(__name__)

def get_database_info(process_metadata: List[TextIO]) -> List[SoupVersion]:
    """Get database or software information.

    :param process_metadata: List of file objects for db records.
    :type process_metadata: List[TextIO]
    :return: Description of software or database version.
    :rtype: List[SoupVersion]
    """
    db_info = []
    for soup in process_metadata:
        dbs = json.load(soup)
        if isinstance(dbs, (list, tuple)):
            for db in dbs:
                db_info.append(SoupVersion(**db))
        else:
            db_info.append(SoupVersion(**dbs))
    return db_info


def parse_run_info(run_metadata: TextIO) -> RunInformation:
    """Parse nextflow analysis information

    :param run_metadata: Nextflow analysis metadata in json format.
    :type run_metadata: TextIO
    :return: Analysis metadata record.
    :rtype: RunMetadata
    """
    LOG.info("Parse run metadata.")
    run_info = RunInformation(**json.load(run_metadata))
    return run_info