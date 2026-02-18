"""Read json files."""

import io
import json
from pathlib import Path
from typing import Any, Mapping

from prp.exceptions import DataFormatError

from .types import StreamOrPath


def read_json(source: StreamOrPath, *, encoding: str = "utf-8") -> Any:
    """
    Read JSON from a path, string path, or file-like object (text or bytes).

    Returns decoded Python object (dict/list/...).
    """
    # Path-like
    if isinstance(source, (str, Path)):
        with open(source, "r", encoding=encoding) as fh:
            return json.load(fh)

    # File-like (text)
    if isinstance(source, io.TextIOBase):
        return json.load(source)

    # File-like (bytes)
    if isinstance(source, (io.BufferedIOBase, io.RawIOBase)) or hasattr(source, "read"):
        data = source.read()
        # data may be bytes or str depending on stream type
        if isinstance(data, bytes):
            data = data.decode(encoding, errors="replace")
        return json.loads(data)

    raise TypeError(f"Unsupported StreamOrPath type: {type(source)!r}")


def require_mapping(obj: Any, *, what: str) -> Mapping[str, Any]:
    if not isinstance(obj, dict):
        raise DataFormatError(
            f"Expected object '{what}' to be a JSON object/dict, got {type(obj)!r}"
        )
    return obj
