"""The sqlglot schema handed to `lineage()` must be built once and reused.

Regression cover for gh-274. sqlglot's `lineage()` calls `ensure_schema()`,
which builds a **new** `MappingSchema` every time it is handed a plain dict,
normalizing (and so `parse_one`-ing) every identifier in the whole mapping.
Passing the dict straight in therefore re-parses the entire warehouse schema
once per traced column.

This asserts the invariant rather than a wall-clock number, so it cannot go
flaky on a slow runner: `lineage()` must receive a `Schema` instance, and the
same instance every time.
"""

from __future__ import annotations

import sqlglot
from sqlglot.schema import MappingSchema

from tycoon_city.catalog import column_lineage as cl

_COLUMNS = {
    "main.orders": (("id", "INTEGER"), ("customer_id", "INTEGER")),
    "main.customers": (("id", "INTEGER"), ("name", "VARCHAR")),
    "main.order_names": (("id", "INTEGER"), ("name", "VARCHAR")),
}

_SQL = {
    "main.order_names": (
        "SELECT o.id AS id, c.name AS name FROM main.orders o JOIN main.customers c ON c.id = o.customer_id"
    )
}


class TestSchemaIsBuiltOnceAndReused:
    def test_lineage_receives_a_schema_instance_not_a_dict(self, monkeypatch) -> None:
        seen: list[object] = []
        real_lineage = cl.lineage

        def spy(column, sql, schema=None, **kwargs):
            seen.append(schema)
            return real_lineage(column, sql, schema=schema, **kwargs)

        monkeypatch.setattr(cl, "lineage", spy)
        cl.derive_column_lineage(_SQL, _COLUMNS)

        assert seen, "expected at least one lineage() call"
        for schema in seen:
            assert isinstance(schema, MappingSchema), (
                f"a plain dict makes sqlglot rebuild the schema per column; got {type(schema).__name__}"
            )

    def test_every_call_gets_the_identical_object(self, monkeypatch) -> None:
        """Not just equal — the same instance, so no rebuild happened."""
        seen: list[object] = []
        real_lineage = cl.lineage

        def spy(column, sql, schema=None, **kwargs):
            seen.append(schema)
            return real_lineage(column, sql, schema=schema, **kwargs)

        monkeypatch.setattr(cl, "lineage", spy)
        cl.derive_column_lineage(_SQL, _COLUMNS)

        assert len(seen) > 1, "need multiple columns to show reuse"
        first = seen[0]
        assert all(s is first for s in seen)


class TestEdgesAreUnchanged:
    """The optimization must not move a single edge."""

    def test_join_lineage_still_resolves_to_both_sources(self) -> None:
        result = cl.derive_column_lineage(_SQL, _COLUMNS)
        edges = {(e.src, e.src_col, e.dst, e.dst_col) for e in result.edges}

        assert ("main.orders", "id", "main.order_names", "id") in edges
        assert ("main.customers", "name", "main.order_names", "name") in edges
        assert result.unparsed == 0

    def test_schema_still_expands_select_star(self) -> None:
        """`select *` expansion is the reason the schema is passed at all."""
        columns = dict(_COLUMNS)
        columns["main.all_customers"] = (("id", "INTEGER"), ("name", "VARCHAR"))
        result = cl.derive_column_lineage({"main.all_customers": "SELECT * FROM main.customers"}, columns)
        edges = {(e.src, e.src_col, e.dst, e.dst_col) for e in result.edges}

        assert ("main.customers", "name", "main.all_customers", "name") in edges
        assert ("main.customers", "id", "main.all_customers", "id") in edges


def test_sqlglot_still_rebuilds_when_handed_a_dict() -> None:
    """Pins the upstream behaviour this fix exists to avoid.

    If a future sqlglot starts caching dict->MappingSchema itself, this fails
    and the optimization can be revisited.
    """
    schema_dict = {"main": {"customers": {"id": "INTEGER"}}}
    first = sqlglot.schema.ensure_schema(schema_dict)
    second = sqlglot.schema.ensure_schema(schema_dict)

    assert first is not second
