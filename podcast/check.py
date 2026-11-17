"""``podcast check``: what would stop the show from building or being listed."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Literal

from podcast.config import load_config
from podcast.episodes import load_episodes
from podcast.imagesize import image_size

GITHUB_FILE_LIMIT = 100 * 1024 * 1024  # GitHub rejects bigger files in a push
_COVER_MIN, _COVER_MAX = 1400, 3000


@dataclass(frozen=True)
class Problem:
    """One finding; errors stop a build, warnings do not."""

    level: Literal["error", "warning"]
    message: str


def check_show(
    root: Path, *, now: datetime, max_audio_bytes: int = GITHUB_FILE_LIMIT
) -> list[Problem]:
    """List every problem with the show in ``root``, errors first.

    Raises:
        PodcastError: the config or an episode cannot be read at all.
    """
    config = load_config(root)
    episodes = load_episodes(root, now=now)
    problems: list[Problem] = []

    if "://example." in config.base_url:
        problems.append(
            Problem("warning", f"base_url is still the placeholder {config.base_url}")
        )
    problems.extend(_cover_problems(root / config.cover, config.cover))
    for ep in episodes.published:
        if ep.audio is not None and ep.audio.size > max_audio_bytes:
            mb = ep.audio.size / 1024 / 1024
            problems.append(
                Problem(
                    "error",
                    f"{ep.slug}: audio is {mb:.0f} MB, over GitHub's file limit; "
                    "re-encode as 64-96 kbit/s mono mp3",
                )
            )
    problems.extend(
        Problem("warning", f"{ep.slug}: held back, {reason}")
        for ep, reason in episodes.held_back
    )
    if not episodes.published:
        problems.append(Problem("warning", "no published episodes yet"))
    return sorted(problems, key=lambda p: p.level != "error")


def _cover_problems(cover: Path, name: str) -> list[Problem]:
    if not cover.is_file():
        return [Problem("error", f"cover image {name} not found")]
    size = image_size(cover)
    if size is None:
        return [Problem("error", f"{name} is not a PNG or JPEG")]
    width, height = size
    if width != height or not _COVER_MIN <= width <= _COVER_MAX:
        return [
            Problem(
                "warning",
                f"{name} is {width}x{height}; Apple wants a square "
                f"{_COVER_MIN}-{_COVER_MAX} px",
            )
        ]
    return []
