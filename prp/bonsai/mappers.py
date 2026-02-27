"""Convert from internal data to the input required by the API."""

from pathlib import Path

from bonsai_libs.api_client.bonsai.models import (
    DatetimeMetadataEntry,
    GenericMetadataEntry,
    MetaEntryInput,
    PipelineArtifact,
    PipelineDefinition,
    PipelineInfo,
    PipelineRunConfig,
    PipelineRunInput,
    SampleInfoInput,
    SequencingInfo,
    SequencingPlatforms,
    TableMetadataInput,
    UploadAnalysisResultInput,
)
from pydantic import TypeAdapter

from prp.pipeline.types import MinimalAnalysisRecord, ParsedSampleResults

meta_adapter_input = TypeAdapter(MetaEntryInput)


def convert_metadata_entry(meta) -> MetaEntryInput:
    """
    Convert one PRP metadata entry into a Bonsai MetaEntryInput variant.
    """
    t = meta.data_type  # your internal type tag

    # 1. Handle table metadata
    if t == "table":
        return None
        # TODO reenable this later once the API supports it --- IGNORE ---
        return TableMetadataInput(
            fieldname=meta.fieldname,
            value=meta.value,  # probably a filename / serialized table?
            category=meta.category or "general",
        )

    # 2. Handle datetime metadata
    if t == "datetime":
        return DatetimeMetadataEntry(
            fieldname=meta.fieldname,
            value=meta.value,  # must be actual datetime
            category=meta.category,
        )

    # 3. Handle primitive-type metadata
    if t in ("string", "integer", "float"):
        return GenericMetadataEntry(
            fieldname=meta.fieldname,
            value=meta.value,
            category=meta.category,
            type=t,
        )

    # 4. Unknown metadata type
    raise ValueError(f"Unsupported metadata data_type: {t!r}")


def sample_to_bonsai(sample_info: ParsedSampleResults) -> SampleInfoInput:
    """Create sample info from parsed manifest."""

    # convert platform
    raw_platform = sample_info.sequencing.platform
    platform = SequencingPlatforms(raw_platform) if raw_platform is not None else None
    sequencing = SequencingInfo(
        sequencing_run_id=sample_info.sequencing.sequencing_run_id,
        platform=platform,
        instrument=sample_info.sequencing.instrument,
        sequenced_at=sample_info.sequencing.sequenced_at,
    )

    # add metadata if present
    bonsai_meta = []
    for meta in sample_info.metadata:
        fmt_meta = convert_metadata_entry(meta)
        if fmt_meta is not None:
            bonsai_meta.append(fmt_meta)

    return SampleInfoInput(
        sample_id=sample_info.sample_id,
        sample_name=sample_info.sample_name,
        lims_id=sample_info.lims_id,
        groups=sample_info.groups,
        sequencing=sequencing,
        metadata=bonsai_meta,
    )


def sample_info_to_pipeline_run(sample_info: ParsedSampleResults) -> PipelineRunInput:
    """Extract pipeline run info from parsed manifest for API upload."""

    # Convert from internal representation to API input models
    raw_pipeline_nfo = sample_info.pipeline.pipeline_info
    artifacts = [
        PipelineArtifact(
            software_name=artifact.software_name,
            software_version=artifact.software_version,
            uri=str(artifact.uri),
        )
        for artifact in (raw_pipeline_nfo.artifacts or [])
    ]
    pipeline_def = PipelineDefinition(
        name=raw_pipeline_nfo.definition.name,
        version=raw_pipeline_nfo.definition.version,
        commit=raw_pipeline_nfo.definition.commit,
        release_life_cycle=raw_pipeline_nfo.definition.release_life_cycle,
    )
    run_cnf = PipelineRunConfig(
        command=raw_pipeline_nfo.run_config.command,
        analysis_profile=raw_pipeline_nfo.run_config.analysis_profile,
        configuration_files=raw_pipeline_nfo.run_config.configuration_files,
    )

    return PipelineRunInput(
        pipeline_run_id=sample_info.pipeline.pipeline_run_id,
        executed_at=sample_info.pipeline.executed_at,
        assay=sample_info.pipeline.assay,
        pipeline_info=PipelineInfo(
            run_config=run_cnf,
            definition=pipeline_def,
            artifacts=artifacts,
        ),
    )


def analysis_result_to_upload_payload(
    sample_id: str, *, run_id: str, result: MinimalAnalysisRecord
) -> UploadAnalysisResultInput:
    """Convert from internal analysis result representation to API input model."""
    if not result.uri:
        raise RuntimeError(
            f"Analysis result URI is required for upload, but got empty value for sample {sample_id}, run {run_id}, software {result.software}."
        )

    # assert uri points to file and that it exists
    uri_path = Path(result.uri.path)
    if not result.uri.scheme == "file" or not uri_path.is_file():
        raise ValueError(
            f"Analysis result URI must point to an existing file. Got: {result.uri}"
        )

    return UploadAnalysisResultInput(
        sample_id=sample_id,
        pipeline_run_id=run_id,
        software=result.software,
        software_version=result.software_version,
        file=uri_path,
    )
