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

import secrets
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


def secrets_path(project_root: Path) -> Path:
    return project_root / _SECRETS_REL


def load_token(project_root: Path) -> str | None:
    """Return the persisted Quack token, or None if not set up yet."""
    path = secrets_path(project_root)
    if not path.exists():
        return None
    try:
        data = yaml.safe_load(path.read_text()) or {}
    except yaml.YAMLError:
        return None
    quack = data.get("quack")
    if isinstance(quack, dict):
        token = quack.get("token")
        return token if isinstance(token, str) and token else None
    return None


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
        pass
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
