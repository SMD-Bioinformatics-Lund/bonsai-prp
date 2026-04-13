"""Read manifest file."""

from pathlib import Path

import yaml

from prp.models.manifest import SampleManifest, BootstrapConfig

from .types import Pathish


def read_manifest(path: Pathish) -> SampleManifest:
    """Read manifest file and return it as manifest object."""
    if not isinstance(path, (str, Path)):
        raise ValueError(f"Input should be either str or Path, got {type(input)}")

    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"file {path.name} not found, please check the path.")

    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
        return SampleManifest.model_validate(data, context=path)


def read_bootstrap_config(path: Pathish) -> BootstrapConfig:
    """Read boostrap configuration."""
    path = Path(path)
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
        return BootstrapConfig.model_validate(data, context=path)