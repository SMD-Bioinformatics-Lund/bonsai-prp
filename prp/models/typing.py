"""Typing related data models"""

from enum import Enum
from typing import Dict, List, Optional, Union

from pydantic import Field

from .base import RWModel


class TypingSoftware(Enum):
    """Container for software names."""

    CHEWBBACA = "chewbbaca"
    MLST = "mlst"
    TBPROFILER = "tbprofiler"
    MYKROBE = "mykrobe"


class TypingMethod(Enum):
    """Valid typing methods."""

    MLST = "mlst"
    CGMLST = "cgmlst"
    LINEAGE = "lineage"


class LineageInformation(RWModel):
    """Base class for storing lineage information typing results"""

    lin: Optional[str]
    family: Optional[str]
    spoligotype: Optional[str]
    rd: Optional[str]
    frac: Optional[str]
    variant: Optional[str]
    coverage: Optional[Dict]


class ResultMlstBase(RWModel):
    """Base class for storing MLST-like typing results"""

    alleles: Dict[str, Union[int, str, List, None]]


class ResultLineageBase(RWModel):
    """Base class for storing MLST-like typing results"""

    lineages: List[LineageInformation]


class TypingResultMlst(ResultMlstBase):
    """MLST results"""

    scheme: str
    sequence_type: Optional[int] = Field(None, alias="sequenceType")


class TypingResultCgMlst(ResultMlstBase):
    """MLST results"""

    n_novel: int = Field(0, alias="nNovel")
    n_missing: int = Field(0, alias="nNovel")


class TypingResultLineage(ResultLineageBase):
    """Lineage results"""

    main_lin: str
    sublin: str
