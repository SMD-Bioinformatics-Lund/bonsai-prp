"""Sample manifest info."""

from pydantic import AnyUrl, BaseModel, Field, FilePath, ValidationError
from pathlib import Path
from .base import AllowExtraModelMixin
from .metadata import MetaEntry


class FlexibleURI(str):
    """Accepts local file paths, http(s) URLs, and s3:// URIs."""

    @classmethod
    def __get_pydantic_validator__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, value):
        """Validate URI"""
        # Check for local file path
        try:
            p = Path(value)
            if p.exists() or p.is_absolute():
                return value
        except Exception:
            pass

        # Check if it's http/https URL
        try:
            AnyUrl.validate(value)
            return value
        except ValidationError:
            pass

        # Check for AWS S3 scheme
        if value.startswith("s3://"):
            return value

        raise ValueError(f"Invalid URI or path: {value}")



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
    ref_genome_sequence: FilePath | None = None
    ref_genome_annotation: FilePath | None = None

    igv_annotations: list[IgvAnnotation] = Field(default_factory=list)

    nextflow_run_info: FilePath

    analysis_result: list[AnalysisResult] = Field(
        default_factory=list,
        description="Analysis results produced by the pipeline",
    )

    def assigned_to_group(self) -> bool:
        """Return True if sample is assigned to a group."""
        return len(self.groups) > 0
