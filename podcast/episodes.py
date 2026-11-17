"""Episodes: ``episodes/NNN-slug.md`` (front matter, notes) + ``audio/NNN-slug.mp3``.

An episode is published when it is not a draft, its date has come and its audio is
there. Everything else is *held back*, with the reason, so ``podcast check`` can say
why an episode is missing from the feed.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, date, datetime, time
from pathlib import Path
from typing import Any

import yaml
from markdown_it import MarkdownIt

from podcast.audio import Audio, probe
from podcast.errors import PodcastError

EPISODES_DIR = "episodes"
AUDIO_DIR = "audio"
TRANSCRIPT_SUFFIX = ".transcript.md"
EPISODE_NAME = re.compile(r"^(\d+)-")
_markdown = MarkdownIt("commonmark", {"html": False}).enable("table")


@dataclass(frozen=True)
class Episode:
    """One episode, ready to render."""

    slug: str  # file stem, also the URL segment
    number: int
    title: str
    published: datetime  # UTC
    summary: str  # plain text, one paragraph
    notes_html: str
    readers: tuple[str, ...] = ()
    season: int | None = None
    guid: str | None = None  # None: the episode page URL
    transcript: str | None = None  # markdown source
    audio: Audio | None = None
    draft: bool = False


@dataclass(frozen=True)
class Episodes:
    """All episodes in a show, split by whether they go out."""

    published: tuple[Episode, ...]  # newest first
    held_back: tuple[tuple[Episode, str], ...]  # (episode, reason)


def load_episodes(root: Path, *, now: datetime) -> Episodes:
    """Read every ``episodes/*.md`` under ``root``.

    Raises:
        PodcastError: a file is misnamed, has bad front matter, or two files share
            an episode number.
    """
    files = sorted(
        p
        for p in (root / EPISODES_DIR).glob("*.md")
        if not p.name.endswith(TRANSCRIPT_SUFFIX)
    )
    episodes = [_load(path, root) for path in files]
    _reject_duplicate_numbers(episodes)

    published, held = [], []
    for ep in episodes:
        reason = _hold_reason(ep, now)
        if reason is None:
            published.append(ep)
        else:
            held.append((ep, reason))
    published.sort(key=lambda e: e.published, reverse=True)
    return Episodes(published=tuple(published), held_back=tuple(held))


def audio_path(root: Path, slug: str) -> Path:
    """Where an episode's mp3 is expected."""
    return root / AUDIO_DIR / f"{slug}.mp3"


def _load(path: Path, root: Path) -> Episode:
    match = EPISODE_NAME.match(path.stem)
    if match is None:
        raise PodcastError(
            f"{path.name}: name must start with the episode number",
            hint="e.g. 001-first-episode.md; `podcast new` picks the next number",
        )
    front, body = _split(path)
    transcript_file = path.with_name(path.stem + TRANSCRIPT_SUFFIX)
    mp3 = audio_path(root, path.stem)
    return Episode(
        slug=path.stem,
        number=int(match.group(1)),
        title=_required(front, "title", path),
        published=_published(front, path),
        summary=_summary(front, body, path),
        notes_html=_markdown.render(body),
        readers=_readers(front, path),
        season=_optional_int(front, "season", path),
        guid=str(front["guid"]) if front.get("guid") else None,
        transcript=(
            transcript_file.read_text(encoding="utf-8")
            if transcript_file.is_file()
            else None
        ),
        audio=probe(mp3) if mp3.is_file() else None,
        draft=front.get("draft") is True,
    )


def _split(path: Path) -> tuple[dict[str, Any], str]:
    text = path.read_text(encoding="utf-8")
    parts = text.split("---\n", 2)
    if not text.startswith("---\n") or len(parts) < 3:  # noqa: PLR2004 -- "", front, body
        raise PodcastError(f"{path.name}: must start with --- front matter ---")
    try:
        front = yaml.safe_load(parts[1]) or {}
    except yaml.YAMLError as exc:
        raise PodcastError(f"{path.name}: front matter is not YAML ({exc})") from None
    if not isinstance(front, dict):
        raise PodcastError(f"{path.name}: front matter must be key: value pairs")
    return front, parts[2].strip()


def _required(front: dict[str, Any], key: str, path: Path) -> str:
    value = front.get(key)
    if value is None or str(value).strip() == "":
        raise PodcastError(f"{path.name}: missing '{key}'")
    return str(value).strip()


def _published(front: dict[str, Any], path: Path) -> datetime:
    value = front.get("published")
    if value is None:
        raise PodcastError(f"{path.name}: missing 'published'")
    if isinstance(value, datetime):
        moment = value
    elif isinstance(value, date):
        moment = datetime.combine(value, time())
    else:
        try:
            moment = datetime.fromisoformat(str(value))
        except ValueError:
            raise PodcastError(
                f"{path.name}: 'published' is not a date",
                hint="use 2026-11-20 or 2026-11-20T09:00:00+01:00",
            ) from None
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=UTC)
    return moment.astimezone(UTC)


def _summary(front: dict[str, Any], body: str, path: Path) -> str:
    if front.get("summary"):
        return _required(front, "summary", path)
    first = body.split("\n\n", 1)[0]
    tokens = _markdown.parseInline(first)
    return "".join(
        child.content
        for token in tokens
        for child in token.children or []
        if child.type in {"text", "code_inline"}
    ).strip()


def _readers(front: dict[str, Any], path: Path) -> tuple[str, ...]:
    value = front.get("readers", [])
    if not isinstance(value, list):
        raise PodcastError(
            f"{path.name}: 'readers' must be a list", hint="readers: [Ada, Bob]"
        )
    return tuple(str(v) for v in value)


def _optional_int(front: dict[str, Any], key: str, path: Path) -> int | None:
    value = front.get(key)
    if value is None:
        return None
    if not isinstance(value, int) or isinstance(value, bool):
        raise PodcastError(f"{path.name}: '{key}' must be a whole number")
    return value


def _reject_duplicate_numbers(episodes: list[Episode]) -> None:
    seen: dict[int, str] = {}
    for ep in episodes:
        if ep.number in seen:
            raise PodcastError(
                f"episode {ep.number} is used by {seen[ep.number]}.md and {ep.slug}.md"
            )
        seen[ep.number] = ep.slug


def _hold_reason(ep: Episode, now: datetime) -> str | None:
    if ep.draft:
        return "draft"
    if ep.published > now:
        return f"scheduled for {ep.published.date().isoformat()}"
    if ep.audio is None:
        return f"no audio at {AUDIO_DIR}/{ep.slug}.mp3"
    return None
