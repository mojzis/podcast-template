"""Shared fixtures: a scaffolded show in ``tmp_path`` and real (tiny) MP3 files."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from podcast.scaffold import init_show

# MPEG-1 Layer III, 128 kbit/s, 44.1 kHz, no padding: 417-byte frames of 1152 samples.
_FRAME_HEADER = bytes([0xFF, 0xFB, 0x90, 0x64])
_FRAME_SIZE = 417
_FRAME_SECONDS = 1152 / 44100

NOW = datetime(2026, 11, 20, 12, 0, tzinfo=UTC)


@pytest.fixture(autouse=True)
def _plain_terminal(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("_TYPER_FORCE_DISABLE_TERMINAL", "1")


def write_mp3(path: Path, seconds: float) -> Path:
    """Write a silent, valid MP3 of roughly ``seconds`` length."""
    frames = max(1, round(seconds / _FRAME_SECONDS))
    frame = _FRAME_HEADER + bytes(_FRAME_SIZE - len(_FRAME_HEADER))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(frame * frames)
    return path


@pytest.fixture
def show(tmp_path: Path) -> Path:
    """A freshly initialised show directory with the placeholder config."""
    root = tmp_path / "show"
    init_show(root, title="Test Show", author="Ada Tester", email="ada@example.com")
    return root


def write_episode(root: Path, stem: str, front: str, body: str = "Notes.") -> Path:
    """Write ``episodes/<stem>.md`` with the given YAML front matter."""
    path = root / "episodes" / f"{stem}.md"
    path.write_text(f"---\n{front.strip()}\n---\n{body}\n", encoding="utf-8")
    return path
