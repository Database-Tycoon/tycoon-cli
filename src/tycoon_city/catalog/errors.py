class CatalogError(Exception):
    """Raised when a DuckDB catalog cannot be loaded (missing, invalid, or locked)."""
