"""DuckDB Quack protocol integration (#42) — multi-client local DuckDB.

Quack (announced 2026-05-12, currently shipping in DuckDB's ``core_nightly``)
turns a DuckDB file into a multi-client server over a local RPC protocol. Today
every consumer of tycoon's warehouse opens the ``.duckdb`` file in-process,
which takes an exclusive lock — only one process at a time. Quack removes that
constraint while staying entirely on ``localhost``, which fits tycoon's
local-first ethos.

This module holds the protocol glue: token lifecycle (persisted once in the
gitignored ``.tycoon/secrets.yml``), the SQL strings for serving and attaching,
and a client helper that opens a Quack-backed connection. The server itself is
run as a managed service (see ``services/definitions.py`` — it mirrors the
``duckdb_ui`` service: a ``duckdb`` CLI session that ``CALL quack_serve(...)``
and stays alive).

Quack is **opt-in** and ``core_nightly``-only for now; the default warehouse
path stays in-process until the extension reaches ``core``.
"""

from __future__ import annotations

import re
import secrets
import stat
from pathlib import Path

import yaml

from tycoon.constants import PORTS
from tycoon.utils.process import is_port_in_use

# The server binds this URI; Quack's default port is 9494.
QUACK_HOST = "localhost"
QUACK_URI = f"quack:{QUACK_HOST}"
QUACK_PORT = PORTS["quack"]

# Token lives here, beside the rest of tycoon's per-project state. Gitignored
# via the existing ``.tycoon/`` ignore (ensured by `ensure_token`).
_SECRETS_REL = Path(".tycoon") / "secrets.yml"

# Quack ships in core_nightly only (verified on duckdb 1.5.2); pin the source so
# the install instruction is correct everywhere.
_LOAD_QUACK = "INSTALL quack FROM core_nightly; LOAD quack;"

# `secrets.token_urlsafe` only ever emits these characters. The token is
# interpolated into SQL string literals (`serve_command` / `connect`), so a
# token carrying a quote char is never legitimate — it's a tampered
# secrets.yml attempting SQL injection. Validate on load (#66).
_TOKEN_RE = re.compile(r"^[A-Za-z0-9_-]+$")


class QuackTokenError(RuntimeError):
    """Raised when ``.tycoon/secrets.yml`` holds a malformed Quack token."""


def secrets_path(project_root: Path) -> Path:
    return project_root / _SECRETS_REL


def _tighten_permissions(path: Path) -> None:
    """Clamp the secrets file to owner-only (0600).

    Fixes files created before the permission hardening (#66): any group/other
    bit lets another local user read the token and connect to the warehouse.
    """
    try:
        if stat.S_IMODE(path.stat().st_mode) != 0o600:
            path.chmod(0o600)
    except OSError:
        pass  # Best-effort on filesystems without POSIX modes.


def load_token(project_root: Path) -> str | None:
    """Return the persisted Quack token, or None if not set up yet.

    Raises QuackTokenError if a token is present but malformed — it would be
    interpolated into SQL string literals, so it must never be used.
    """
    path = secrets_path(project_root)
    if not path.exists():
        return None
    _tighten_permissions(path)
    try:
        data = yaml.safe_load(path.read_text()) or {}
    except yaml.YAMLError:
        return None
    quack = data.get("quack")
    if not isinstance(quack, dict):
        return None
    token = quack.get("token")
    if not isinstance(token, str):
        return None
    if not _TOKEN_RE.match(token):
        raise QuackTokenError(
            f"Malformed Quack token in {path}: expected URL-safe characters only "
            "([A-Za-z0-9_-]). Delete the 'quack' entry from that file and rerun "
            "`tycoon start` to generate a fresh token."
        )
    return token


def generate_token() -> str:
    """A fresh URL-safe token (no quoting hazards in SQL string literals)."""
    return secrets.token_urlsafe(32)


