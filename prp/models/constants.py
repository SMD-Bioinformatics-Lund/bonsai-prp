"""Shared Enums."""

from enum import StrEnum


class PredictionSoftware(StrEnum):
    """Container for prediciton software names."""

    AMRFINDER = "amrfinder"
    RESFINDER = "resfinder"
    VIRFINDER = "virulencefinder"
    SEROTYPEFINDER = "serotypefinder"
    MYKROBE = "mykrobe"
    TBPROFILER = "tbprofiler"
    KLEBORATE = "kleborate"


class ElementType(StrEnum):
    """Categories of resistance and virulence genes."""

    AMR = "AMR"
    STRESS = "STRESS"
    VIR = "VIRULENCE"
    ANTIGEN = "ANTIGEN"
