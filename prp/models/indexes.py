"""Stores method indexes."""

from typing import Annotated

from pydantic import Field

from .amrfinder import AmrFinderIndex
from .kleborate import KleborateAmrIndex, KleborateQcIndex, KleborateSppIndex, KleborateVirulenceIndex
from .mykrobe import MykrobeSppIndex
from .qc import (
    GambitIndex,
    GenomeCompletenessIndex,
    NanoPlotIndex,
    PostAlignQcMethodIndex,
    QuastIndex,
    SamtoolsCoverageIndex,
)
from .resfinder import ResFinderIndex
from .species import BrackenSppIndex
from .tbprofiler import TbProfilerEtIndex, TbProfilerLineageTypingIndex
from .virulencefinder import VirulenceFinderIndex
from .typing import CgMlstTypingIndex, EmmTypingIndex, MlstTypingIndex, SccmecTypingIndex, ShigaTypingIndex, SpatyperTypingIndex

# class ElementTypeProtocol(Protocol):
#     """Phenotype result data model.

#     A phenotype result is a generic data structure that stores predicted genes,
#     mutations and phenotyp changes.
#     """

#     phenotypes: dict[str, list[str]] = {}
#     genes: list[Union[AmrFinderGene, AmrFinderResistanceGene, ResfinderGene]]
#     variants: list[
#         Union[TbProfilerVariant, MykrobeVariant, ResfinderVariant, AmrFinderVariant]
#     ] = []

QcMethodIndex = Annotated[
    GambitIndex
    | GenomeCompletenessIndex
    | KleborateQcIndex
    | NanoPlotIndex
    | PostAlignQcMethodIndex
    | QuastIndex
    | SamtoolsCoverageIndex,
    Field(discriminator="software"),
]

SppMethodIndex = Annotated[
    BrackenSppIndex | MykrobeSppIndex | KleborateSppIndex,
    Field(discriminator="software"),
]

TraitMethodIndex = Annotated[
    AmrFinderIndex
    | KleborateVirulenceIndex
    | KleborateAmrIndex
    | ResFinderIndex
    | VirulenceFinderIndex
    | TbProfilerEtIndex,
    Field(discriminator="software"),
]

TypingMethodIndex = Annotated[
    CgMlstTypingIndex
    | EmmTypingIndex
    | MlstTypingIndex
    | SccmecTypingIndex
    | ShigaTypingIndex
    | SpatyperTypingIndex
    | TbProfilerLineageTypingIndex,
    Field(discriminator="type"),
]