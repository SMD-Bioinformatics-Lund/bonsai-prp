"""Base parser functionality."""

from abc import ABC, abstractmethod
from logging import Logger, getLogger
from typing import Type, IO
from prp.models.base import ParserOutput, AnalysisType

class BaseParser(ABC):
    """Parser class structure."""

    software: str
    parser_name: str
    parser_version: str
    schema_version: str
    produces: set[AnalysisType]


    def __init__(self, *, logger: Logger | None = None):
        self.logger = logger or getLogger(f"bonsai_prp.parse.{self.parser_name}")
    
    def log_info(self, msg: str, **ctx):
        self.logger.info(msg, extra={"context": ctx})
    
    def log_warning(self, msg: str, **ctx):
        self.logger.warning(msg, extra={"context": ctx})

    def log_error(self, msg: str, **ctx):
        self.logger.error(msg, extra={"context": ctx})
    
    @abstractmethod
    def parse(self, *, stream: IO[bytes], want: set[AnalysisType] | None = None) -> ParserOutput:
        ...

ParserClass = Type[BaseParser]
