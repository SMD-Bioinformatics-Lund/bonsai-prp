"""Sample manifest info."""

from pydantic import BaseModel, Field, FilePath
from .base import AllowExtraModelMixin
from .metadata import MetaEntry


class IgvAnnotation(BaseModel):
    """Format of a IGV annotation track."""

    name: str
    type: str
    uri: str | None = None
    index_uri: str | None = None


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

    def assinged_to_group(self) -> bool:
        """Return True if sample is assigned to a group."""
        return len(self.groups) > 0
