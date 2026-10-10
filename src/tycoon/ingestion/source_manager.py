"""Download and manage dlt verified sources on demand.

Sources are installed via `dlt init`, then a thin _run.py shim is written
alongside the source package to bridge dlt's native API with tycoon's
run_pipeline(name, source_config, raw_db_path, max_records) interface.

A project with its own `.venv` (gh-262) gets its own project-local
`<project>/.tycoon/sources/` instead of the shared, global
`~/.tycoon/sources/`, see `resolve_sources_dir()`. A project that hasn't
picked up a `.venv` yet keeps resolving from the global directory, unchanged,
so anything already downloaded there keeps working (gh-261). A source
already downloaded globally before the project picked up a `.venv` doesn't
move on its own, `migrate_source()` copies it into the new project-local
directory on request (`tycoon data sources migrate <type>`).
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

from tycoon.utils.console import info, warn
from tycoon.venv import venv_path

SOURCES_DIR = Path.home() / ".tycoon" / "sources"

# `dlt init` reaches out to github.com; cap it so a network that accepts
# connections but never answers fails instead of hanging the command.
_DLT_INIT_TIMEOUT = 120

# install_source parks the shared requirements.txt under this name while
# `dlt init` runs (gh-364); a file with this suffix only outlives a run that
# was killed mid-install, and the next run recovers it.
_PARKED_REQUIREMENTS_NAME = "requirements.txt.tycoon-parked"


def _requirement_key(line: str) -> str:
    """Whitespace-insensitive identity for a requirements line, so
    `requests>=2` and `requests >= 2` dedupe as one (gh-364 review)."""
    return "".join(line.split())


def _merge_parked_requirements(shared_reqs: Path, parked_reqs: Path) -> None:
    """Fold a parked shared requirements.txt back in after `dlt init`.

    dlt either wrote `shared_reqs` fresh for the source just downloaded, or
    wrote nothing (a failed run, or a source with no requirements of its
    own). Either way the shared file must come back as the union. Carried
    lines go first: `uv add -r` lets the last specifier for a package win,
    so the freshly downloaded source's own pin has to come after the
    carried history, not before it (gh-364 review).
    """
    if not parked_reqs.exists():
        return
    if not shared_reqs.exists():
        parked_reqs.replace(shared_reqs)
        return
    fresh = shared_reqs.read_text()
    seen = {_requirement_key(line) for line in fresh.splitlines() if line.strip()}
    carried: list[str] = []
    for line in parked_reqs.read_text().splitlines():
        key = _requirement_key(line)
        if line.strip() and key not in seen:
            carried.append(line)
            seen.add(key)
    if carried:
        shared_reqs.write_text("\n".join(carried) + "\n" + fresh.lstrip("\n"))
    parked_reqs.unlink()


def resolve_sources_dir(project_root: Path) -> Path:
    """Where downloaded source code and _run.py shims live for this project.

    A project with its own `.venv` gets its own project-local sources
    directory; a project without one keeps resolving from the shared global
    location, so nothing already downloaded there stops working.
    """
    if venv_path(project_root).exists():
        return project_root / ".tycoon" / "sources"
    return SOURCES_DIR


# Per-source shim: imports from the dlt-init'd package, maps tycoon config keys
# to the dlt source function's parameters, and exposes run_pipeline().
_SHIMS: dict[str, str] = {
    "github": """\
from __future__ import annotations
from pathlib import Path
from typing import Any
import dlt
from github import github_reactions

def run_pipeline(name, source_config, raw_db_path, max_records=None):
    cfg = source_config.config
    source = github_reactions(
        owner=cfg.get("owner", ""),
        name=cfg.get("repo", ""),
        access_token=cfg.get("access_token", ""),
    )
    if max_records:
        source = source.add_limit(max_records)
    pipeline = dlt.pipeline(
        pipeline_name=name,
        destination=dlt.destinations.duckdb(str(raw_db_path)),
        dataset_name=source_config.schema_name,
    )
    return pipeline, pipeline.run(source)
""",
    "slack": """\
from __future__ import annotations
from pathlib import Path
from typing import Any
import dlt
from slack_source import slack_source

def run_pipeline(name, source_config, raw_db_path, max_records=None):
    cfg = source_config.config
    channel_ids = cfg.get("channel_ids", "")
    channels = [c.strip() for c in channel_ids.split(",") if c.strip()] or None
    source = slack_source(
        access_token=cfg.get("access_token", ""),
        channels=channels,
    )
    if max_records:
        source = source.add_limit(max_records)
    pipeline = dlt.pipeline(
        pipeline_name=name,
        destination=dlt.destinations.duckdb(str(raw_db_path)),
        dataset_name=source_config.schema_name,
    )
    return pipeline, pipeline.run(source)
