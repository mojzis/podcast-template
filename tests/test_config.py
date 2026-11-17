from __future__ import annotations

from pathlib import Path

import pytest

from podcast.config import Config, load_config
from podcast.errors import PodcastError


def test_init_writes_a_config_that_loads(show: Path) -> None:
    config = load_config(show)

    assert config == Config(
        title="Test Show",
        description="What the show is about, in a sentence or two.",
        author="Ada Tester",
        email="ada@example.com",
        base_url="https://example.github.io/test-show/",
    )


def test_base_url_gets_a_trailing_slash(show: Path) -> None:
    toml = show / "podcast.toml"
    toml.write_text(
        toml.read_text().replace(
            'base_url = "https://example.github.io/test-show/"',
            'base_url = "https://example.github.io/x"',
        )
    )

    assert load_config(show).base_url == "https://example.github.io/x/"


def test_links_are_read_in_order(show: Path) -> None:
    with (show / "podcast.toml").open("a") as f:
        f.write(
            '\n[[links]]\nname = "Apple"\nurl = "https://apple.example"\n'
            '\n[[links]]\nname = "Spotify"\nurl = "https://spotify.example"\n'
        )

    links = load_config(show).links

    assert [(link.name, link.url) for link in links] == [
        ("Apple", "https://apple.example"),
        ("Spotify", "https://spotify.example"),
    ]


def test_missing_config_says_how_to_create_one(tmp_path: Path) -> None:
    with pytest.raises(PodcastError, match=r"no podcast\.toml") as info:
        load_config(tmp_path)

    assert info.value.hint == "run `podcast init` to create one"


@pytest.mark.parametrize(
    ("old", "new", "message"),
    [
        ('title = "Test Show"', "", r"\[show\] title is required"),
        (
            "explicit = false",
            'explicit = "no"',
            r"\[show\] explicit must be true or false",
        ),
        (
            'base_url = "https://example.github.io/test-show/"',
            'base_url = "example.github.io"',
            r"\[show\] base_url must start with https://",
        ),
        ('type = "episodic"', 'type = "weekly"', "type must be 'episodic' or 'serial'"),
    ],
)
def test_invalid_values_name_the_key(
    show: Path, old: str, new: str, message: str
) -> None:
    toml = show / "podcast.toml"
    text = toml.read_text()
    assert old in text
    toml.write_text(text.replace(old, new))

    with pytest.raises(PodcastError, match=message):
        load_config(show)
