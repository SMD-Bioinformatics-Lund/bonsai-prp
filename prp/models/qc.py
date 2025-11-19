"""QC data models."""

from enum import StrEnum
from typing_extensions import Literal

from pydantic import BaseModel, Field

from .base import MethodIndexBase


class QcSoftware(StrEnum):
    """Valid tools."""

    QUAST = "quast"
    FASTQC = "fastqc"
    POSTALIGNQC = "postalignqc"
    CHEWBBACA = "chewbbaca"
    GAMBITCORE = "gambitcore"
    NANOPLOT = "nanoplot"
    KLEBORATE = "kleborate"
    SAMTOOLS = "samtools"


class ValidQualityStr(StrEnum):
    """Valid strings for qc entries."""

    LOWCONTIGQUAL = "-"


class QuastQcResult(BaseModel):
    """Assembly QC metrics."""

    total_length: int
    reference_length: int | None = None
    largest_contig: int
    n_contigs: int
    n50: int
    ng50: int | ValidQualityStr | None = None
    assembly_gc: float
    reference_gc: float | None = None
    duplication_ratio: float | None = None


class PostAlignQcResult(BaseModel):
    """Alignment QC metrics."""

    ins_size: int | None = None
    ins_size_dev: int | None = None
    mean_cov: int
    pct_above_x: dict[str, float]
    n_reads: int
    n_mapped_reads: int
    n_read_pairs: int
    coverage_uniformity: float | None = None
    quartile1: float
    median_cov: float
    quartile3: float


class GenomeCompleteness(BaseModel):
    """cgMLST QC metric."""

    n_missing: int = Field(..., description="Number of missing cgMLST alleles")


class GambitcoreQcResult(BaseModel):
    """Gambitcore genome completeness QC metrics."""

    scientific_name: str
    completeness: float | None = None
    assembly_core: str | None = None
    closest_accession: str | None = None
    closest_distance: float | None = None
    assembly_kmers: int | None = None
    species_kmers_mean: int | None = None
    species_kmers_std_dev: int | None = None
    assembly_qc: str | None = None


class NanoPlotQcResult(BaseModel):
    """Nanopore sequencing QC metrics from NanoPlot."""

    mean_read_length: float
    mean_read_quality: float
    median_read_length: float
    median_read_quality: float
    number_of_reads: float
    read_length_n50: float
    stdev_read_length: float
    total_bases: float


class ContigCoverage(BaseModel):
    """Coverage information for a single contig."""

    rname: str
    startpos: int
    endpos: int
    numreads: int
    covbases: int
    coverage: float
    meandepth: float
    meanbaseq: float
    meanmapq: float


class SamtoolsCoverageQcResult(BaseModel):
    """SAMtools coverage QC result model."""

    contigs: list[ContigCoverage]


class CdmQcMethodIndex(MethodIndexBase):
    """Qc results container for CDM"""

    id: str


class QuastIndex(MethodIndexBase[QuastQcResult]):
    software: Literal[QcSoftware.QUAST] = QcSoftware.QUAST


class PostAlignQcMethodIndex(MethodIndexBase[PostAlignQcResult]):
    software: Literal[QcSoftware.POSTALIGNQC] = QcSoftware.POSTALIGNQC


class GenomeCompletenessIndex(MethodIndexBase[GenomeCompleteness]):
    software: str = "GENOMECOMPLETENESS"


class GambitIndex(MethodIndexBase[GambitcoreQcResult]):
    software: Literal[QcSoftware.GAMBITCORE] = QcSoftware.GAMBITCORE


class NanoPlotIndex(MethodIndexBase[NanoPlotQcResult]):
    software: Literal[QcSoftware.NANOPLOT] = QcSoftware.NANOPLOT


class SamtoolsCoverageIndex(MethodIndexBase[SamtoolsCoverageQcResult]):
    software: Literal[QcSoftware.SAMTOOLS] = QcSoftware.SAMTOOLS
