from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from podcast.build import build_site
from podcast.errors import PodcastError
from tests.conftest import NOW, write_episode, write_mp3

NS = {
    "itunes": "http://www.itunes.com/dtds/podcast-1.0.dtd",
    "podcast": "https://podcastindex.org/namespace/1.0",
    "atom": "http://www.w3.org/2005/Atom",
}
BASE = "https://example.github.io/test-show/"


@pytest.fixture
def built(show: Path, tmp_path: Path) -> Path:
    write_episode(
        show,
        "001-hello",
        "title: Hello & welcome\npublished: 2026-11-18T09:00:00+01:00\n"
        "readers: [Ada, Bob]\nsummary: We say <hi>.",
        body="Show **notes**.",
    )
    (show / "episodes" / "001-hello.transcript.md").write_text("Hi, I am Ada.\n")
    write_mp3(show / "audio" / "001-hello.mp3", seconds=65)
    write_episode(show, "002-draft", "title: Later\npublished: 2026-11-19\ndraft: true")
    out = tmp_path / "public"
    build_site(show, out, now=NOW)
    return out


def _channel(out: Path) -> ET.Element:
    channel = ET.parse(out / "feed.xml").getroot().find("channel")
    assert channel is not None
    return channel


def _attr(parent: ET.Element, path: str, name: str) -> str | None:
    element = parent.find(path, NS)
    return None if element is None else element.get(name)


def _attrs(parent: ET.Element, path: str) -> dict[str, str] | None:
    element = parent.find(path, NS)
    return None if element is None else dict(element.attrib)


def test_feed_channel_has_the_itunes_fields(built: Path) -> None:
    channel = _channel(built)

    assert {
        "title": channel.findtext("title"),
        "link": channel.findtext("link"),
        "author": channel.findtext("itunes:author", namespaces=NS),
        "owner": channel.findtext("itunes:owner/itunes:email", namespaces=NS),
        "explicit": channel.findtext("itunes:explicit", namespaces=NS),
        "image": _attr(channel, "itunes:image", "href"),
        "self": _attr(channel, "atom:link", "href"),
    } == {
        "title": "Test Show",
        "link": BASE,
        "author": "Ada Tester",
        "owner": "ada@example.com",
        "explicit": "false",
        "image": BASE + "cover.png",
        "self": BASE + "feed.xml",
    }


def test_drafts_stay_out_of_the_feed(built: Path) -> None:
    titles = [item.findtext("title") for item in _channel(built).findall("item")]

    assert titles == ["Hello & welcome"]


def test_feed_item_has_enclosure_duration_and_rfc2822_date(built: Path) -> None:
    item = _channel(built).find("item")
    assert item is not None
    size = (built / "audio" / "001-hello.mp3").stat().st_size

    assert {
        "description": item.findtext("description"),
        "pubDate": item.findtext("pubDate"),
        "guid": item.findtext("guid"),
        "episode": item.findtext("itunes:episode", namespaces=NS),
        "duration": item.findtext("itunes:duration", namespaces=NS),
        "enclosure": _attrs(item, "enclosure"),
    } == {
        "description": "We say <hi>.",
        "pubDate": "Wed, 18 Nov 2026 08:00:00 +0000",
        "guid": BASE + "episodes/001-hello/",
        "episode": "1",
        "duration": "65",
        "enclosure": {
            "url": BASE + "audio/001-hello.mp3",
            "type": "audio/mpeg",
            "length": str(size),
        },
    }


def test_feed_item_credits_readers_and_links_the_transcript(built: Path) -> None:
    item = _channel(built).find("item")
    assert item is not None

    assert [p.text for p in item.findall("podcast:person", NS)] == ["Ada", "Bob"]
    assert _attr(item, "podcast:transcript", "url") == (
        BASE + "episodes/001-hello/transcript.txt"
    )


def test_explicit_guid_is_kept(show: Path, tmp_path: Path) -> None:
    write_episode(show, "001-a", "title: A\npublished: 2026-11-10\nguid: old-feed-42")
    write_mp3(show / "audio" / "001-a.mp3", 1)

    build_site(show, tmp_path / "out", now=NOW)

    item = ET.parse(tmp_path / "out" / "feed.xml").getroot().find("channel/item")
    assert item is not None
    assert item.findtext("guid") == "old-feed-42"


def test_index_lists_published_episodes_only(built: Path) -> None:
    index = (built / "index.html").read_text()

    assert 'href="episodes/001-hello/"' in index
    assert "Hello &amp; welcome" in index
    assert "Later" not in index
    assert '<link rel="alternate" type="application/rss+xml"' in index


def test_episode_page_has_player_notes_readers_and_transcript(built: Path) -> None:
    page = (built / "episodes" / "001-hello" / "index.html").read_text()

    assert '<audio controls preload="none" src="../../audio/001-hello.mp3">' in page
    assert "<strong>notes</strong>" in page
    assert "read by Ada, Bob" in page
    assert "Hi, I am Ada." in page


def test_build_writes_transcript_text_and_assets(built: Path) -> None:
    transcript = built / "episodes" / "001-hello" / "transcript.txt"

    assert transcript.read_text() == "Hi, I am Ada.\n"
    assert (built / "cover.png").read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"
    assert sorted(p.name for p in built.iterdir()) == [
        ".nojekyll",
        "audio",
        "cover.png",
        "episodes",
        "feed.xml",
        "index.html",
        "style.css",
    ]


def test_build_replaces_stale_output(show: Path, tmp_path: Path) -> None:
    out = tmp_path / "public"
    (out / "episodes" / "gone").mkdir(parents=True)

    build_site(show, out, now=NOW)

    assert not (out / "episodes" / "gone").exists()


def test_build_refuses_to_wipe_the_show_itself(show: Path) -> None:
    with pytest.raises(PodcastError, match="output directory"):
        build_site(show, show, now=NOW)
