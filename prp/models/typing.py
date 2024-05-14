"""Typing related data models"""

from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import Field

from .base import RWModel
from .phenotype import SerotypeGene, VirulenceGene


class TypingSoftware(Enum):
    """Container for software names."""

    CHEWBBACA = "chewbbaca"
    MLST = "mlst"
    TBPROFILER = "tbprofiler"
    MYKROBE = "mykrobe"
    VIRULENCEFINDER = "virulencefinder"
    SEROTYPEFINDER = "serotypefinder"


class TypingMethod(Enum):
    """Valid typing methods."""

    MLST = "mlst"
    CGMLST = "cgmlst"
    LINEAGE = "lineage"
    STX = "stx"
    OTYPE = "O_type"
    HTYPE = "H_type"


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


class MlstErrors(str, Enum):
    """MLST error codes."""

    NOVEL = "novel"
    PARTIAL = "partial"


class LineageInformation(RWModel):
    """Base class for storing lineage information typing results"""

    lin: str | None = None
    family: str | None = None
    spoligotype: str | None = None
    rd: str | None = None
    fraction: float | None = None
    variant: str | None = None
    coverage: Dict[str, Any] | None = None


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

    lineage_depth: float | None = None
    main_lin: str
    sublin: str


class TypingResultPhylogenetics(TypingResultLineage):
    """Phylogenetics results"""

    phylo_group_depth: float | None = None
    phylo_group: str | None = None
    species_depth: float | None = None
    species: str | None = None


class TypingResultGeneAllele(VirulenceGene, SerotypeGene):
    """Identification of individual gene alleles."""


CgmlstAlleles = Dict[str, int | None | ChewbbacaErrors | MlstErrors | List[int]]
