"""Load and validate ``podcast.toml``: everything about the show in one file."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from podcast.errors import PodcastError

CONFIG_FILE = "podcast.toml"
SHOW_TYPES = ("episodic", "serial")


@dataclass(frozen=True)
class Link:
    """Where else the show can be heard (Apple, Spotify, ...)."""

    name: str
    url: str


@dataclass(frozen=True)
class Config:
    """The ``[show]`` table plus ``[[links]]``."""

    title: str
    description: str
    author: str
    email: str  # itunes:owner; directories send verification mail here
    base_url: str  # absolute, always ends with "/"
    language: str = "en"
    category: str = "Technology"  # an Apple Podcasts category
    subcategory: str = ""
    explicit: bool = False
    type: str = "episodic"  # "serial" lists oldest first in podcast apps
    subtitle: str = ""
    copyright: str = ""
    cover: str = "cover.png"  # relative to the show root
    links: tuple[Link, ...] = ()


def load_config(root: Path) -> Config:
    """Read ``root/podcast.toml``.

    Raises:
        PodcastError: the file is missing, unparsable or has a bad value.
    """
    path = root / CONFIG_FILE
    if not path.is_file():
        raise PodcastError(
            f"no {CONFIG_FILE} in {root}", hint="run `podcast init` to create one"
        )
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as exc:
        raise PodcastError(f"{CONFIG_FILE}: {exc}") from None
    show = data.get("show")
    if not isinstance(show, dict):
        raise PodcastError(f"{CONFIG_FILE}: missing the [show] table")
    return Config(
        title=_text(show, "title"),
        description=_text(show, "description"),
        author=_text(show, "author"),
        email=_text(show, "email"),
        base_url=_base_url(show),
        language=_text(show, "language", "en"),
        category=_text(show, "category", "Technology"),
        subcategory=_text(show, "subcategory", ""),
        explicit=_flag(show, "explicit"),
        type=_choice(show, "type", SHOW_TYPES),
        subtitle=_text(show, "subtitle", ""),
        copyright=_text(show, "copyright", ""),
        cover=_text(show, "cover", "cover.png"),
        links=tuple(_links(data.get("links", []))),
    )


def _text(table: dict[str, Any], key: str, default: str | None = None) -> str:
    value = table.get(key, default)
    if value is None or (default is None and value == ""):
        raise PodcastError(f"{CONFIG_FILE}: [show] {key} is required")
    if not isinstance(value, str):
        raise PodcastError(f"{CONFIG_FILE}: [show] {key} must be a string")
    return value.strip()


def _flag(table: dict[str, Any], key: str) -> bool:
    value = table.get(key, False)
    if not isinstance(value, bool):
        raise PodcastError(f"{CONFIG_FILE}: [show] {key} must be true or false")
    return value


def _choice(table: dict[str, Any], key: str, choices: tuple[str, ...]) -> str:
    value = _text(table, key, choices[0])
    if value not in choices:
        allowed = " or ".join(repr(c) for c in choices)
        raise PodcastError(f"{CONFIG_FILE}: [show] {key} must be {allowed}")
    return value


def _base_url(table: dict[str, Any]) -> str:
    url = _text(table, "base_url")
    if not url.startswith("https://"):
        raise PodcastError(
            f"{CONFIG_FILE}: [show] base_url must start with https://",
            hint="podcast directories only accept feeds served over https",
        )
    return url if url.endswith("/") else url + "/"


def _links(raw: object) -> list[Link]:
    if not isinstance(raw, list):
        raise PodcastError(f"{CONFIG_FILE}: [[links]] must be an array of tables")
    links = []
    for item in raw:
        if not isinstance(item, dict) or not {"name", "url"} <= item.keys():
            raise PodcastError(f"{CONFIG_FILE}: every [[links]] needs name and url")
        links.append(Link(name=str(item["name"]), url=str(item["url"])))
    return links
