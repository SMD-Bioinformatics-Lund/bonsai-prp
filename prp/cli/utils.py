"""Shared utility and click input types."""

from typing import Any, TextIO

import click

from prp import VERSION as __version__
from prp.io.manifest import read_manifest
from prp.io.json import read_json
from prp.models.manifest import SampleManifest

OptionalFile = TextIO | None


class SampleManifestFile(click.ParamType):
    """CLI option for sample files."""

    name = "config"

    def convert(self, value: str, param: Any, ctx: Any) -> SampleManifest:
        """Convert string path to yaml object."""
        return read_manifest(value)


class JsonFile(click.ParamType):
    """CLI option for json files."""

    name = "config"

    def convert(self, value: str, param: Any, ctx: Any) -> dict[str, Any]:
        """Convert string path to yaml object."""
        return read_json(value)
