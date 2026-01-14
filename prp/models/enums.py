"""Analysis specific data models."""

from enum import StrEnum


class AnalysisSoftware(StrEnum):
    """Single source of truth for analysis software names."""

    AMRFINDER = "amrfinder"
    BRACKEN = "bracken"
    EMMTYPER = "emmtyper"
    MYKROBE = "mykrobe"
    SCCMECTYPER = "sccmectyper"
    SEROTYPEFINDER = "serotypefinder"


class AnalysisType(StrEnum):
    """The various types of analysis a parser can produce."""
    AMR = "amr"
    VIRULENCE = "virulence"
    STRESS = "stress"
    TYPING = "typing"
    SPECIES = "species"
    QC = "qc"
    VARIANT = "variant"
    LINEAGE = "lineage"
    COVERAGE = "coverage"
    SCCMEC = "sccmec"
    O_TYPE = "o_type"
    H_TYPE = "h_type"