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
    SHIGAPASS = "shigapass"


class AnalysisType(StrEnum):
    """The various types of analysis a parser can produce."""
    AMR = "amr"
    COVERAGE = "coverage"
    EMM = "emm"
    H_TYPE = "h_type"
    LINEAGE = "lineage"
    O_TYPE = "o_type"
    QC = "qc"
    SCCMEC = "sccmec"
    SHIGATYPE = "shigatype"
    SPECIES = "species"
    STRESS = "stress"
    TYPING = "typing"
    VARIANT = "variant"
    VIRULENCE = "virulence"
