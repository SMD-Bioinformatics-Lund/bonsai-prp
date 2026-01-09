"""Analysis specific data models."""

from enum import StrEnum

class AnalysisType(StrEnum):
    """The various types of analysis a parser can produce."""
    AMR = "amr"
    VIRULENCE = "virulence"
    STRESS = "stress"
    TYPING = "typing"
    SPECIES = "species"
    QC = "qc"
    VARIANT = "variant"
    COVERAGE = "coverage"