"""Common errors"""

from typing import Any


class ParserError(Exception):

    def __init__(self, message: str, *, context: dict[str, Any] | None = None):
        super().__init__(message)
        self.context = context or {}


class InvalidDataFormat(ParserError):
    ...

class UnsupportedMethod(ParserError):
    ...

class SchemaMismatchError(ParserError):
    ...

class VersionUnsupportedError(ParserError):
    ...