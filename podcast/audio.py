"""Read what the feed needs from an audio file: size in bytes and length."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from mutagen import MutagenError
from mutagen.mp3 import MP3

from podcast.errors import PodcastError


@dataclass(frozen=True)
class Audio:
    """An episode's audio file."""

    path: Path
    size: int  # bytes, for <enclosure length>
    seconds: int  # rounded, for <itunes:duration>


def probe(path: Path) -> Audio:
    """Measure an MP3.

    Raises:
        PodcastError: the file is not a readable MP3.
    """
    try:
        info = MP3(path).info
    except MutagenError as exc:
        raise PodcastError(f"{path.name}: not a readable mp3 ({exc})") from None
    if info is None:
        raise PodcastError(f"{path.name}: no mp3 audio stream found")
    return Audio(path=path, size=path.stat().st_size, seconds=round(info.length))
