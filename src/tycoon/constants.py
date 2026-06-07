"""Default ports and shared constants.

NYC-specific dataset IDs, API URLs, and schema names have moved to
the nyc-transit template (src/tycoon/templates/nyc-transit/).
"""

# Service ports
PORTS = {
    "duckdb_ui": 4213,
    "dbt_docs": 8080,
    "recce": 8000,
    "rill": 9009,
    "tycoon": 8888,
    "dagster": 3000,
    "nao": 5005,
}

# Socrata API pagination (used by rest_api sources targeting Socrata)
SOCRATA_PAGE_SIZE = 50_000

# Supported Python interpreter range. Single source of truth, mirroring
# `requires-python = ">=3.12,<3.14"` in pyproject.toml. dbt-core / dbt-duckdb
# ship no wheels for 3.14 yet, and tycoon runs dbt out of the same interpreter
# it lives in. Used by `tycoon doctor` (the version check) and `tycoon setup`
# (which builds a project-local `.venv` on a supported interpreter). Lift the
# ceiling once dbt supports 3.14.
MIN_PYTHON: tuple[int, int] = (3, 12)
MAX_PYTHON_EXCLUSIVE: tuple[int, int] = (3, 14)
# Default interpreter `tycoon setup` requests from uv when none is specified.
DEFAULT_SETUP_PYTHON = "3.13"


def python_range_str() -> str:
    """Human-readable supported range, e.g. ``>=3.12,<3.14``."""
    lo = f"{MIN_PYTHON[0]}.{MIN_PYTHON[1]}"
    hi = f"{MAX_PYTHON_EXCLUSIVE[0]}.{MAX_PYTHON_EXCLUSIVE[1]}"
    return f">={lo},<{hi}"
