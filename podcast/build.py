"""Render the site: ``index.html``, one page per episode, ``feed.xml``, assets."""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from datetime import datetime
from email.utils import format_datetime
from importlib.resources import files
from pathlib import Path

from jinja2 import Environment, PackageLoader, StrictUndefined, select_autoescape

from podcast.config import Config, load_config
from podcast.episodes import Episode, load_episodes
from podcast.errors import PodcastError

FEED_FILE = "feed.xml"


@dataclass(frozen=True)
class BuildResult:
    """What a build wrote."""

    out: Path
    published: int
    held_back: int


def build_site(root: Path, out: Path, *, now: datetime) -> BuildResult:
    """Build the show in ``root`` into ``out``, replacing what was there.

    Raises:
        PodcastError: bad config or episodes, or ``out`` would swallow the show.
    """
    _refuse_unsafe_out(root, out)
    config = load_config(root)
    episodes = load_episodes(root, now=now)
    cover = root / config.cover
    if not cover.is_file():
        raise PodcastError(f"cover image {config.cover} not found in {root}")

    if out.exists():
        shutil.rmtree(out)
    (out / "audio").mkdir(parents=True)

    env = _environment()
    cover_name = "cover" + cover.suffix.lower()
    common = {
        "show": config,
        "episodes": episodes.published,
        "cover": cover_name,
        "feed": FEED_FILE,
        "copyright": _copyright(config, episodes.published, now),
    }
    _write(out / "index.html", env.get_template("index.html").render(root="", **common))
    _write(out / FEED_FILE, env.get_template("feed.xml").render(**common))
    for ep in episodes.published:
        page = out / "episodes" / ep.slug
        _write(
            page / "index.html",
            env.get_template("episode.html").render(root="../../", ep=ep, **common),
        )
        if ep.transcript is not None:
            _write(page / "transcript.txt", ep.transcript)
        if ep.audio is not None:
            shutil.copyfile(ep.audio.path, out / "audio" / ep.audio.path.name)

    shutil.copyfile(cover, out / cover_name)
    _write(
        out / "style.css", files("podcast").joinpath("templates/style.css").read_text()
    )
    (out / ".nojekyll").touch()
    return BuildResult(
        out=out, published=len(episodes.published), held_back=len(episodes.held_back)
    )


def _refuse_unsafe_out(root: Path, out: Path) -> None:
    show, target = root.resolve(), out.resolve()
    if target == show or target in show.parents:
        raise PodcastError(
            f"output directory {out} contains the show; building would delete it",
            hint="build into a separate directory, e.g. --out public",
        )


def _environment() -> Environment:
    env = Environment(
        loader=PackageLoader("podcast", "templates"),
        autoescape=select_autoescape(["html", "xml"]),
        undefined=StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
    )
    env.filters["rfc2822"] = format_datetime
    env.filters["clock"] = _clock
    return env


def _clock(seconds: int) -> str:
    """``3725`` -> ``1:02:05``; ``65`` -> ``1:05``."""
    hours, rest = divmod(seconds, 3600)
    minutes, secs = divmod(rest, 60)
    return f"{hours}:{minutes:02d}:{secs:02d}" if hours else f"{minutes}:{secs:02d}"


def _copyright(config: Config, episodes: tuple[Episode, ...], now: datetime) -> str:
    if config.copyright:
        return config.copyright
    first = min((e.published.year for e in episodes), default=now.year)
    years = f"{first}" if first == now.year else f"{first}-{now.year}"
    return f"© {years} {config.author}"


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
