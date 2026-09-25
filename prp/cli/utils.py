"""Shared utility and click input types."""

from typing import Any

import click

from prp.io.manifest import read_manifest
from prp.models.manifest import SampleManifest


class SampleManifestFile(click.ParamType):
    """CLI option for sample files."""

    name = "config"

    def convert(self, value: str, param: Any, ctx: Any) -> SampleManifest:
        """Convert string path to yaml object."""
        return read_manifest(value)
