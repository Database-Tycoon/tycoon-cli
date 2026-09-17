"""Rewrite contract/fixtures/demo.city.json from contract/fixtures/demo.duckdb.

Run this whenever a deliberate contract change makes
`tests/export/test_city_json.py::test_golden_matches_a_fresh_emit` fail, and
review the diff -- that diff *is* the contract change, and it is the only place
an accidental one shows up before a client breaks on it.

    uv run python scripts/update_contract_golden.py
"""

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from tycoon_city.export import build_city, city_document, dumps  # noqa: E402
from tycoon_city.theme_data import load_theme_data, theme_dir  # noqa: E402

GOLDEN = REPO / "contract" / "fixtures" / "demo.city.json"


def main() -> int:
    theme = load_theme_data(theme_dir("default"))
    ctx, city = build_city(GOLDEN.parent / "demo.duckdb", theme.style_rules)
    text = dumps(city_document(ctx, city, theme))

    previous = GOLDEN.read_text(encoding="utf-8") if GOLDEN.exists() else None
    GOLDEN.parent.mkdir(parents=True, exist_ok=True)
    GOLDEN.write_text(text, encoding="utf-8")

    if previous == text:
        print(f"{GOLDEN.relative_to(REPO)} unchanged")
    else:
        print(f"rewrote {GOLDEN.relative_to(REPO)} ({len(text)} bytes) -- review the diff")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
