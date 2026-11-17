"""The one exception type for expected, user-facing failures."""

from __future__ import annotations


class PodcastError(Exception):
    """A problem the user can fix; printed as ``error:`` plus an optional hint."""

    def __init__(self, message: str, hint: str | None = None, code: int = 1) -> None:
        super().__init__(message)
        self.hint = hint
        self.code = code  # exit code: 1 failure, 2 usage or config
