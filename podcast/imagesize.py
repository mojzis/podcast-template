"""Width and height of a PNG or JPEG, from its header (no imaging library)."""

from __future__ import annotations

import struct
from pathlib import Path

_PNG = b"\x89PNG\r\n\x1a\n"
_JPEG_SOF = {
    0xC0,
    0xC1,
    0xC2,
    0xC3,
    0xC5,
    0xC6,
    0xC7,
    0xC9,
    0xCA,
    0xCB,
    0xCD,
    0xCE,
    0xCF,
}


def image_size(path: Path) -> tuple[int, int] | None:
    """``(width, height)``, or ``None`` when the file is not a PNG or JPEG."""
    data = path.read_bytes()
    if data.startswith(_PNG) and len(data) >= 24:  # noqa: PLR2004 -- end of IHDR size
        width, height = struct.unpack(">II", data[16:24])
        return width, height
    if data.startswith(b"\xff\xd8"):
        return _jpeg_size(data)
    return None


def _jpeg_size(data: bytes) -> tuple[int, int] | None:
    i = 2
    while i + 9 <= len(data):
        if data[i] != 0xFF:  # noqa: PLR2004 -- marker prefix
            return None
        marker = data[i + 1]
        length = struct.unpack(">H", data[i + 2 : i + 4])[0]
        if marker in _JPEG_SOF:
            height, width = struct.unpack(">HH", data[i + 5 : i + 9])
            return width, height
        i += 2 + length
    return None
