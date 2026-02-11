"""Analysis specific data models."""

from enum import StrEnum

from prp.models.enums import AnalysisSoftware, AnalysisType

class ResultStatus(StrEnum):
    """
    PARSED - Assay exists and was parsed
    SKIPPED - Assay exists but user didnt request it
    EMPTY - Assay exists but contains no findings
    ABSENT - Assay doesnt exist in the input
    """

    PARSED = "parsed"
    SKIPPED = "skipped"
    EMPTY = "empty"
    ABSENT = "absent"
    ERROR = "error"


class SequenceStrand(StrEnum):
    """Definition of DNA strand."""

    FORWARD = "+"
    REVERSE = "-"


class VariantType(StrEnum):
    """Types of variants."""

    SNV = "SNV"
    MNV = "MNV"
    SV = "SV"
    INDEL = "INDEL"
    STR = "STR"


class VariantSubType(StrEnum):
    """Variant subtypes."""

    INSERTION = "INS"
    DELETION = "DEL"
    SUBSTITUTION = "SUB"
    TRANSISTION = "TS"
    TRANSVERTION = "TV"
    INVERSION = "INV"
    DUPLICATION = "DUP"
    TRANSLOCATION = "BND"
    FRAME_SHIFT = "FS"


class ElementType(StrEnum):
    """Categories of resistance and virulence genes."""

    AMR = "AMR"
    STRESS = "STRESS"
    VIR = "VIRULENCE"
    ANTIGEN = "ANTIGEN"


class ElementStressSubtype(StrEnum):
    """Categories of resistance and virulence genes."""

    ACID = "ACID"
    BIOCIDE = "BIOCIDE"
    METAL = "METAL"
    HEAT = "HEAT"


class ElementAmrSubtype(StrEnum):
    """Categories of resistance genes."""

    AMR = "AMR"
    POINT = "POINT"


class ElementVirulenceSubtype(StrEnum):
    """Categories of resistance and virulence genes."""

    VIR = "VIRULENCE"
    ANTIGEN = "ANTIGEN"
    TOXIN = "TOXIN"


class AnnotationType(StrEnum):
    """Valid annotation types."""

    TOOL = "tool"
    USER = "user"


class ElementSerotypeSubtype(StrEnum):
    """Categories of serotype genes."""

    ANTIGEN = "ANTIGEN"


class TaxLevel(StrEnum):
    """Braken phylogenetic level."""

    P = "phylum"
    C = "class"
    O = "order"
    F = "family"
    G = "genus"
    S = "species"


class GambitQcFlag(StrEnum):
    """Qc thresholds for Gambit."""

    GREEN = "green"
    AMBER = "amber"
    RED = "red"


class MetadataTypes(StrEnum):
    STR = "string"
    INT = "integer"
    FLOAT = "float"


class SoupType(StrEnum):
    """Type of software of unkown provenance."""

    DB = "database"
    SW = "software"


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
