"""Command line: each command parses options and calls one function elsewhere."""

from __future__ import annotations

import os
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from typer_agentic import DEFAULT_AGENT_ENV_VARS, agent_errors

from podcast.build import build_site
from podcast.check import check_show
from podcast.errors import PodcastError
from podcast.guide import TOPICS, page, pick_topic
from podcast.scaffold import init_show, new_episode

AGENT = any(os.environ.get(v) for v in DEFAULT_AGENT_ENV_VARS)
console = Console(
    no_color=AGENT, highlight=not AGENT, width=200 if AGENT else None, soft_wrap=True
)
err = Console(stderr=True, no_color=AGENT, highlight=not AGENT, soft_wrap=True)

app = typer.Typer(
    no_args_is_help=True,
    add_completion=False,
    context_settings={"help_option_names": ["-h", "--help"]},
    help="Build a podcast as a static site. Run `podcast guide` first.",
)

Root = Annotated[
    Path, typer.Option("--root", "-r", help="Show directory (holds podcast.toml).")
]
Topic = StrEnum("Topic", {t: t for t in TOPICS})


def _fail(exc: PodcastError) -> typer.Exit:
    err.print(f"error: {exc}", markup=False)
    if exc.hint:
        err.print(f"hint: {exc.hint}", markup=False)
    return typer.Exit(exc.code)


@app.command("init")
def init_cmd(
    directory: Annotated[Path, typer.Argument(help="Where to create the show.")],
    title: Annotated[str, typer.Option(help="Show title.")],
    author: Annotated[str, typer.Option(help="Author / owner name.")],
    email: Annotated[str, typer.Option(help="Owner email for directories.")],
) -> None:
    """Create podcast.toml, episodes/, audio/ and a placeholder cover."""
    try:
        config = init_show(directory, title=title, author=author, email=email)
    except PodcastError as exc:
        raise _fail(exc) from None
    console.print(f"created {config}", markup=False)
    console.print("next: edit base_url and description, then `podcast check`")


@app.command("new")
def new_cmd(
    title: Annotated[str, typer.Argument(help="Episode title.")],
    root: Root = Path(),
) -> None:
    """Start the next numbered episode as a draft."""
    try:
        path, audio = new_episode(root, title, today=datetime.now(UTC).date())
    except PodcastError as exc:
        raise _fail(exc) from None
    console.print(f"created {path}", markup=False)
    console.print(f"record to {audio}", markup=False)


@app.command("check")
def check_cmd(root: Root = Path()) -> None:
    """Report what would stop the show from building or being listed."""
    try:
        problems = check_show(root, now=datetime.now(UTC))
    except PodcastError as exc:
        raise _fail(exc) from None
    for problem in problems:
        console.print(f"{problem.level}: {problem.message}", markup=False)
    if any(p.level == "error" for p in problems):
        raise typer.Exit(1)
    if not problems:
        console.print("ok")


@app.command("build")
def build_cmd(
    root: Root = Path(),
    out: Annotated[Path, typer.Option("--out", "-o", help="Output directory.")] = Path(
        "public"
    ),
) -> None:
    """Render the site and feed into --out, replacing its contents."""
    try:
        result = build_site(root, out, now=datetime.now(UTC))
    except PodcastError as exc:
        raise _fail(exc) from None
    noun = "episode" if result.published == 1 else "episodes"
    held = f", {result.held_back} held back" if result.held_back else ""
    console.print(
        f"built {result.published} {noun}{held} into {result.out}", markup=False
    )


@app.command("guide")
def guide_cmd(
    topic: Annotated[
        Topic | None, typer.Argument(help="setup | use | tune; default: auto")
    ] = None,
    root: Root = Path(),
) -> None:
    """Print instructions for using this tool here (setup, use, tune)."""
    if topic is None:
        name, reason = pick_topic(root)
        console.print(f"# podcast guide: {reason} -> {name}", markup=False)
    else:
        name = str(topic)
    console.print(page(name), markup=False)


main = agent_errors(app)
