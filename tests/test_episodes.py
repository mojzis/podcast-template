from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from podcast.episodes import load_episodes
from podcast.errors import PodcastError
from tests.conftest import NOW, write_episode, write_mp3


def test_published_episode_reads_audio_size_and_duration(show: Path) -> None:
    write_episode(
        show,
        "001-first",
        "title: First\npublished: 2026-11-18T09:00:00+01:00\nreaders: [Ada, Bob]",
    )
    mp3 = write_mp3(show / "audio" / "001-first.mp3", seconds=3)

    [ep] = load_episodes(show, now=NOW).published

    assert ep.slug == "001-first"
    assert ep.number == 1
    assert ep.title == "First"
    assert ep.readers == ("Ada", "Bob")
    assert ep.published == datetime(2026, 11, 18, 8, 0, tzinfo=UTC)
    assert ep.audio is not None
    assert ep.audio.size == mp3.stat().st_size
    assert ep.audio.seconds == 3


def test_drafts_future_and_audioless_episodes_are_held_back(show: Path) -> None:
    write_episode(show, "001-draft", "title: D\npublished: 2026-11-01\ndraft: true")
    write_mp3(show / "audio" / "001-draft.mp3", 1)
    write_episode(show, "002-future", "title: F\npublished: 2026-12-24")
    write_mp3(show / "audio" / "002-future.mp3", 1)
    write_episode(show, "003-silent", "title: S\npublished: 2026-11-02")

    eps = load_episodes(show, now=NOW)

    assert eps.published == ()
    held = {e.slug: reason for e, reason in eps.held_back}
    assert held == {
        "001-draft": "draft",
        "002-future": "scheduled for 2026-12-24",
        "003-silent": "no audio at audio/003-silent.mp3",
    }


def _ready(show: Path, number: int, day: int) -> None:
    write_episode(show, f"00{number}-e", f"title: E\npublished: 2026-11-{day}")
    write_mp3(show / "audio" / f"00{number}-e.mp3", 1)


def test_published_episodes_are_newest_first(show: Path) -> None:
    _ready(show, 1, day=10)
    _ready(show, 2, day=12)
    _ready(show, 3, day=11)

    eps = load_episodes(show, now=NOW).published

    assert [e.number for e in eps] == [2, 3, 1]


def test_summary_defaults_to_first_paragraph_and_transcript_is_picked_up(
    show: Path,
) -> None:
    write_episode(
        show,
        "001-a",
        "title: A\npublished: 2026-11-10",
        body="First *para*.\n\nSecond.",
    )
    write_mp3(show / "audio" / "001-a.mp3", 1)
    (show / "episodes" / "001-a.transcript.md").write_text("Hello listeners.\n")

    [ep] = load_episodes(show, now=NOW).published

    assert ep.summary == "First para."
    assert ep.notes_html == "<p>First <em>para</em>.</p>\n<p>Second.</p>\n"
    assert ep.transcript == "Hello listeners.\n"


def test_raw_html_in_notes_is_escaped(show: Path) -> None:
    write_episode(
        show, "001-a", "title: A\npublished: 2026-11-10", body="<script>x</script>"
    )
    write_mp3(show / "audio" / "001-a.mp3", 1)

    [ep] = load_episodes(show, now=NOW).published

    assert "<script>" not in ep.notes_html


@pytest.mark.parametrize(
    ("front", "message"),
    [
        ("published: 2026-11-10", "001-a.md: missing 'title'"),
        ("title: A", "001-a.md: missing 'published'"),
        ("title: A\npublished: soon", "001-a.md: 'published' is not a date"),
        ("title: A\npublished: 2026-11-10\nreaders: Ada", "'readers' must be a list"),
    ],
)
def test_bad_front_matter_names_the_file_and_field(
    show: Path, front: str, message: str
) -> None:
    write_episode(show, "001-a", front)

    with pytest.raises(PodcastError, match=message):
        load_episodes(show, now=NOW)


def test_episode_files_need_a_number(show: Path) -> None:
    write_episode(show, "intro", "title: A\npublished: 2026-11-10")

    with pytest.raises(PodcastError, match=r"intro\.md: name must start with"):
        load_episodes(show, now=NOW)


def test_duplicate_episode_numbers_are_rejected(show: Path) -> None:
    write_episode(show, "001-a", "title: A\npublished: 2026-11-10")
    write_episode(show, "1-b", "title: B\npublished: 2026-11-11")

    with pytest.raises(
        PodcastError, match=r"episode 1 is used by 001-a\.md and 1-b\.md"
    ):
        load_episodes(show, now=NOW)
