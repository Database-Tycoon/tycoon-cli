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
