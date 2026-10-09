"""The tycoon-project factory, re-exported.

The factory itself moved to `tycoon_city.demo.factory` on 2026-08-06, when
`tycoon-city demo` started materialising a project at runtime: an installed wheel
has no `tests/` directory, and a second copy of the same knowledge about dbt's
metadata schema would be a second source of truth. This module keeps the import
path every test (and `scripts/make_demo_tycoon.py`) already uses.

No test touches `~/clients/dogfood`; that factory is its stand-in.
"""

from tycoon_city.demo.factory import (
    CASCADE_MODELS,
    CASCADE_RUNS,
    CASCADE_SOURCES,
    CASCADE_TESTS,
    DEFAULT_MODELS,
    DEFAULT_SOURCES,
    DEFAULT_TESTS,
    ModelSpec,
    RunSpec,
    SourceSpec,
    TestSpec,
    make_cascade_project,
    make_tycoon_project,
    write_schema_changes,
    write_sources_json,
)

__all__ = [
    "CASCADE_MODELS",
    "CASCADE_RUNS",
    "CASCADE_SOURCES",
    "CASCADE_TESTS",
    "DEFAULT_MODELS",
    "DEFAULT_SOURCES",
    "DEFAULT_TESTS",
    "ModelSpec",
    "RunSpec",
    "SourceSpec",
    "TestSpec",
    "make_cascade_project",
    "make_tycoon_project",
    "write_schema_changes",
    "write_sources_json",
]
