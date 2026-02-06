"""Sample manifest info."""

from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse
from pydantic import BaseModel, Field, ValidationInfo
from pydantic_core import core_schema
from pathlib import Path

from .base import AllowExtraModelMixin, RelOrAbsPath
from .metadata import MetaEntry


@dataclass
class URI:
    scheme: str
    path: str
    netloc: str = ""


class FlexibleURI:
    """
    Accepts:
    - relative or absolute local paths → file://
    - file:// URIs
    - http(s)://
    - s3://
    Returns: URI(scheme, netloc, path)
    """

    @classmethod
    def validate(cls, value: Any, info: ValidationInfo):
        # Normalize Path → string
        if isinstance(value, Path):
            value = str(value)

        # --- handle local filesystem paths ---
        if isinstance(value, str):
            p = Path(value)

            # resolve relative to context, if given
            if not p.is_absolute() and info.context:
                base = Path(info.context.parent)
                p = (base / p).resolve()

            if p.exists():
                pr = urlparse(f"file://{p.as_posix()}")
                return URI(pr.scheme, pr.path, pr.netloc)

        # --- parse as URL (including s3://, file://, http://, https://, etc.) ---
        pr = urlparse(value)
        if pr.scheme:
            return URI(pr.scheme, pr.path, pr.netloc)

        raise ValueError(f"Invalid URI or path: {value}")

    @classmethod
    def __get_pydantic_core_schema__(cls, _source, _handler):
        return core_schema.with_info_plain_validator_function(cls.validate)

class IgvAnnotation(BaseModel):
    """Format of a IGV annotation track."""

    name: str
    type: str
    uri: str | None = None
    index_uri: str | None = None


class AnalysisResult(BaseModel):
    """Describe how a analysis result was derived."""

    software: str
    software_version: str
    database: str | None = None
    uri: FlexibleURI


class SampleManifest(AllowExtraModelMixin):
    """Sample information with metadata and results files."""

    # Sample information
    sample_id: str = Field(..., min_length=3, max_length=100)
    sample_name: str
    lims_id: str

    # Bonsai paramters
    groups: list[str] = Field(default_factory=list)
    metadata: list[MetaEntry] = Field(default_factory=list)

    # Reference genome
    ref_genome_sequence: RelOrAbsPath | None = None
    ref_genome_annotation: RelOrAbsPath | None = None

    igv_annotations: list[IgvAnnotation] = Field(default_factory=list)

    nextflow_run_info: RelOrAbsPath

    analysis_result: list[AnalysisResult] = Field(
        default_factory=list,
        description="Analysis results produced by the pipeline",
    )

    def assigned_to_group(self) -> bool:
        """Return True if sample is assigned to a group."""
        return len(self.groups) > 0
