"""Metadata models."""

from datetime import datetime
from enum import StrEnum
from typing import Literal, Optional

from pydantic import BaseModel, FilePath

from .base import RWModel


class MetadataTypes(StrEnum):

    STR = "string"
    INT ="integer"
    FLOAT = "float"


class GenericMetadataEntry(BaseModel):
    """Container of basic metadata information"""

    fieldname: str
    value: str | int | float
    type: MetadataTypes


class DatetimeMetadataEntry(BaseModel):
    """Container of basic metadata information"""

    fieldname: str
    value: datetime
    type: Literal["datetime"]


class TableMetadataEntry(BaseModel):
    """Container of basic metadata information"""

    fieldname: str
    value: FilePath
    type: Literal["table"]


class SoupType(StrEnum):
    """Type of software of unkown provenance."""

    DB = "database"
    SW = "software"


class SoupVersion(BaseModel):
    """Version of Software of Unknown Provenance."""

    name: str
    version: str
    type: SoupType


class SequencingInfo(RWModel):
    """Information on the sample was sequenced."""

    run_id: str
    platform: str
    instrument: Optional[str]
    method: dict[str, str] = {}
    date: datetime | None


class PipelineInfo(RWModel):
    """Information on the sample was analysed."""

    pipeline: str
    version: str
    commit: str
    analysis_profile: list[str]
    assay: str
    release_life_cycle: str
    configuration_files: list[str]
    workflow_name: str
    command: str
    softwares: list[SoupVersion]
    date: datetime
