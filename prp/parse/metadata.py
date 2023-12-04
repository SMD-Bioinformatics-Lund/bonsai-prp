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


def parse_run_metadata(run_meta: TextIO, process_meta: List[TextIO]) -> RunMetadata:
    """Parse metadata for the analysis

    :param run_meta: Nextflow analysis metadata in json format.
    :type run_meta: TextIO
    :param process_meta: Records of the databases used in the analysis.
    :type process_meta: TextIO
    :return: Analysis metadata record.
    :rtype: RunMetadata
    """
    LOG.info("Parse run metadata.")
    run_info = RunInformation(**json.load(run_meta))
    db_info = get_database_info(process_meta)
    return RunMetadata(run=run_info, databases=db_info)