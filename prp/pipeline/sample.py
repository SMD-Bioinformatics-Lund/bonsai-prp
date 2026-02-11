"""Parse for input config using parsers from this module."""

from datetime import datetime
import logging
from typing import Any

from prp.models.manifest import SampleManifest
from prp.models.metadata import MetaEntry, TableMetadataEntry
from prp.parse import run_parser
from prp.io.json import read_json
from prp.io.delimited import read_delimited
from .types import GenericMetadataRecord, InternalMetadataRecord, ParsedSampleResults, PipelineRun, PipelineInfo, PipelineDefinition, PipelineRunConfig, PipelineArtifact, SequencingInfo, AnalysisResult, TabularMetadataRecord


LOG = logging.getLogger(__name__)


def to_internal_run_info(*, run_info: dict[str, Any], analysis_results: list[dict[str, Any]]) -> PipelineRun:
    """Parse the run information dump from JASEN."""
    artifacts = [
        PipelineArtifact(
            software_name=a.software,
            software_version=a.software_version,
            uri=a.uri
        ) for a in analysis_results]

    # structure the data into its internal representation
    pipeline_def = PipelineDefinition(
        name=run_info.get('pipeline'),
        version=run_info.get('version') or run_info.get('commit'),
        commit=None if ((c := run_info.get("commit")) == "null") else c,
        release_life_cycle=run_info.get('release_life_cycle', 'unknown'),
    )
    run_cnf = PipelineRunConfig(
        command=run_info.get('command'),
        analysis_profile=run_info.get('analysis_profile'),
        configuration_files=run_info.get('configuration_files', []),
    )
    return PipelineRun(
        pipeline_run_id=run_info.get('workflow_name'),
        assay=run_info.get('assay'),
        executed_at=run_info.get('date'),
        pipeline_info=PipelineInfo(
            definition=pipeline_def,
            run_config=run_cnf,
            artifacts=artifacts,
        )
    )


def parse_date_from_run_id(run_id: str) -> datetime | None:
    """
    Get the date of sequencing from run id as datetime object.

    XXX_20240112 -> 2024-01-12
    """
    err_msg = "Unrecognized format of run_id, sequence time cant be determined"
    if "_" not in run_id:
        LOG.warning(err_msg)
        return None
    # parse date string
    try:
        seq_date = datetime.strptime(run_id.split("_")[0], r"%y%m%d")
    except ValueError:
        LOG.warning(err_msg)
        seq_date = None
    return seq_date


def to_internal_sequencing_info(run_info: dict[str, Any]) -> SequencingInfo:
    """Format sequencing info from pipeline metadata."""
    run_id = run_info.get('sequencing_run')
    return SequencingInfo(
        sequencing_run_id=run_id or 'unknown',
        platform=run_info.get('sequencing_run'),
        sequencing_method=run_info.get('sequencing_type'),
        sequenced_at=parse_date_from_run_id(run_id)
    )


def to_table_record(record: TableMetadataEntry) -> TabularMetadataRecord:
    """Format manifest table record as internal representation."""

    if not isinstance(record, TableMetadataEntry):
        raise ValueError("Function expects TableMetadataEntry got {type(record)}")

    suffix = record.value.suffix
    if not record.value.suffix in ['.csv', '.tsv']:
        raise ValueError(f"Dont know how to parse {suffix}")
    delimiter = ',' if suffix == '.csv' else '\t'

    # read file
    reader = read_delimited(record.value, delimiter=delimiter)
    first_row = next(reader)
    cols = list(first_row)
    cells = [list(first_row.values())]

    # continue building the table
    for row in reader:
        cells.append(list(row.values()))
    return TabularMetadataRecord(
        fieldname=record.fieldname,
        columns=cols,
        cells=cells,
        category=record.category
    )


def to_generic_metadata_record(record: MetaEntry) -> GenericMetadataRecord:
    """Format metadata file as ."""
    return GenericMetadataRecord(
        fieldname=record.fieldname,
        value=record.value,
        category=record.category,
        data_type=record.type
    )


def parse_results_from_manifest(manifest: SampleManifest) -> ParsedSampleResults:
    """Parse pipeline analysis results from a manifest file."""

    metadata: list[InternalMetadataRecord] = []
    for record in manifest.metadata:
        if record.type == 'table':
            metadata.append(to_table_record(record))
        else:
            metadata.append(to_generic_metadata_record(record))

    raw_run_info = read_json(manifest.nextflow_run_info)
    # parse results from analysis softwares
    analysis_results: list[AnalysisResult] = []
    for res in manifest.analysis_result:
        if not res.uri.scheme == 'file':
            raise NotImplementedError(f"No method for reading {res.uri.scheme} URI scheme.")
        ev = run_parser(software=res.software, version=res.software_version, data=res.uri.path)
        for at, parser_result in ev.results.items():
            analysis_results.append(
                AnalysisResult(
                    software=ev.software,
                    software_version=ev.software_version,
                    parser_name=ev.parser_name,
                    parser_version=ev.parser_version,
                    parser_status=parser_result.status,
                    reason=parser_result.reason,
                    analysis_type=at,
                    results=parser_result.value,
                )
            )

    return ParsedSampleResults(
        sample_id=manifest.sample_id,
        sample_name=manifest.sample_name,
        lims_id=manifest.lims_id,
        metadata=metadata,
        pipeline=to_internal_run_info(run_info=raw_run_info, analysis_results=manifest.analysis_result),
        sequencing=to_internal_sequencing_info(run_info=raw_run_info),
        analysis_results=analysis_results,
    )