""",
    "stripe_analytics": """\
from __future__ import annotations
from pathlib import Path
from typing import Any
import dlt
from stripe_analytics import stripe_source

def run_pipeline(name, source_config, raw_db_path, max_records=None):
    cfg = source_config.config
    source = stripe_source(
        stripe_secret_key=cfg.get("stripe_secret_key", ""),
    )
    if max_records:
        source = source.add_limit(max_records)
    pipeline = dlt.pipeline(
        pipeline_name=name,
        destination=dlt.destinations.duckdb(str(raw_db_path)),
        dataset_name=source_config.schema_name,
    )
    return pipeline, pipeline.run(source)
""",
    "hubspot": """\
from __future__ import annotations
from pathlib import Path
from typing import Any
import dlt
from hubspot import hubspot

def run_pipeline(name, source_config, raw_db_path, max_records=None):
    cfg = source_config.config
    source = hubspot(api_key=cfg.get("api_key", ""))
    if max_records:
        source = source.add_limit(max_records)
    pipeline = dlt.pipeline(
        pipeline_name=name,
        destination=dlt.destinations.duckdb(str(raw_db_path)),
        dataset_name=source_config.schema_name,
    )
    return pipeline, pipeline.run(source)
""",
    "notion": """\
from __future__ import annotations
from pathlib import Path
from typing import Any
import dlt
from notion import notion_databases

def run_pipeline(name, source_config, raw_db_path, max_records=None):
    cfg = source_config.config
    raw_ids = cfg.get("database_ids", "")
    database_ids = [d.strip() for d in raw_ids.split(",") if d.strip()] or None
    source = notion_databases(
        database_ids=database_ids,
        api_key=cfg.get("api_key", ""),
    )
    if max_records:
        source = source.add_limit(max_records)
    pipeline = dlt.pipeline(
        pipeline_name=name,
        destination=dlt.destinations.duckdb(str(raw_db_path)),
        dataset_name=source_config.schema_name,
    )
    return pipeline, pipeline.run(source)
""",
    "google_sheets": """\
from __future__ import annotations
import json
from pathlib import Path
from typing import Any
import dlt
from google_sheets import google_spreadsheet

def run_pipeline(name, source_config, raw_db_path, max_records=None):
    cfg = source_config.config
    spreadsheet = cfg.get("spreadsheet_url_or_id", "")
    raw_ranges = cfg.get("range_names", "")
    range_names = [r.strip() for r in raw_ranges.split(",") if r.strip()] or None

    # Service-account key: read the JSON and hand dlt the parsed dict, which it
    # coerces into GcpServiceAccountCredentials. If the path is empty/missing we
    # pass nothing, letting dlt fall back to its own resolution (env / secrets).
    kwargs: dict[str, Any] = {"spreadsheet_url_or_id": spreadsheet}
    if range_names:
        kwargs["range_names"] = range_names
    creds_path = cfg.get("credentials_path", "")
    if creds_path:
        key_file = Path(creds_path).expanduser()
        if key_file.is_file():
            kwargs["credentials"] = json.loads(key_file.read_text(encoding="utf-8"))

    source = google_spreadsheet(**kwargs)
    if max_records:
        source = source.add_limit(max_records)
    pipeline = dlt.pipeline(
        pipeline_name=name,
        destination=dlt.destinations.duckdb(str(raw_db_path)),
        dataset_name=source_config.schema_name,
    )
    return pipeline, pipeline.run(source)
""",
    "rest_api": """\
from __future__ import annotations
from typing import Any
import dlt
from dlt.sources.rest_api import rest_api_source

def run_pipeline(name, source_config, raw_db_path, max_records=None):
    cfg = source_config.config
    base_url = cfg.get("base_url", "https://pokeapi.co/api/v2/")
    raw_resources = cfg.get("resources", "pokemon,berry,type")
    resource_names = [r.strip() for r in raw_resources.split(",") if r.strip()]
    source = rest_api_source({
        "client": {"base_url": base_url},
        "resources": resource_names,
    })
    if max_records:
        source = source.add_limit(max_records)
    pipeline = dlt.pipeline(
        pipeline_name=name,
        destination=dlt.destinations.duckdb(str(raw_db_path)),
        dataset_name=source_config.schema_name,
    )
    return pipeline, pipeline.run(source)
