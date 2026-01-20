"""QC data models."""

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field

from .base import RWModel
from .kleborate import KleborateQcResult


class ValidQualityStr(StrEnum):
    """Valid strings for qc entries."""

    LOWCONTIGQUAL = "-"


class QcSoftware(StrEnum):
    """Valid tools."""

    CHEWBBACA = "chewbbaca"
    FASTQC = "fastqc"
    GAMBITCORE = "gambitcore"
    KLEBORATE = "kleborate"
    NANOPLOT = "nanoplot"
    POSTALIGNQC = "postalignqc"
    QUAST = "quast"
    SAMTOOLS = "samtools"


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

    ins_size: float | None = None
    ins_size_dev: float | None = None
    mean_cov: float
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


class GambitQcFlag(StrEnum):
    """Qc thresholds for Gambit."""

    GREEN = "green"
    AMBER = "amber"
    RED = "red"


class GambitcoreQcResult(BaseModel):
    """Gambitcore genome completeness QC metrics."""

    scientific_name: str
    completeness: float
    assembly_core: int
    species_core: int
    closest_accession: str | None = None
    closest_distance: float | None = None
    assembly_kmers: int | None = None
    species_kmers_mean: int | None = None
    species_kmers_std_dev: int | None = None
    assembly_qc: GambitQcFlag | None = None


class NanoPlotSummary(BaseModel):
    """Summary of NanoPlot results."""

    mean_read_length: float
    mean_read_quality: float
    median_read_length: float
    median_read_quality: float
    n_reads: float
    read_length_n50: float
    stdev_read_length: float
    total_bases: float


class NanoPlotQcCutoff(BaseModel):
    """Percentage of reads above quality cutoffs."""

    q10: float
    q15: float
    q20: float
    q25: float
    q30: float


class NanoPlotQcResult(BaseModel):
    """Nanopore sequencing QC metrics from NanoPlot."""

    summary: NanoPlotSummary
    qc_cutoff: NanoPlotQcCutoff
    top_quality: list[float] = Field(default_factory=list)
    top_longest: list[int] = Field(default_factory=list)


class ContigCoverage(BaseModel):
    """Coverage information for a single contig."""

    contig_name: str
    start_pos: int
    end_pos: int
    n_reads: int
    cov_bases: int
    coverage: float
    mean_depth: float
    mean_base_quality: float
    mean_map_quality: float


class SamtoolsCoverageQcResult(BaseModel):
    """SAMtools coverage QC result model."""

    contigs: list[ContigCoverage]


class QcMethodIndex(RWModel):
    """QC results container.

    Based on Mongo db Attribute pattern.
    Reference: https://www.mongodb.com/developer/products/mongodb/attribute-pattern/
    """

    software: QcSoftware
    version: str | None = None
    result: QuastQcResult | PostAlignQcResult | GenomeCompleteness | GambitcoreQcResult | NanoPlotQcResult | SamtoolsCoverageQcResult | KleborateQcResult


class KleborateQcIndex(RWModel):
    """Indexing of Kleborate data."""

    software: Literal[QcSoftware.KLEBORATE] = QcSoftware.KLEBORATE
    version: str
    result: KleborateQcResult


class CdmQcMethodIndex(QcMethodIndex):
    """Qc results container for CDM"""

    id: str
