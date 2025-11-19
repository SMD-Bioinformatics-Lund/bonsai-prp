"""Typing related data models"""

from enum import StrEnum
from typing import Any, Protocol, Union, Annotated

from pydantic import Field

from .base import MethodIndexBase, RWModel
from .phenotype import SerotypeGene, VirulenceGene


class TypingSoftware(StrEnum):
    """Container for software names."""

    CHEWBBACA = "chewbbaca"
    EMMTYPER = "emmtyper"
    KLEBORATE = "kleborate"
    MLST = "mlst"
    MYKROBE = "mykrobe"
    SCCMEC = "sccmec"
    SEROTYPEFINDER = "serotypefinder"
    SHIGAPASS = "shigapass"
    SPATYPER = "spatyper"
    TBPROFILER = "tbprofiler"
    VIRULENCEFINDER = "virulencefinder"


class TypingMethod(StrEnum):
    """Valid typing methods."""

    ABST = "abst"
    CBST = "cbst"
    CGMLST = "cgmlst"
    EMMTYPE = "emmtype"
    HTYPE = "H_type"
    KTYPE = "K_type"
    LINEAGE = "lineage"
    MLST = "mlst"
    OTYPE = "O_type"
    RMST = "rmst"
    SCCMECTYPE = "sccmectype"
    SHIGATYPE = "shigatype"
    SMST = "smst"
    SPATYPE = "spatype"
    STX = "stx"
    YBST = "ymst"


class ChewbbacaErrors(StrEnum):
    """Chewbbaca error codes."""

    ALM = "ALM"
    ASM = "ASM"
    EXC = "EXC"
    LNF = "LNF"
    LOTSC = "LOTSC"
    NIPH = "NIPH"
    NIPHEM = "NIPHEM"
    PAMA = "PAMA"
    PLOT3 = "PLOT3"
    PLOT5 = "PLOT5"


class MlstErrors(StrEnum):
    """MLST error codes."""

    NOVEL = "novel"
    PARTIAL = "partial"


class ResultMlstBase(RWModel):
    """Base class for storing MLST-like typing results"""

    alleles: dict[str, Union[int, str, list, None]]


class TypingResultMlst(ResultMlstBase):
    """MLST results"""

    scheme: str
    sequence_type: int | str | None = Field(None, alias="sequenceType")


class TypingResultCgMlst(ResultMlstBase):
    """cgMLST results"""

    n_novel: int = Field(0, alias="nNovel")
    n_missing: int = Field(0, alias="nMissing")


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


class TypingResultEmm(RWModel):
    """Container for emmtype gene information"""

    cluster_count: int
    emmtype: str | None = None
    emm_like_alleles: list[str] | None = None
    emm_cluster: str | None = None


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


class TypingResultGeneAllele(VirulenceGene, SerotypeGene):
    """Identification of individual gene alleles."""


CgmlstAlleles = dict[str, int | None | ChewbbacaErrors | MlstErrors | list[int]]


class TypingResultSpatyper(RWModel):
    """Spatyper results"""

    sequence_name: str | None
    repeats: str | None
    type: str | None



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


class LineageMixin(RWModel):
    """Adds a lineage field to existing model"""

    lineage: str | None


class TypingMethodContract(Protocol):
    type: str


class EmmTypingIndex(MethodIndexBase[TypingResultEmm]):
    software = TypingSoftware.EMMTYPER
    type = TypingMethod.EMMTYPE


class SccmecTypingIndex(MethodIndexBase[TypingResultSccmec]):
    software = TypingSoftware.SCCMEC
    type = TypingMethod.SCCMECTYPE


class ShigaTypingIndex(MethodIndexBase[TypingResultShiga]):
    type = TypingMethod.SHIGATYPE
    software = TypingSoftware.SHIGAPASS


class MlstTypingIndex(MethodIndexBase[TypingResultMlst]):
    software = TypingSoftware.MLST
    type = TypingMethod.MLST


class CgMlstTypingIndex(MethodIndexBase[TypingResultCgMlst]):
    software = TypingSoftware.CHEWBBACA
    type = TypingMethod.CGMLST


class SpatyperTypingIndex(MethodIndexBase[TypingResultSpatyper])):
    software = TypingSoftware.SPATYPER
    type = TypingMethod.SPATYPE


class TbProfilerLineageTypingIndex(MethodIndexBase[TbProfilerLineage]):
    software = TypingSoftware.TbProfiler
    type = TypingMethod.Lineage


TypingMethodIndex = Annotated[
    CgMlstTypingIndex
    | EmmTypingIndex
    | MlstTypingIndex
    | SccmecTypingIndex
    | ShigaTypingIndex
    | SpatyperTypingIndex
    | TbProfilerLineageTypingIndex,
    Field(desciminator="type"),
]
