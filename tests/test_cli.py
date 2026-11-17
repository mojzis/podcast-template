from __future__ import annotations

import re
from pathlib import Path

import pytest
from typer.testing import CliRunner

from podcast.cli import app
from podcast.guide import TOPICS
from tests.conftest import write_episode, write_mp3

runner = CliRunner()


def test_init_then_check_then_build(tmp_path: Path) -> None:
    root = tmp_path / "show"
    result = runner.invoke(
        app,
        [
            "init",
            str(root),
            "--title",
            "My Show",
            "--author",
            "Me",
            "--email",
            "m@x.org",
        ],
    )
    assert result.exit_code == 0, result.output
    assert (root / "podcast.toml").is_file()

    write_episode(root, "001-a", "title: A\npublished: 2026-01-10")
    write_mp3(root / "audio" / "001-a.mp3", 2)

    result = runner.invoke(app, ["check", "--root", str(root)])
    assert result.exit_code == 0, result.output
    assert "base_url is still the placeholder" in result.output

    out = tmp_path / "public"
    result = runner.invoke(app, ["build", "--root", str(root), "--out", str(out)])
    assert result.exit_code == 0, result.output
    assert "1 episode" in result.output
    assert (out / "episodes" / "001-a" / "index.html").is_file()


def test_init_refuses_an_existing_show(show: Path) -> None:
    result = runner.invoke(
        app, ["init", str(show), "--title", "X", "--author", "Y", "--email", "z@x.org"]
    )

    assert result.exit_code == 2
    assert "error: " in result.output
    assert "already has a podcast.toml" in result.output


def test_new_numbers_episodes_after_the_last_one(show: Path) -> None:
    write_episode(show, "007-old", "title: Old\npublished: 2026-01-10")

    result = runner.invoke(app, ["new", "Über Café!", "--root", str(show)])

    assert result.exit_code == 0, result.output
    created = show / "episodes" / "008-uber-cafe.md"
    assert created.is_file()
    assert "title: Über Café!" in created.read_text()
    assert "draft: true" in created.read_text()
    assert "audio/008-uber-cafe.mp3" in result.output


def test_check_fails_on_errors(show: Path) -> None:
    write_episode(show, "001-a", "published: 2026-01-10")

    result = runner.invoke(app, ["check", "--root", str(show)])

    assert result.exit_code == 1
    assert "001-a.md: missing 'title'" in result.output


def test_guide_autodetects_setup_then_use(show: Path, tmp_path: Path) -> None:
    empty = runner.invoke(app, ["guide", "--root", str(tmp_path / "nothing")])
    configured = runner.invoke(app, ["guide", "--root", str(show)])

    assert empty.exit_code == 0
    assert empty.output.splitlines()[0].endswith("-> setup")
    assert configured.exit_code == 0
    assert configured.output.splitlines()[0].endswith("-> use")


@pytest.mark.parametrize("topic", TOPICS)
def test_every_guide_topic_prints_and_names_real_commands(topic: str) -> None:
    result = runner.invoke(app, ["guide", topic])
    assert result.exit_code == 0
    assert result.output.strip()

    commands = {c.name for c in app.registered_commands}
    mentioned = set(re.findall(r"podcast ([a-z]+)", result.output))
    assert mentioned, "every page shows at least one command"
    assert mentioned <= commands, mentioned - commands
