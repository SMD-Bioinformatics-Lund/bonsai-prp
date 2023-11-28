"""Generic database objects of which several other models are based on."""
from pydantic import BaseConfig, BaseModel


class RWModel(BaseModel):  # pylint: disable=too-few-public-methods
    """Base model for read/ write operations"""

    class Config(BaseConfig):  # pylint: disable=too-few-public-methods
        """Configure base model behaviour."""

        allow_population_by_alias = True
        populate_by_name = True
        use_enum_values = True
