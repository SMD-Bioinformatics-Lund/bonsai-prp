"""Metadata models."""
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from .base import RWModel


class SoupType(Enum):
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
    analysis_profile: str
    configuration_files: list[str]
    workflow_name: str
    command: str
    softwares: list[SoupVersion]
    date: datetime