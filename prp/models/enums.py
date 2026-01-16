"""Analysis specific data models."""

from enum import StrEnum


class AnalysisSoftware(StrEnum):
    """Single source of truth for analysis software names."""

    AMRFINDER = "amrfinder"
    BRACKEN = "bracken"
    EMMTYPER = "emmtyper"
    GAMBIT = "gambit"
    HAMRONIZATION = "hAMRonization"
    KLEBORATE = "kleborate"
    MYKROBE = "mykrobe"
    NANOPLOT = "nanoplot"
    POSTALIGNQC = "postalignqc"
    QUAST = "quast"
    RESFINDER = "resfinder"
    SAMTOOLS = "samtools"
    SCCMECTYPER = "sccmectyper"
    SEROTYPEFINDER = "serotypefinder"
    SHIGAPASS = "shigapass"
    SPATYPER = "spatyper"
    TBPROFILER = "tbprofiler"
    VIRULENCEFINDER = "virulencefinder"


class AnalysisType(StrEnum):
    """The various types of analysis a parser can produce."""

    ABST = "abst"
    AMR = "amr"
    CBST = "cbst"
    CGMLST = "cgmlst"
    COVERAGE = "coverage"
    EMM = "emm"
    EMMTYPE = "emmtype"
    H_TYPE = "h_type"
    K_TYPE = "K_type"
    LINEAGE = "lineage"
    MLST = "mlst"
    O_TYPE = "o_type"
    QC = "qc"
    RMST = "rmst"
    SCCMEC = "sccmec"
    SCCMECTYPE = "sccmectype"
    SHIGATYPE = "shigatype"
    SMST = "smst"
    SPATYPE = "spatype"
    SPECIES = "species"
    STRESS = "stress"
    STX = "stx"
    TYPING = "typing"
    VARIANT = "variant"
    VIRULENCE = "virulence"
    YBST = "ybst"


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