""",
}

# Sources that ship with dlt itself — no `dlt init` needed.
#
# filesystem is intentionally absent: unlike rest_api, it never reaches this
# shim-and-catalog-dispatch path at all (runner.py's _NATIVE_BUILDERS always
# takes precedence over CATALOG for it), and _maybe_install_catalog_source
# skips it for the same reason. It used to have its own shim here with
# different defaults (write_disposition left at dlt's default "append"
# rather than tycoon's "replace" convention, and a different table-naming
# heuristic) that could never actually run. Issue #227.
_BUILTIN_SOURCES: set[str] = {"rest_api"}

# Maps catalog source type → dlt init source name (they sometimes differ)
_DLT_INIT_NAME: dict[str, str] = {
    "github": "github",
    "slack": "slack",
    "stripe": "stripe_analytics",
    "hubspot": "hubspot",
    "notion": "notion",
    "google_sheets": "google_sheets",
}


def is_source_installed(source_type: str, sources_dir: Path = SOURCES_DIR) -> bool:
    """Return True if the source package AND its _run.py shim are both present."""
    if source_type in _BUILTIN_SOURCES:
        return (sources_dir / source_type / "_run.py").exists()
    dlt_name = _DLT_INIT_NAME.get(source_type, source_type)
    source_pkg = sources_dir / dlt_name
    return source_pkg.is_dir() and (source_pkg / "__init__.py").exists() and (source_pkg / "_run.py").exists()


def install_source(source_type: str, sources_dir: Path = SOURCES_DIR) -> bool:
    """Install a source and write its _run.py shim.

    For built-in dlt sources (rest_api) this just writes the shim.
    For verified sources it runs `dlt init <source> duckdb` only if the package
    isn't already present, then always writes the _run.py shim.

    Returns True on success, False on failure.
    """
    sources_dir.mkdir(parents=True, exist_ok=True)

    if source_type in _BUILTIN_SOURCES:
        shim = _SHIMS.get(source_type)
        if shim:
            shim_dir = sources_dir / source_type
            shim_dir.mkdir(exist_ok=True)
            (shim_dir / "_run.py").write_text(shim)
        return True

    dlt_name = _DLT_INIT_NAME.get(source_type, source_type)
    source_pkg = sources_dir / dlt_name

    # Only run `dlt init` if the package isn't already downloaded.
    # Re-running dlt init with captured stdin on an existing package can fail
    # when dlt prompts "overwrite?" with no tty to answer.
    if not (source_pkg.is_dir() and (source_pkg / "__init__.py").exists()):
        info(
            f"Downloading verified source '{dlt_name}' from dlt-hub/verified-sources "
            f"(github.com) into {sources_dir}. This code runs during ingestion."
        )
        # dlt init writes <sources_dir>/requirements.txt only when the dir
        # has no dependency system at all (neither pyproject.toml nor
        # requirements.txt), so the first source's file used to make every
        # later `dlt init` skip writing requirements entirely: tycoon then
        # re-installed the first source's deps and the new source's own
        # were never recorded or installed (gh-364). Park the shared file
        # while dlt init runs, so dlt writes THIS source's requirements
        # fresh, then merge the parked lines back: the shared file ends up
        # the union of every source added so far.
        shared_reqs = sources_dir / "requirements.txt"
        parked_reqs = sources_dir / _PARKED_REQUIREMENTS_NAME
        # A run killed anywhere between parking and merging leaves the
        # parked file behind, possibly NEXT TO a fresh shared file (dlt
        # writes it before the finally runs). The merge handles every
        # shape: no parked file is a no-op, parked alone moves back, and
        # both existing union, so no recorded line is ever lost
        # (gh-364 review).
        _merge_parked_requirements(shared_reqs, parked_reqs)
        if shared_reqs.exists():
            shared_reqs.replace(parked_reqs)
        try:
            try:
                result = subprocess.run(
                    [sys.executable, "-m", "dlt", "init", dlt_name, "duckdb"],
                    cwd=sources_dir,
                    capture_output=True,
                    text=True,
                    timeout=_DLT_INIT_TIMEOUT,
                )
            except (subprocess.TimeoutExpired, OSError) as exc:
                # A network that accepts connections but never answers (a
                # captive portal, a dead proxy) hits the timeout instead of
                # exiting; unhandled, this crashed with a raw traceback
                # instead of returning False like every other failure here
                # (gh-272 re-review).
                reason = (
                    f"timed out after {_DLT_INIT_TIMEOUT}s" if isinstance(exc, subprocess.TimeoutExpired) else str(exc)
                )
                warn(f"`dlt init {dlt_name}` {reason}.")
                return False
            # A network failure or other partial run can exit 0 without ever
            # writing the package: the exit code alone isn't proof the
            # package is actually there to write the shim into (gh-272
            # review).
            if result.returncode != 0 or not (source_pkg.is_dir() and (source_pkg / "__init__.py").exists()):
                # Surface dlt's own reason ("Failed to connect...") rather
                # than swallowing it: the caller only knows the download
                # failed, not why (gh-272 re-review).
                detail = (result.stderr or result.stdout or "").strip()
                if detail:
                    warn(f"`dlt init {dlt_name}` failed: {detail.splitlines()[-1]}")
                return False
        finally:
            # Runs on success, failure and timeout alike: whatever dlt did,
            # the shared file must come back containing every previously
            # recorded line (gh-364).
            _merge_parked_requirements(shared_reqs, parked_reqs)

    # Always (re)write the shim — idempotent.
    shim = _SHIMS.get(dlt_name)
    if shim:
        shim_path = source_pkg / "_run.py"
        shim_path.write_text(shim)

    return True


def source_package_dir(source_type: str, sources_dir: Path) -> Path:
    """The directory a source's package and _run.py shim live in."""
    if source_type in _BUILTIN_SOURCES:
        return sources_dir / source_type
    return sources_dir / _DLT_INIT_NAME.get(source_type, source_type)


