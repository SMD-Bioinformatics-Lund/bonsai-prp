"""Sample configuration with paths to output files."""

from pathlib import Path
from typing import List

from pydantic import Field, ValidationInfo
from pydantic.functional_validators import BeforeValidator
from typing_extensions import Annotated

from .base import RWModel


class IgvAnnotation(RWModel):
    """Format of a IGV annotation track."""

    name: str
    type: str
    uri: str
    index_uri: str | None = None


def convert_rel_to_abs_path(path: str, validation_info: ValidationInfo) -> Path:
    """Validate that file exist and resolve realtive directories.

    if a path is relative, convert to absolute from the configs parent directory
    i.e.  prp_path = ./results/sample_name.json --> /path/to/sample_name.json
          given, cnf_path = /data/samples/cnf.yml
    relative paths are used when bootstraping a test database
    """
    # convert relative path to absolute
    path = (
        Path(path)
        if Path(path).is_absolute()
        else validation_info.data["config_path"].parent / path
    )

    assert path.is_file(), f"Invalid path: {path}"
    return path


FilePath = Annotated[Path, BeforeValidator(convert_rel_to_abs_path)]


class SampleConfig(RWModel):
    """Sample information with metadata and results files."""

    # File info
    config_path: Path

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
    # nextflow_run_info: FilePath
    nextflow_run_info: FilePath
    process_metadata: List[FilePath] = []  # stores versions of tools and databases
    software_info: List[FilePath] = []  # store sw and db version info

    ## Classification
    kraken: FilePath | None = None

    ## QC
    quast: FilePath
    postalnqc: FilePath | None = None

    ## typing
    pymlst: FilePath | None = None
    chewbbaca: FilePath | None = None
    serotypefinder: FilePath | None = None
    shigapass: FilePath | None = None
    emmtyper: FilePath | None = None
    spatyper: FilePath | None = None

    ## resistance, virulence etc
    amrfinder: FilePath | None = None
    resfinder: FilePath | None = None
    virulencefinder: FilePath | None = None
    mykrobe: FilePath | None = None
    tbprofiler: FilePath | None = None

    ## clustering
    sourmash_signature: str | None = None
    ska_index: str | None = None

    def assinged_to_group(self) -> bool:
        """Return True if sample is assigned to a group."""
        return len(self.groups) > 0
