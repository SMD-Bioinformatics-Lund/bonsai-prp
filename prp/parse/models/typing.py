"""Chewbacca specific models."""

from enum import StrEnum

from pydantic import BaseModel

from prp.models.base import RWModel


class ChewbbacaErrors(StrEnum):
    """Chewbbaca error codes."""

    PLOT5 = "PLOT5"
    PLOT3 = "PLOT3"
    LOTSC = "LOTSC"
    NIPH = "NIPH"
    NIPHEM = "NIPHEM"
    ALM = "ALM"
    ASM = "ASM"
    LNF = "LNF"
    EXC = "EXC"
    PAMA = "PAMA"


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


class ResultLineageBase(RWModel):
    """Lineage results"""

    lineage_depth: float | None = None
    main_lineage: str
    sublineage: str