def _carry_sources_dir_files(old_dir: Path, new_dir: Path) -> None:
    """Carry what `dlt init` writes at a sources dir's root, not inside a package.

    The `.gitignore` and `.dlt/config.toml` are copied only when `new_dir`
    has none, so nothing the user already has there is overwritten.
    `.dlt/secrets.toml` is never copied: it can hold credentials for every
    source in the shared dir, and tycoon passes credentials from tycoon.yml
    anyway. requirements.txt lines missing from `new_dir`'s copy are
    appended, since `dlt init` only writes that file once per dir and other
    sources may already rely on the project's copy (gh-358).
    """
    for rel in (Path(".gitignore"), Path(".dlt") / "config.toml"):
        src, dst = old_dir / rel, new_dir / rel
        if src.is_file() and not dst.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)

    old_reqs = old_dir / "requirements.txt"
    if not old_reqs.is_file():
        return
    new_reqs = new_dir / "requirements.txt"
    existing = new_reqs.read_text().splitlines() if new_reqs.exists() else []
    have = {line.strip() for line in existing}
    missing = [line for line in old_reqs.read_text().splitlines() if line.strip() and line.strip() not in have]
    if missing:
        new_reqs.write_text("\n".join([*existing, *missing]) + "\n")


def migrate_source(source_type: str, old_dir: Path, new_dir: Path) -> bool:
    """Copy an already-installed source package + shim from old_dir to new_dir.

    A source installed before a project had its own `.venv` lands in the
    shared global directory; once the project gains a `.venv`,
    `resolve_sources_dir` starts pointing at a project-local directory that
    doesn't have it, and the "not installed" check in `_run_catalog` has no
    way to recover without a real copy of what's already on disk. The
    sources dir's requirements.txt, `.gitignore` and `.dlt/config.toml` come
    along too (gh-358). Installing those requirements is the caller's job.

    Returns False if the source isn't present in old_dir to copy from, and
    True without copying anything if new_dir already has its `_run.py`.
    Raises FileExistsError, deleting nothing, if new_dir already has the
    package directory without a `_run.py`, since that may hold the user's
    own files.
    """
    src = source_package_dir(source_type, old_dir)
    if not (src.is_dir() and (src / "_run.py").exists()):
        return False

    dst = source_package_dir(source_type, new_dir)
    if (dst / "_run.py").exists():
        return True
    if dst.exists():
        raise FileExistsError(str(dst))

    new_dir.mkdir(parents=True, exist_ok=True)
    _carry_sources_dir_files(old_dir, new_dir)
    shutil.copytree(src, dst)
    return True


def get_run_module_path(source_type: str) -> str:
    """Return the dotted module path for the _run shim, e.g. 'github._run'."""
    if source_type in _BUILTIN_SOURCES:
        return f"{source_type}._run"
    dlt_name = _DLT_INIT_NAME.get(source_type, source_type)
    return f"{dlt_name}._run"
