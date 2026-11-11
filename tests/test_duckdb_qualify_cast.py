"""``QUALIFY`` over just-cast columns builds as a table on the pinned DuckDB (#339).

duckdb 1.5.2 raised ``INTERNAL Error: Failed to bind column reference`` when a
``QUALIFY`` window over columns cast in a CTE was wrapped in ``CREATE TABLE AS``.
That is how dbt materializes a table model, so ``tycoon data transform`` failed
on a common staging dedupe pattern. DuckDB 1.5.4 fixes it.
"""

from __future__ import annotations

import duckdb
import pytest

QUALIFY_OVER_CASTS = """
with renamed as (
    select try_cast(code as integer) as code_int, definition, try_cast(fine as double) as fine
    from src
)
select * from renamed
qualify row_number() over (partition by code_int order by definition) = 1
"""


@pytest.fixture
def con():
    connection = duckdb.connect()
    connection.sql(
        "create table src as select (i % 50)::varchar as code, "
        "'def ' || i as definition, (i*1.5)::varchar as fine from range(200) t(i)"
    )
    yield connection
    connection.close()


def test_create_table_as_over_qualify_on_cast_columns(con):
    con.sql(f"create or replace table out as {QUALIFY_OVER_CASTS}")

    assert con.sql("select count(*), count(distinct code_int) from out").fetchall() == [(50, 50)]
