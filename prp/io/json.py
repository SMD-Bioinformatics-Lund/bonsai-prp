"""Read json files."""

import io
import json
from typing import Any
from pathlib import Path
from prp.parse.base import ParserInput


def read_json(source: ParserInput, *, encoding: str = "utf-8") -> Any:
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

    raise TypeError(f"Unsupported ParserInput type: {type(source)!r}")
