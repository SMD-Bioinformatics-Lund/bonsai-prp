"""Convert from internal data to the input required by the API."""

from bonsai_libs.api_client.bonsai.models import (
    InputMetaEntry,
    InputTableMetadata,
    DatetimeMetadataEntry,
    GenericMetadataEntry,
    InputSampleInfo,
    SequencingInfo,
    SequencingPlatforms,
)
from pydantic import TypeAdapter

from prp.pipeline.types import ParsedSampleResults

input_meta_adapter = TypeAdapter(InputMetaEntry)


def convert_metadata_entry(meta) -> InputMetaEntry:
    """
    Convert one PRP metadata entry into a Bonsai InputMetaEntry variant.
    """
    t = meta.data_type  # your internal type tag

    # 1. Handle table metadata
    if t == "table":
        return None
        return InputTableMetadata(
            fieldname=meta.fieldname,
            value=meta.value,               # probably a filename / serialized table?
            category=meta.category or "general",
        )

    # 2. Handle datetime metadata
    if t == "datetime":
        return DatetimeMetadataEntry(
            fieldname=meta.fieldname,
            value=meta.value,               # must be actual datetime
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


def sample_to_bonsai(sample_info: ParsedSampleResults) -> InputSampleInfo:
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
    bonsai_meta =  []
    for meta in sample_info.metadata:
        fmt_meta = convert_metadata_entry(meta)
        if fmt_meta is not None:
            bonsai_meta.append(fmt_meta)

    return InputSampleInfo(
        sample_id=sample_info.sample_id,
        sample_name=sample_info.sample_name,
        lims_id=sample_info.lims_id,
        groups=sample_info.groups,
        sequencing=sequencing,
        metadata=bonsai_meta,
    )
