"""Refuse to open a MotherDuck target when no token is available (#460).

With no token, DuckDB's MotherDuck extension starts a browser sign-in and
waits for it to finish. At a terminal that is a surprise; in a script, a CI
job or a coding agent it is a hang. Commands that open an ``md:`` or
``motherduck:`` target call :func:`require_motherduck_token` first and exit
with one line instead.

A token counts as available when any of these holds:

* ``MOTHERDUCK_TOKEN`` or ``motherduck_token`` is set in the environment.
  MotherDuck documents both spellings, and #450 and #477 accept both.
* The connection string carries ``motherduck_token=<value>`` in its query part.

The file ``~/.duckdb/motherduck_token`` is deliberately not a token source. On
DuckDB 1.5.4 with both variables unset, a valid token written to that file
still started the browser sign-in, so a guard that accepted the file would let
through exactly the case this module exists to stop.

The duplicate of this check in ``tycoon_city.export.build`` must stay in step:
the renderer does not import ``tycoon``.
"""

from __future__ import annotations

import os
import re

import typer

from tycoon.project import is_motherduck
from tycoon.utils.console import error

TOKEN_ENV = "MOTHERDUCK_TOKEN"
_TOKEN_ENV_NAMES = (TOKEN_ENV, "motherduck_token")
_QUERY_TOKEN_RE = re.compile(r"[?&]motherduck_token=[^&\s]", re.IGNORECASE)


def has_motherduck_token(target: str) -> bool:
    """True when a token is available from the environment or from ``target`` itself."""
    if any(os.environ.get(name, "").strip() for name in _TOKEN_ENV_NAMES):
        return True
    return bool(_QUERY_TOKEN_RE.search(target))


def missing_token_message(target: str) -> str:
    """The one line printed when ``target`` has no token. The query part is dropped, as ``display_target`` does."""
    name = target.split("?", 1)[0]
    return f"No MotherDuck token for {name}: export {TOKEN_ENV} and run again."


def require_motherduck_token(target: str) -> None:
    """Exit 1 with one line when ``target`` is MotherDuck and no token is available.

    A local path returns at once: it never reaches the token lookup.
    """
    if not is_motherduck(target):
        return
    if has_motherduck_token(target):
        return
    error(missing_token_message(target))
    raise typer.Exit(1)
