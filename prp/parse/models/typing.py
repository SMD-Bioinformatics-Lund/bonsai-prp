"""Chewbacca specific models."""

from typing import Any

from pydantic import BaseModel

from prp.models.base import RWModel


class ResultMlstBase(BaseModel):
    """Base class for storing MLST-like typing results"""

    alleles: dict[str, int | str | list | None]


class TypingResultMlst(ResultMlstBase):
    """MLST results"""

    scheme: str
    sequence_type: int | str | None = None


class TypingResultCgMlst(ResultMlstBase):
    """MLST results"""

    n_novel: int = 0
    n_missing: int = 0


class TypingResultEmm(BaseModel):
    """Container for emmtype gene information"""

    cluster_count: int
    emmtype: str | None = None
    emm_like_alleles: list[str] | None = None
    emm_cluster: str | None = None


class LineageMixin(BaseModel):
    """Adds a lineage field to existing model"""

    lineage: str | None


class LineageInformation(RWModel):
    """Base class for storing lineage information typing results"""

    lineage: str | None
    family: str | None
    rd: str | None
    fraction: float | None
    support: list[dict[str, Any]] | None = None


class ResultLineageBase(RWModel):
    """Lineage results"""

    lineage_depth: float | None = None
    main_lineage: str
    sublineage: str


class TypingResultSccmec(RWModel):
    """Sccmec results"""

    type: str | None = None
    subtype: str | None = None
    mecA: str | None = None
    targets: list[str] | None = None
    regions: list[str] | None = None
    target_schema: str
    target_schema_version: str
    region_schema: str
    region_schema_version: str
    camlhmp_version: str
    coverage: list[float] | None = None
    hits: list[int] | None = None
    target_comment: str | None = None
    region_comment: str | None = None
    comment: str | None = None


class TypingResultSpatyper(RWModel):
    """Spatyper results"""

    sequence_name: str | None
    repeats: str | None
    type: str | None


class TypingResultShiga(RWModel):
    """Container for shigatype gene information"""

    rfb: str | None = None
    rfb_hits: float | None = None
    mlst: str | None = None
    flic: str | None = None
    crispr: str | None = None
    ipah: str
    predicted_serotype: str
    predicted_flex_serotype: str | None = None
    comments: str | None = None
