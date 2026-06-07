"""Service definitions for the Tycoon demo environment."""

from __future__ import annotations

from dataclasses import dataclass, field

from tycoon.config import config
from tycoon.constants import PORTS


@dataclass
class ServiceDef:
    """Describes a managed service that Tycoon can start."""

    name: str
    port: int
    command: list[str]
    health_path: str | None = None
    cwd: str | None = None
    env: dict[str, str] = field(default_factory=dict)


def get_service_definitions() -> list[ServiceDef]:
    """Return the full list of service definitions.

    Built as a function (not a module-level constant) so that ``config``
    paths are resolved at call time rather than import time.
    """
    defs: list[ServiceDef] = [
        ServiceDef(
            name="duckdb_ui",
            port=PORTS["duckdb_ui"],
            command=[
                "duckdb",
                "-cmd",
                "INSTALL ui; LOAD ui; CALL start_ui_server('localhost', 4213);",
                str(config.local_db),
            ],
        ),
        ServiceDef(
            name="dbt_docs",
            port=PORTS["dbt_docs"],
            command=[
                "dbt",
                "docs",
                "serve",
                "--port",
                "8080",
                "--project-dir",
                str(config.dbt_project_dir),
                "--profiles-dir",
                str(config.dbt_project_dir),
            ],
        ),
        ServiceDef(
            name="rill",
            port=PORTS["rill"],
            command=["rill", "start", str(config.rill_dir), "--port", "9009", "--no-open"],
            env={"CONNECTOR_DUCKDB_DSN": str(config.local_db)},
        ),
        ServiceDef(
            name="dagster",
            port=PORTS["dagster"],
            command=["dagster", "dev", "--port", str(PORTS["dagster"])],
            health_path="/server_info",
            env={"DAGSTER_HOME": str(config.root / ".tycoon" / "dagster")},
        ),
        ServiceDef(
            name="nao",
            port=PORTS["nao"],
            command=[
                "python", "-m", "nao_core", "chat",
                "--port", str(PORTS["nao"]),
            ],
            cwd=str(config.nao_dir),
        ),
        ServiceDef(
            name="tycoon",
            port=PORTS["tycoon"],
            command=[
                "uvicorn",
                "tycoon.server.app:create_app",
                "--factory",
                "--host", "0.0.0.0",
                "--port", str(PORTS["tycoon"]),
            ],
            health_path="/health",
        ),
    ]

    # Quack — serve the warehouse over DuckDB's multi-client RPC protocol so
    # `tycoon data query` (and any other local client) can share the *live*
    # warehouse instead of fighting the single-writer file lock. Mirrors the
    # duckdb_ui pattern: a `duckdb` CLI session that CALLs quack_serve and idles
    # in its REPL to stay alive. Only meaningful when a token exists (ensured by
    # `tycoon start` preflight); core_nightly-gated there too.
    from tycoon import quack

    quack_token = quack.load_token(config.root)
    if quack_token:
        defs.append(
            ServiceDef(
                name="quack",
                port=PORTS["quack"],
                command=quack.serve_command(config.local_db, quack_token),
            )
        )

    # Recce is optional — only available when target-base/ exists.
    target_base = config.dbt_project_dir / "target-base"
    if target_base.exists():
        defs.append(
            ServiceDef(
                name="recce",
                port=PORTS["recce"],
                command=["recce", "server", "--port", "8000"],
                cwd=str(config.dbt_project_dir),
            )
        )

    return defs
