"""Create a show (``podcast init``) and episode stubs (``podcast new``)."""

from __future__ import annotations

import re
import struct
import unicodedata
import zlib
from datetime import date
from pathlib import Path

from podcast.config import CONFIG_FILE
from podcast.episodes import AUDIO_DIR, EPISODE_NAME, EPISODES_DIR, audio_path
from podcast.errors import PodcastError

COVER_SIZE = 1400  # Apple's minimum; the maximum is 3000
_COVER_RGB = (0x2B, 0x4C, 0x7E)

_CONFIG_TEMPLATE = """\
# Everything about the show. `podcast guide tune` explains each key.

[show]
title = "{title}"
description = "What the show is about, in a sentence or two."
author = "{author}"
email = "{email}"   # itunes:owner -- Apple and Spotify send verification mail here
base_url = "https://example.github.io/{slug}/"   # where the site is served
language = "en"
category = "Technology"   # an Apple Podcasts category
subcategory = ""
explicit = false
type = "episodic"   # or "serial"
cover = "cover.png"   # square JPEG or PNG, 1400-3000 px

# Where else people can listen. Add these once the directories list you.
# [[links]]
# name = "Apple Podcasts"
# url = "https://podcasts.apple.com/..."
"""

_EPISODE_TEMPLATE = """\
---
title: {title}
published: {published}
readers: []
draft: true
---
Show notes in markdown. The first paragraph is the summary podcast apps show.
"""


def init_show(root: Path, *, title: str, author: str, email: str) -> Path:
    """Create ``podcast.toml``, ``episodes/``, ``audio/`` and a placeholder cover.

    Raises:
        PodcastError: ``root`` already holds a show.
    """
    config = root / CONFIG_FILE
    if config.exists():
        raise PodcastError(
            f"{root} already has a {CONFIG_FILE}",
            hint="edit it instead of re-running",
            code=2,
        )
    for sub in (EPISODES_DIR, AUDIO_DIR):
        (root / sub).mkdir(parents=True, exist_ok=True)
        (root / sub / ".gitkeep").touch()
    config.write_text(
        _CONFIG_TEMPLATE.format(
            title=_toml_escape(title),
            author=_toml_escape(author),
            email=_toml_escape(email),
            slug=slugify(title) or "my-podcast",
        ),
        encoding="utf-8",
    )
    cover = root / "cover.png"
    if not cover.exists():
        cover.write_bytes(placeholder_cover(COVER_SIZE, COVER_SIZE))
    return config


def new_episode(root: Path, title: str, *, today: date) -> tuple[Path, Path]:
    """Write the next numbered draft episode; return it and where its mp3 goes.

    Raises:
        PodcastError: the file already exists.
    """
    episodes = root / EPISODES_DIR
    numbers = [
        int(m.group(1))
        for p in episodes.glob("*.md")
        if (m := EPISODE_NAME.match(p.stem)) is not None
    ]
    slug = f"{max(numbers, default=0) + 1:03d}-{slugify(title) or 'episode'}"
    path = episodes / f"{slug}.md"
    if path.exists():
        raise PodcastError(f"{path} already exists")
    episodes.mkdir(parents=True, exist_ok=True)
    path.write_text(
        _EPISODE_TEMPLATE.format(
            title=_yaml_scalar(title), published=today.isoformat()
        ),
        encoding="utf-8",
    )
    return path, audio_path(root, slug)


def slugify(text: str) -> str:
    """ASCII, lowercase, dash-separated: ``Über Café!`` -> ``uber-cafe``."""
    ascii_text = (
        unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    )
    return re.sub(r"[^a-z0-9]+", "-", ascii_text.lower()).strip("-")


def placeholder_cover(width: int, height: int) -> bytes:
    """A single-colour PNG, so a fresh show builds before real art exists."""
    row = b"\x00" + bytes(_COVER_RGB) * width
    raw = zlib.compress(row * height, 9)

    def chunk(kind: bytes, data: bytes) -> bytes:
        body = kind + data
        return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body))

    header = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", header)
        + chunk(b"IDAT", raw)
        + chunk(b"IEND", b"")
    )


def _toml_escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace('"', '\\"')


def _yaml_scalar(text: str) -> str:
    """Quote a title only when YAML would misread it."""
    if re.fullmatch(r"[\w .,!?'()&-]+", text) and text[0] not in "!&'-":
        return text
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'
