"""Generic database objects of which several other models are based on."""

from pathlib import Path
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, BeforeValidator, ConfigDict, ValidationInfo
from pysam import Callable
from typing_extensions import Annotated


def convert_rel_to_abs_path(path: str, validation_info: ValidationInfo) -> Path:
    """Validate that file exist and resolve realtive directories.

    if a path is relative, convert to absolute from the configs parent directory
    i.e.  prp_path = ./results/sample_name.json --> /path/to/sample_name.json
          given, cnf_path = /data/samples/cnf.yml
    relative paths are used when bootstraping a test database
    """
    # convert relative path to absolute
    upd_path = Path(path)
    if not upd_path.is_absolute():
        # check if config file path is provided as the model context
        if validation_info.context is None:
            raise ValueError("No context defined for model.")
        upd_path = Path(validation_info.context).parent / upd_path

    assert upd_path.is_file(), f"Invalid path: {upd_path}"
    return upd_path


class ParserOutput(BaseModel):
    """Common output data structure for all parsers."""

    target_field: str
    data: Any


ParserFunc = Callable[[Any], ParserOutput]


FilePath = Annotated[Path, BeforeValidator(convert_rel_to_abs_path)]


class RWModel(BaseModel):  # pylint: disable=too-few-public-methods
    """Base model for read/ write operations"""

    model_config = ConfigDict(
        populate_by_name=True,
        use_enum_values=True,
    )


T = TypeVar("T")

class MethodIndexBase(RWModel, Generic[T]):
    """Generic container for typing method results."""
    
    software: str
    type: str
    result: T


class VersionMixin(BaseModel):
    """Add version field to data model."""
    
    version: str