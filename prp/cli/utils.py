"""Shared utility and click input types."""

import json
from pathlib import Path
from typing import Any, TextIO

import click
import yaml

from prp import VERSION as __version__
from prp.models.config import SampleConfig

OptionalFile = TextIO | None


class SampleConfigFile(click.ParamType):
    """CLI option for sample files."""

    name = "config"

    def convert(self, value: str, param: Any, ctx: Any) -> SampleConfig:
        """Convert string path to yaml object."""
        # verify input is path to existing file
        try:
            cnf_path = Path(value)
            if not cnf_path.is_file():
                raise FileNotFoundError(
                    f"file {cnf_path.name} not found, please check the path."
                )
        except TypeError as error:
            raise TypeError(f"value should be a str not '{type(value)}'") from error
        # load yaml and cast to pydantic model
        with cnf_path.open(encoding="utf-8") as cfile:
            data = yaml.safe_load(cfile)
            return SampleConfig.model_validate(data, context=cnf_path)


class JsonFile(click.ParamType):
    """CLI option for json files."""

    name = "config"

    def convert(self, value: str, param: Any, ctx: Any) -> dict[str, Any]:
        """Convert string path to yaml object."""
        # verify input is path to existing file
        try:
            file_path = Path(value)
            if not file_path.is_file():
                raise FileNotFoundError(
                    (f"file {file_path.name} not found, ", "please check the path")
                )
        except TypeError as error:
            raise TypeError(f"value should be a str not '{type(value)}'") from error
        # load yaml and cast to pydantic model
        with file_path.open(encoding="utf-8") as cfile:
            return json.load(cfile)
