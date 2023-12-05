"""Metadata models."""
from datetime import datetime
from enum import Enum
from typing import List

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


class RunInformation(RWModel):
    """Store information on a run how the run was conducted."""

    pipeline: str
    version: str
    commit: str
    analysis_profile: str = Field(
        ...,
        alias="analysisProfile",
        description="The analysis profile used when starting the pipeline",
    )
    configuration_files: List[str] = Field(
        ..., alias="configurationFiles", description="Nextflow configuration used"
    )
    workflow_name: str
    sample_name: str
    sequencing_platform: str
    sequencing_type: str
    command: str
    date: datetime


SoupVersions = List[SoupVersion]


class RunMetadata(BaseModel):
    """Run metadata"""

    run: RunInformation
    databases: SoupVersions
