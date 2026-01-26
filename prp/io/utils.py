"""Helper functions for file I/O operations."""


import io
import os
from typing import IO
from pathlib import Path

from prp.io.types import StreamOrPath


def ensure_text_stream(
    source: StreamOrPath,
    *,
    encoding: str = "utf-8",
    newline: str = "",
) -> IO[str]:
    """
    Normalize input to a text stream (IO[str]) using given encoding & newline policy.

    Accepts:
      - path-like (str/Path)
      - raw bytes/bytearray
      - text stream (IO[str]) -> returned as-is
      - binary stream (IO[bytes]) -> wrapped in TextIOWrapper
      - duck-typed .read() objects (best-effort)
    """
    # Path-like
    if isinstance(source, (str, Path)):
        # open with newline="" for CSV correctness across platforms
        return open(os.fspath(source), "r", encoding=encoding, newline=newline)

    # Already a text stream
    if isinstance(source, io.TextIOBase):
        return source

    # Raw bytes -> wrap into BytesIO -> TextIOWrapper
    if isinstance(source, (bytes, bytearray)):
        return io.TextIOWrapper(io.BytesIO(source), encoding=encoding, newline=newline)

    # Binary streams
    if isinstance(source, (io.BufferedIOBase, io.RawIOBase)):
        return io.TextIOWrapper(source, encoding=encoding, newline=newline)

    # Duck-typed file-like
    read = getattr(source, "read", None)
    if callable(read):
        # Try safe zero-byte read to detect binary vs text
        try:
            sample = source.read(0)  # may be '' or b''; must not advance position
        except Exception:
            # If we can't probe, assume text-like
            return source  # type: ignore[return-value]

        if isinstance(sample, (bytes, bytearray)):
            return io.TextIOWrapper(source, encoding=encoding, newline=newline)  # type: ignore[arg-type]
        return source  # type: ignore[return-value]

    raise TypeError(f"Unsupported StreamOrPath type: {type(source)!r}")
