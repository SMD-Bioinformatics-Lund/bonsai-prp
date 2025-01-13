"""Sample configuration with paths to output files."""

from pathlib import Path
from typing import List

from pydantic import Field, FilePath

from .base import RWModel


class IgvAnnotation(RWModel):
    """Format of a IGV annotation track."""

    name: str
    type: str
    uri: str
    index_uri: str | None = None


class SampleConfig(RWModel):
    """Sample information with metadata and results files."""

    # Sample information
    sample_id: str = Field(..., alias="sampleId", min_length=3, max_length=100)
    sample_name: str
    lims_id: str

    # Bonsai paramters
    groups: List[str] = []

    # Reference genome
    ref_genome_sequence: Path
    ref_genome_annotation: Path

    igv_annotations: List[IgvAnnotation] = []

    # Jasen result files
    nextflow_run_info: FilePath
    process_metadata: List[FilePath] = []  # stores versions of tools and databases
    software_info: List[FilePath] = []  # store sw and db version info

    ## Classification
    kraken: FilePath

    ## QC
    quast: FilePath
    postalnqc: FilePath | None = None

    ## typing
    pymlst: FilePath | None = None
    chewbbaca: FilePath | None = None
    serotypefinder: FilePath | None = None
    shigapass: FilePath | None = None
    emmtyper: FilePath | None = None

    ## resistance, virulence etc
    amrfinder: FilePath | None = None
    resfinder: FilePath | None = None
    virulencefinder: FilePath | None = None
    mykrobe: FilePath | None = None
    tbprofiler: FilePath | None = None

    ## clustering
    sourmash_signature: FilePath | None = None
    ska_index: str | None = None

    def assinged_to_group(self) -> bool:
        """Return True if sample is assigned to a group."""
        return len(self.groups) > 0
