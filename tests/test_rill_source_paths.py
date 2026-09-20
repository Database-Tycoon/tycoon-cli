"""Tests for the ``path:`` that `tycoon.scaffolding.rill_generator` writes
into Rill ``local_file`` source YAMLs.

Regression cover for gh-275: these YAMLs are committed to the user's project
repo, so an absolute path pins the generated project to one machine — it
breaks on every other clone and in CI, and rewrites itself into the diff on
each regeneration.
"""

from __future__ import annotations

from pathlib import Path

from tycoon.scaffolding.rill_generator import (
    _generate_source_yaml,
    _source_yaml_path,
    _write_parquet_backed_source_set,
)


def _path_line(yaml_text: str) -> str:
    """The value of the single ``path:`` key in a source YAML."""
    for line in yaml_text.splitlines():
        if line.startswith("path:"):
            return line.partition(":")[2].strip()
    raise AssertionError(f"no path: line in\n{yaml_text}")


class TestSourceYamlPathIsRelative:
    """The emitted path must be relative to the Rill project directory.

    Rill resolves ``local_file`` paths against its own project root, so the
    relative form is what keeps the generated project portable.
    """

    def test_sibling_data_dir_becomes_a_parent_relative_path(self, tmp_path: Path) -> None:
        # The real layout: <project>/rill/ alongside <project>/data/parquet/.
        rill_dir = tmp_path / "rill"
        parquet = tmp_path / "data" / "parquet" / "_tycoon" / "dbt_nodes.parquet"

        assert _source_yaml_path(parquet, rill_dir) == str(
            Path("..") / "data" / "parquet" / "_tycoon" / "dbt_nodes.parquet"
        )

    def test_generated_yaml_carries_no_absolute_path(self, tmp_path: Path) -> None:
        rill_dir = tmp_path / "rill"
        parquet = tmp_path / "data" / "parquet" / "_tycoon" / "dbt_runs.parquet"

        yaml_text = _generate_source_yaml(parquet, rill_dir)
        path_value = _path_line(yaml_text)

        assert not Path(path_value).is_absolute()
        # The machine-specific prefix must not survive into the committed file.
        assert str(tmp_path) not in yaml_text
        assert yaml_text.startswith("type: source\nconnector: local_file\n")

    def test_parquet_nested_under_the_rill_dir_needs_no_parent_hop(self, tmp_path: Path) -> None:
        rill_dir = tmp_path / "rill"
        parquet = rill_dir / "data" / "orders.parquet"

        assert _source_yaml_path(parquet, rill_dir) == str(Path("data") / "orders.parquet")

    def test_path_resolves_back_to_the_original_file(self, tmp_path: Path) -> None:
        """The relative path must still point at the same file from rill_dir."""
        rill_dir = tmp_path / "rill"
        rill_dir.mkdir()
        parquet = tmp_path / "data" / "parquet" / "_tycoon" / "dbt_nodes.parquet"
        parquet.parent.mkdir(parents=True)
        parquet.write_bytes(b"PAR1")

        emitted = _source_yaml_path(parquet, rill_dir)

        assert (rill_dir / emitted).resolve() == parquet.resolve()


class TestWrittenObservabilitySourcesArePortable:
    """End-to-end cover through the writer that actually produced the bug.

    This is the load-bearing regression test: it goes through
    ``_write_parquet_backed_source_set``, the path that generated the
    absolute-path YAMLs found in a real project, so it fails on the old
    behaviour rather than merely failing to import.
    """

    def test_written_source_yaml_has_no_machine_specific_path(self, tmp_path: Path) -> None:
        rill_dir = tmp_path / "rill"
        parquet = tmp_path / "data" / "parquet" / "_tycoon" / "dbt_nodes.parquet"
        parquet.parent.mkdir(parents=True)
        parquet.write_bytes(b"PAR1")

        _write_parquet_backed_source_set(
            {"dbt_nodes": parquet},
            rill_dir,
            [("dbt_nodes", "_tycoon_dbt_nodes", "type: metrics_view\n", "")],
        )

        written = (rill_dir / "sources" / "_tycoon_dbt_nodes.yaml").read_text()
        path_value = _path_line(written)

        assert not Path(path_value).is_absolute(), f"source YAML pins the project to this machine: {path_value!r}"
        assert str(tmp_path) not in written
        # And it still points at the real file from the Rill project root.
        assert (rill_dir / path_value).resolve() == parquet.resolve()
