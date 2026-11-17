"""``podcast guide``: one page of instructions for the agent about to use the tool."""

from __future__ import annotations

from importlib.resources import files
from pathlib import Path

from podcast.config import CONFIG_FILE

TOPICS = ("setup", "use", "tune")


def pick_topic(root: Path) -> tuple[str, str]:
    """Choose a topic from the files in ``root``; return it with the reason."""
    if (root / CONFIG_FILE).is_file():
        return "use", f"found {CONFIG_FILE} in {root}"
    return "setup", f"no {CONFIG_FILE} in {root}"


def page(topic: str) -> str:
    """The markdown for ``topic``."""
    return files("podcast.guide").joinpath(f"{topic}.md").read_text(encoding="utf-8")
