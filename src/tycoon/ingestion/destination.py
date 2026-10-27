"""The dlt destination for a raw database target."""

from __future__ import annotations

import importlib.util
import os
from pathlib import Path

import dlt
from dlt.common.destination import Destination

from tycoon.project import MOTHERDUCK_PREFIX, is_motherduck


def _has_pyarrow() -> bool:
    return importlib.util.find_spec("pyarrow") is not None


def _has_token(target: str) -> bool:
    return bool(
        os.environ.get("MOTHERDUCK_TOKEN") or os.environ.get("motherduck_token") or "motherduck_token=" in target
    )


def raw_destination(target: str | Path) -> Destination:
    """The dlt destination for ``database.raw``.

    A MotherDuck target (``md:`` or ``motherduck:``) gets dlt's motherduck
    destination, a local DuckDB file path gets the duckdb one. dlt only parses
    the ``md:`` spelling, so ``motherduck:`` is rewritten to it. dlt does not
    create the MotherDuck database, which has to exist before the first run.
    """
    text = str(target)
    if not is_motherduck(text):
        return dlt.destinations.duckdb(text)
    if not _has_token(text):
        from tycoon.ingestion.runner import IngestionError

        raise IngestionError(
            "database.raw is MotherDuck, but MOTHERDUCK_TOKEN is not set in the environment. Export it in the "
            "shell that runs tycoon, then run again: tycoon does not read .env files, and a token that is only "
            "in .dlt/secrets.toml is not used. Create a token at app.motherduck.com."
        )
    if not _has_pyarrow():
        from tycoon.ingestion.runner import IngestionError

        raise IngestionError(
            "Loading into MotherDuck needs pyarrow, which tycoon does not install by default. "
            "Install it into the environment tycoon runs in (pip install pyarrow) and run again."
        )
    return dlt.destinations.motherduck(MOTHERDUCK_PREFIX + text.split(":", 1)[1])
