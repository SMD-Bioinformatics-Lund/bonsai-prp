"""Parse metadata passed to pipeline."""
import json
import logging
from typing import List

from Bio import SeqIO

from ..models.metadata import RunInformation, SoupVersion

LOG = logging.getLogger(__name__)


def get_database_info(process_metadata: List[str]) -> List[SoupVersion]:
    """Get database or software information.

    :param process_metadata: List of file objects for db records.
    :type process_metadata: List[str]
    :return: Description of software or database version.
    :rtype: List[SoupVersion]
    """
    db_info = []
    for soup_filepath in process_metadata:
        with open(soup_filepath, "r", encoding="utf-8") as soup:
            dbs = json.load(soup)
            if isinstance(dbs, (list, tuple)):
                for db in dbs:
                    db_info.append(SoupVersion(**db))
            else:
                db_info.append(SoupVersion(**dbs))
    return db_info


def parse_run_info(run_metadata: str) -> RunInformation:
    """Parse nextflow analysis information

    :param run_metadata: Nextflow analysis metadata in json format.
    :type run_metadata: str
    :return: Analysis metadata record.
    :rtype: RunMetadata
    """
    LOG.info("Parse run metadata.")
    with open(run_metadata, encoding="utf-8") as jsonfile:
        run_info = RunInformation(**json.load(jsonfile))
    return run_info


def get_gb_genome_version(fasta_path: str) -> str:
    """Retrieve genbank genome version"""
    record = next(SeqIO.parse(fasta_path, "fasta"))
    return record.id, record.description.rstrip(", complete genome")
