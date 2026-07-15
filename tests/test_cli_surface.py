"""CLI-surface health tests — catch stale strings, broken `--help`, and
namespace drift before users see them.

These are *meta*-tests: they walk the registered command tree rather
than testing any one feature. Their job is to reject regressions like:

- A removed command name surfacing in a warn/error/help string
- An outdated package name in an install hint
- `--help` regressing to non-zero exit on any subcommand
- A user-facing string referencing a command path that no longer exists

The motivating regression: v0.1.5 removed `tycoon ask init` and
`tycoon ask install-model`. Three live error / warn / docstring strings
in `src/tycoon/` continued to point at them. None of the existing
tests caught the drift because no test was looking at the strings
themselves. This file fixes that.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tycoon.cli import app


# -- Stale-string registry ------------------------------------------------
#
# Every entry is a substring that should NOT appear anywhere in the
# tycoon source tree (excluding tests + this file). Add to this list
# whenever a command/module is renamed or removed; that one-line
# addition then guards against regressions across the entire codebase.

_STALE_SUBSTRINGS: tuple[tuple[str, str], ...] = (
    # Note: `tycoon ask init` was removed in v0.1.5 (it had been a
    # confusing alias for `register llm`) and re-introduced in v0.1.6
    # with a different contract: idempotent project-bootstrap that
    # writes nao_config.yaml from the existing tycoon.yml, no prompts.
    # That's why this list no longer flags "tycoon ask init" — the
    # current command is genuine, not a regression to the old one.
    ("ask install-model",
        "removed in v0.1.5 — folded into `tycoon register llm`"),
    ("pip install tycoon[",
        "wrong package name — use `pip install database-tycoon[...]`"),
    ("pip install tycoon\\[",
        "wrong package name — use `pip install database-tycoon[...]`"),
    ("pip install 'tycoon[",
        "wrong package name — use `pip install 'database-tycoon[...]'`"),
)


# -- Command tree introspection -------------------------------------------


def _all_command_paths(typer_app, prefix: tuple[str, ...] = ()) -> list[tuple[str, ...]]:
    """Return every reachable subcommand path in a Typer app.

    Each path is a tuple of arg strings, e.g. ``("data", "sources",
    "run")`` for ``tycoon data sources run``.
    """
    paths: list[tuple[str, ...]] = [prefix] if prefix else []
    for cmd in typer_app.registered_commands:
        if cmd.name:
            paths.append(prefix + (cmd.name,))
    for grp in typer_app.registered_groups:
        if grp.name and grp.typer_instance is not None:
            paths.extend(_all_command_paths(grp.typer_instance, prefix + (grp.name,)))
    return paths


# -- 1. No stale strings anywhere in source -------------------------------


class TestStaleStringSentinel:
    """Walk src/tycoon/ and reject any file containing a known-stale
    substring. Excludes test files (which legitimately reference old
    names in regression-test descriptions) and historical release notes.
    """

    @pytest.fixture
    def src_files(self) -> list[Path]:
        src = Path(__file__).parent.parent / "src" / "tycoon"
        return sorted(src.rglob("*.py"))

    @pytest.mark.parametrize("needle,reason", _STALE_SUBSTRINGS)
    def test_substring_absent_from_src(
        self, src_files: list[Path], needle: str, reason: str
    ):
        """Each needle must appear in zero source files."""
        offenders: list[tuple[Path, int, str]] = []
        for f in src_files:
            try:
                lines = f.read_text(errors="replace").splitlines()
            except OSError:
                continue
            for i, line in enumerate(lines, start=1):
                if needle in line:
                    offenders.append((f, i, line.strip()))
        assert not offenders, (
            f"Found stale substring {needle!r} ({reason}) in:\n"
            + "\n".join(
                f"  {f.relative_to(Path(__file__).parent.parent)}:{i}: {line}"
                for f, i, line in offenders
            )
        )


# -- 2. Top-level + key subcommand --help works --------------------------
#
# A bigger parametrized walk over EVERY command is tempting but
# fragile — some commands (e.g. ones that touch live services) hang
# their `--help` under typer's CliRunner. Instead, hard-list the
# user-facing entry points whose help surface most needs to stay
# stable. The stale-string sentinel above already covers source-level
# drift everywhere.


_KEY_HELP_PATHS = [
    (),                                  # top-level
    ("init",),
    ("register",),
    ("register", "dbt"),
    ("register", "warehouse"),
    ("register", "rill"),
    ("data",),
    ("data", "sources"),
    ("data", "transform"),
    ("data", "sync"),
    ("data", "analyze"),
    ("doctor",),
]


class TestHelpSurface:
    """Top-level commands' --help must:
    - exit 0
    - not contain stale strings
    """

    @pytest.mark.parametrize("path", _KEY_HELP_PATHS, ids=lambda p: " ".join(p) or "tycoon")
    def test_help_exits_clean(self, path: tuple[str, ...], cli_runner):
        result = cli_runner.invoke(app, list(path) + ["--help"])
        assert result.exit_code == 0, (
            f"`tycoon {' '.join(path)} --help` exited {result.exit_code}\n"
            f"--- stdout ---\n{result.stdout}"
        )

    @pytest.mark.parametrize("path", _KEY_HELP_PATHS, ids=lambda p: " ".join(p) or "tycoon")
    def test_help_has_no_stale_strings(self, path: tuple[str, ...], cli_runner):
        result = cli_runner.invoke(app, list(path) + ["--help"])
        for needle, reason in _STALE_SUBSTRINGS:
            assert needle not in result.stdout, (
                f"`tycoon {' '.join(path)} --help` output contains stale "
                f"substring {needle!r} ({reason}):\n{result.stdout}"
            )


# -- 3. Rich-markup pitfall: extras names must render literally ----------
#
#         Rich treats `[docs]` as a style tag and silently strips it
#         unless the bracket is escaped. Lock in the rendered output,
#         not just the source.


class TestExtrasNamesRenderLiterally:
    """Regression: every user-facing message that suggests
    `pip install 'database-tycoon[<extra>]'` must render the extras
    name through Rich without stripping the brackets.

    The `error()`, `warn()`, and `info()` helpers use the project's
    shared Rich console — which parses markup — so an unescaped
    `[docs]` becomes a (nonexistent) style and disappears.
    """

    def _render(self, message_string: str) -> str:
        """Render a string through a fresh Rich console and return plain text."""
        from rich.console import Console

        c = Console(record=True, force_terminal=False, width=200)
        c.print(message_string)
        return c.export_text()

    def test_docs_install_hint_renders(self):
        msg = (
            "MkDocs is not installed. Install the docs extra: "
            r"[bold]pip install 'database-tycoon\[docs]'[/bold]"
        )
        rendered = self._render(msg)
        assert "database-tycoon[docs]" in rendered, rendered

    def test_no_unescaped_extras_remain_in_source(self):
        """Catch-all: scan every commands/*.py source file for the
        bug pattern (unescaped `database-tycoon[<extra>]`). The escape
        is `\\[` — a Rich literal-bracket marker. Any unescaped form is
        a regression."""
        import re

        commands_dir = Path(__file__).parent.parent / "src" / "tycoon" / "commands"
        # Pattern matches `database-tycoon[anything]` where the `[` is
        # NOT preceded by a backslash. Lookbehind keeps the regex tight.
        unescaped = re.compile(r"(?<!\\)database-tycoon\[")

        offenders: list[str] = []
        for src_file in commands_dir.rglob("*.py"):
            text = src_file.read_text()
            for match in unescaped.finditer(text):
                # Skip docstring-resident matches — those don't go through
                # Rich. Detection: count `"""` occurrences before the
                # match; odd count means we're mid-docstring.
                triple_count = text.count('"""', 0, match.start())
                if triple_count % 2 == 1:
                    continue
                line_start = text.rfind("\n", 0, match.start()) + 1
                line_end = text.find("\n", match.start())
                line = text[line_start:line_end if line_end != -1 else None]
                offenders.append(f"{src_file.name}: {line.strip()}")

        assert not offenders, (
            "Unescaped `database-tycoon[<extra>]` found — Rich will strip "
            "the brackets. Use `database-tycoon\\\\[<extra>]` instead.\n"
            + "\n".join(offenders)
        )


# -- 5. Smoke-check that `tycoon --version` returns the published version
#       (catches `__init__.py` and `pyproject.toml` drift). Belt-and-
#       suspenders against the release-prep version-pin coherence gate.


class TestVersionString:

    def test_version_matches_init_module(self, cli_runner):
        from tycoon import __version__

        result = cli_runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert __version__ in result.stdout, (
            f"`tycoon --version` printed {result.stdout!r}, expected substring "
            f"{__version__!r}"
        )

    def test_version_matches_pyproject(self):
        """`__version__` and pyproject.toml's [project].version must agree.

        This is also gated by publish.yml's preflight job, but locking
        it in pytest catches the drift earlier (during PR CI, not at
        tag-push time).
        """
        from tycoon import __version__

        pyproject = (Path(__file__).parent.parent / "pyproject.toml").read_text()
        # The first `version = "X.Y.Z"` after the [project] header is
        # the one we care about. Walk by hand to avoid pulling in a TOML
        # parser just for this assertion.
        in_project = False
        pin = None
        for line in pyproject.splitlines():
            if line.strip() == "[project]":
                in_project = True
                continue
            if in_project and line.startswith("["):
                break
            if in_project and line.startswith("version"):
                pin = line.split("=", 1)[1].strip().strip('"').strip("'")
                break
        assert pin == __version__, (
            f"pyproject.toml [project].version={pin!r} but "
            f"src/tycoon/__init__.py __version__={__version__!r}"
        )