def ensure_token(project_root: Path) -> str:
    """Return the project's Quack token, generating + persisting one if absent.

    Idempotent: an existing token is returned untouched. The first call writes
    ``.tycoon/secrets.yml`` (preserving any other keys already there) and makes
    sure ``.tycoon/`` is gitignored so the token never lands in version control.
    """
    existing = load_token(project_root)
    if existing:
        return existing

    token = generate_token()
    path = secrets_path(project_root)
    path.parent.mkdir(parents=True, exist_ok=True)

    data: dict = {}
    if path.exists():
        try:
            data = yaml.safe_load(path.read_text()) or {}
        except yaml.YAMLError:
            data = {}
    data.setdefault("quack", {})["token"] = token
    # Owner-only *before* the token lands on disk: with default modes (0644)
    # any other local user could read it and connect to the served warehouse.
    path.touch(mode=0o600)
    path.chmod(0o600)  # touch() leaves the mode of a pre-existing file alone
    path.write_text(yaml.safe_dump(data, default_flow_style=False, sort_keys=False))

    _ensure_gitignored(project_root)
    return token


def _ensure_gitignored(project_root: Path) -> None:
    """Make sure ``.tycoon/`` is in the project's .gitignore (best-effort)."""
    gitignore = project_root / ".gitignore"
    entry = ".tycoon/"
    try:
        lines = gitignore.read_text().splitlines() if gitignore.exists() else []
        if any(line.strip().rstrip("/") == ".tycoon" for line in lines):
            return
        with gitignore.open("a") as fh:
            if lines and lines[-1].strip():
                fh.write("\n")
            fh.write(f"{entry}\n")
    except OSError:
        pass  # Never block on .gitignore hygiene.


def is_server_running(port: int = QUACK_PORT) -> bool:
    """True if something is listening on the Quack port."""
    return is_port_in_use(port)


def extension_available() -> bool:
    """True if the ``duckdb`` CLI can install + load the Quack extension.

    Quack is ``core_nightly``-only, so this gates folding the warehouse server
    into ``tycoon start``: on machines where the extension can't load we skip it
    silently rather than spamming "port not responding". Run once per start
    (infrequent, interactive); the install is cached after the first call.
    """
    import shutil
    import subprocess

    if shutil.which("duckdb") is None:
        return False
    # Try a plain LOAD first: if the extension is already cached locally this
    # succeeds offline and skips the network round-trip that INSTALL ... FROM
    # core_nightly always makes.
    try:
        loaded = subprocess.run(
            ["duckdb", "-c", "LOAD quack;"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if loaded.returncode == 0:
            return True
    except (subprocess.TimeoutExpired, OSError):
        # A timeout or OS-level failure on a plain LOAD (the binary already
        # exists — we checked `which` above) means duckdb is hanging or
        # unusable; the 60s INSTALL would hit the same wall. Quack is opt-in
        # with graceful fallback, so fail fast rather than cascade.
        return False
    try:
        result = subprocess.run(
            ["duckdb", "-c", _LOAD_QUACK],
            capture_output=True,
            text=True,
            timeout=60,
        )
    except (subprocess.TimeoutExpired, OSError):
        return False
    return result.returncode == 0


def serve_command(db_path: Path, token: str) -> list[str]:
    """The ``duckdb`` CLI argv that serves ``db_path`` over Quack.

    Mirrors the ``duckdb_ui`` service: a ``-cmd`` that loads the extension and
    starts the server, followed by the DB path so the served database *is* the
    warehouse. The CLI then idles in its REPL, keeping the process — and the
    background server thread — alive until the service is stopped.
    """
    serve_sql = f"{_LOAD_QUACK} CALL quack_serve('{QUACK_URI}', token => '{token}');"
    return ["duckdb", "-cmd", serve_sql, str(db_path)]


def connect(token: str, alias: str = "warehouse"):
    """Open an in-process DuckDB connection attached to the Quack server.

    The remote database is attached as ``alias`` and made the default catalog
    (``USE``) so a caller's unqualified SQL resolves against it — letting
    ``tycoon data query`` transparently route through Quack when the server is
    up instead of fighting the file lock.
    """
    import duckdb

    con = duckdb.connect()
    con.execute(_LOAD_QUACK)
    con.execute(f"CREATE SECRET (TYPE quack, TOKEN '{token}');")
    con.execute(f"ATTACH '{QUACK_URI}' AS {alias};")
    con.execute(f"USE {alias};")
    return con
