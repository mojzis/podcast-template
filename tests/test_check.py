from __future__ import annotations

from pathlib import Path

from podcast.check import check_show
from podcast.scaffold import placeholder_cover
from tests.conftest import NOW, write_episode, write_mp3


def test_fresh_show_only_warns_about_placeholders(show: Path) -> None:
    problems = check_show(show, now=NOW)

    assert [(p.level, p.message) for p in problems] == [
        (
            "warning",
            "base_url is still the placeholder https://example.github.io/test-show/",
        ),
        ("warning", "no published episodes yet"),
    ]


def test_held_back_episodes_are_reported(show: Path) -> None:
    write_episode(show, "001-a", "title: A\npublished: 2026-11-10")

    messages = [p.message for p in check_show(show, now=NOW)]

    assert "001-a: held back, no audio at audio/001-a.mp3" in messages


def test_oversized_audio_is_an_error(show: Path) -> None:
    write_episode(show, "001-a", "title: A\npublished: 2026-11-10")
    write_mp3(show / "audio" / "001-a.mp3", 1)

    problems = check_show(show, now=NOW, max_audio_bytes=100)

    assert any(
        p.level == "error" and p.message.startswith("001-a: audio is ")
        for p in problems
    )


def test_cover_must_be_square_and_big_enough(show: Path) -> None:
    (show / "cover.png").write_bytes(placeholder_cover(600, 400))

    messages = [p.message for p in check_show(show, now=NOW)]

    assert "cover.png is 600x400; Apple wants a square 1400-3000 px" in messages
