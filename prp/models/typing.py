"""Typing related data models"""

from enum import Enum
from typing import Any, Literal, Optional, Union

from pydantic import Field

from .base import RWModel
from .phenotype import SerotypeGene, VirulenceGene, ShigatypeGene, EmmtypeGene


class TypingSoftware(str, Enum):
    """Container for software names."""

    CHEWBBACA = "chewbbaca"
    MLST = "mlst"
    TBPROFILER = "tbprofiler"
    MYKROBE = "mykrobe"
    VIRULENCEFINDER = "virulencefinder"
    SEROTYPEFINDER = "serotypefinder"
    SHIGAPASS = "shigapass"
    EMMTYPER = "emmtyper"


class TypingMethod(str, Enum):
    """Valid typing methods."""

    MLST = "mlst"
    CGMLST = "cgmlst"
    LINEAGE = "lineage"
    STX = "stx"
    OTYPE = "O_type"
    HTYPE = "H_type"
    SHIGATYPE = "shigatype"
    EMMTYPE = "emmtype"


class ChewbbacaErrors(str, Enum):
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


class MlstErrors(str, Enum):
    """MLST error codes."""

    NOVEL = "novel"
    PARTIAL = "partial"


class ResultMlstBase(RWModel):
    """Base class for storing MLST-like typing results"""

    alleles: dict[str, Union[int, str, list, None]]


class TypingResultMlst(ResultMlstBase):
    """MLST results"""

    scheme: str
    sequence_type: Optional[int] = Field(None, alias="sequenceType")


class TypingResultCgMlst(ResultMlstBase):
    """MLST results"""

    n_novel: int = Field(0, alias="nNovel")
    n_missing: int = Field(0, alias="nNovel")


class ResultLineageBase(RWModel):
    """Lineage results"""

    lineage_depth: float | None = None
    main_lineage: str
    sublineage: str


class LineageInformation(RWModel):
    """Base class for storing lineage information typing results"""

    lineage: str | None
    family: str | None
    rd: str | None
    fraction: float | None
    support: list[dict[str, Any]] | None = None


class TbProfilerLineage(ResultLineageBase):
    """Base class for storing MLST-like typing results"""

    lineages: list[LineageInformation]


class TypingResultGeneAllele(VirulenceGene, SerotypeGene, ShigatypeGene, EmmtypeGene):
    """Identification of individual gene alleles."""


CgmlstAlleles = dict[str, int | None | ChewbbacaErrors | MlstErrors | list[int]]
