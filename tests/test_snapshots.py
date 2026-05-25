"""Snapshot tests for rendered Rich CLI output (#41, v0.1.7).

Catches the class of bug where user-facing strings drift silently —
the Rich-bracket strip ([extra] → empty), stale install hints,
doctor row text drift, etc. Today's tests assert *some* error
appears; these assert *which*.

## Update workflow

When a maintainer intentionally changes a string:

    uv run pytest --snapshot-update tests/test_snapshots.py
    git diff tests/__snapshots__/

The committed `.ambr` files in `tests/__snapshots__/` are the golden
references. Snapshot diffs surface in PRs as plain-text changes that
reviewers can read at a glance.

## Scope (v1)

- Install-hint strings rendered through Rich — the `[extra]` shape
  that triggered the v0.1.6 bracket-strip bug.
- ``tycoon doctor`` rows across cold / half-init / healthy states.
- ``tycoon ask`` startup error paths (the most-rendered user-facing
  text on a fresh install).

Out of scope (deferred to v2): full-screen renders with time-dependent
fields (``data status`` panels showing freshness). Those need a
redactor pass.
"""

from __future__ import annotations

from io import StringIO

from rich.console import Console


def _render(payload: str) -> str:
    """Render a Rich-markup string through a recorded console.

    ``force_terminal=False`` keeps the output deterministic — no ANSI
    escape codes regardless of TTY. ``width=80`` pins line wrapping so
    snapshots don't churn with terminal-size differences in CI.
    """
    buf = StringIO()
    console = Console(file=buf, force_terminal=False, width=80, record=True)
    console.print(payload)
    return console.export_text()


# -- install hints --------------------------------------------------------------


class TestInstallHintRendering:
    """The Rich-bracket pattern that triggered the v0.1.6 strip bug.

    Every install hint in tycoon should escape the extras bracket as
    ``\\[extra]``. These snapshots pin the rendered form so a regression
    (someone re-introduces the unescaped form) surfaces immediately.
    """

    def test_ask_extra_hint(self, snapshot):
        msg = r"Run: [bold]pip install 'database-tycoon\[ask]'[/bold]"
        assert _render(msg) == snapshot

    def test_server_extra_hint(self, snapshot):
        msg = r"Run: [bold]pip install 'database-tycoon\[server]'[/bold]"
        assert _render(msg) == snapshot

    def test_dagster_extra_hint(self, snapshot):
        msg = r"Run: [bold]pip install 'database-tycoon\[dagster]'[/bold]"
        assert _render(msg) == snapshot

    def test_combined_extras_hint(self, snapshot):
        """The recipe doctest harness uses the combined form. Pin it too."""
        msg = r"Run: [bold]pip install 'database-tycoon\[ask,server,dagster]'[/bold]"
        assert _render(msg) == snapshot


# -- doctor rows --------------------------------------------------------------


class TestDoctorRowRendering:
    """Pin the exact text of each doctor row in each state.

    The half-init-vs-cold-start distinction (#38) was missed for several
    releases because no test asserted *which* fix command appeared in
    *which* state. These snapshots are the reactive safety net.
    """

    def test_cold_start_suggests_register_llm(self, snapshot):
        """When `tycoon.yml` has no `ask.llm` block at all."""
        msg = (
            "[yellow bold]WARN[/yellow bold] nao_config.yaml missing — "
            "run [bold]tycoon register llm[/bold] to set up the AI stack."
        )
        assert _render(msg) == snapshot

    def test_half_init_suggests_ask_init(self, snapshot):
        """When `ask.llm` is present but `.tycoon/nao/nao_config.yaml` isn't."""
        msg = (
            "[yellow bold]WARN[/yellow bold] nao_config.yaml missing — "
            "run [bold]tycoon ask init[/bold] to bootstrap from the existing "
            "ask.llm config in tycoon.yml."
        )
        assert _render(msg) == snapshot

    def test_healthy_layer_coverage(self, snapshot):
        """The success path for the v0.1.7 layer-coverage doctor row."""
        msg = (
            "[green bold]OK[/green bold] Layer coverage: every source (3) "
            "has at least one staging model."
        )
        assert _render(msg) == snapshot

    def test_uncovered_source_warning(self, snapshot):
        msg = (
            "[yellow bold]WARN[/yellow bold] Layer coverage: no staging "
            "model found for source(s): orphan, ghost. Scaffold with "
            "`tycoon data analyze <source>` or write models under "
            "`<dbt_project>/models/staging/`."
        )
        assert _render(msg) == snapshot


# -- common error paths -------------------------------------------------------


class TestCommonErrorPaths:
    """The error-path strings that fire on every fresh install."""

    def test_no_tycoon_yml_message(self, snapshot):
        msg = (
            "[red bold]ERROR[/red bold] No tycoon.yml found. "
            "Run [bold]tycoon init[/bold] first, or cd into an existing "
            "tycoon project."
        )
        assert _render(msg) == snapshot

    def test_no_nao_installed_message(self, snapshot):
        """The error users see when `tycoon ask chat` runs without nao-core.

        This is the exact string the Rich-bracket bug mangled in v0.1.5
        before commit c40fda9 in v0.1.6. Pinning prevents regression.
        """
        msg = (
            "[red bold]ERROR[/red bold] Nao is not installed. "
            r"Run: [bold]pip install 'database-tycoon\[ask]'[/bold]"
        )
        assert _render(msg) == snapshot

    def test_no_dbt_manifest_message(self, snapshot):
        """The error path for `data history --layer` without a manifest."""
        msg = (
            "[red bold]ERROR[/red bold] No dbt manifest found. "
            "Run `tycoon data transform run` (or `dbt compile`) before "
            "filtering history by layer."
        )
        assert _render(msg) == snapshot
