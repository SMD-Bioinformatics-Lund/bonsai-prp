"""Parse metadata passed to pipeline."""
import json
import logging
from datetime import datetime

from Bio import SeqIO

from ..models.metadata import PipelineInfo, SequencingInfo, SoupVersion

LOG = logging.getLogger(__name__)


def get_database_info(process_metadata: list[str]) -> list[SoupVersion]:
    """Get database or software information.

    :param process_metadata: list of file objects for db records.
    :type process_metadata: list[str]
    :return: Description of software or database version.
    :rtype: list[SoupVersion]
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


def parse_sequence_date_from_run_id(run_id: str) -> datetime | None:
    err_msg = 'Unrecognized format of run_id, sequence time cant be determined'
    if '_' not in run_id:
        LOG.warning(err_msg)
        return None
    # parse date string
    try:
        seq_date = datetime.strptime(run_id.split('_')[0], r'%y%m%d')
    except ValueError:
        LOG.warning(err_msg)
        seq_date = None
    return seq_date


def parse_run_info(run_metadata: str, process_metadata: list[str]) -> tuple[SequencingInfo, PipelineInfo]:
    """Parse nextflow analysis information.

    :param run_metadata: Nextflow analysis metadata in json format.
    :type run_metadata: str
    :return: Analysis metadata record.
    :rtype: RunMetadata
    """
    LOG.info("Parse run metadata.")
    with open(run_metadata, encoding="utf-8") as jsonfile:
        run_info = json.load(jsonfile)
    # get sample info
    sample_info = {"sample_name": run_info["sample_name"], "lims_id": run_info["lims_id"]}
    # get sequencing info
    seq_info = SequencingInfo(
        run_id=run_info['sequencing_run'],
        platform=run_info['sequencing_platform'],
        instrument=None,
        method={'method': run_info['sequencing_type']},
        date=parse_sequence_date_from_run_id(run_info['sequencing_run'])
    )
    # get pipeline info
    soup_versions = get_database_info(process_metadata)
    pipeline_info = PipelineInfo(
        pipeline=run_info['pipeline'],
        version=run_info['version'],
        commit=run_info['commit'],
        analysis_profile=run_info['analysis_profile'],
        configuration_files=run_info['configuration_files'],
        workflow_name=run_info['commit'],
        command=run_info['command'],
        softwares=soup_versions,
        date=datetime.fromisoformat(run_info['date']),
    )
    return sample_info, seq_info, pipeline_info


def get_gb_genome_version(fasta_path: str) -> str:
    """Retrieve genbank genome version"""
    record = next(SeqIO.parse(fasta_path, "fasta"))
    return record.id, record.description.rstrip(", complete genome")
