"""Read a Tycoon CLI project's pointers off disk — never import the `tycoon`
package.

That is a standing decision, not a shortcut: the CLI is pre-1.0 and drifting
(real `tycoon.yml` files carry `stack.orchestrator` and `ask:` keys its own
pydantic model lacks), `config.py` builds a cwd-bound singleton at import, and
`load_config()` can `SystemExit`. This module reads only the keys it needs, so
drift is tolerated *by construction* — an unknown key is never even looked at.
No `schema_version` requirement, no warnings, no exit paths.
"""

import os
import re
from dataclasses import dataclass
from pathlib import Path

import yaml

TYCOON_FILE = "tycoon.yml"
_ENV_VAR = re.compile(r"\$\{(\w+)\}")


@dataclass(frozen=True)
class TycoonProjectInfo:
    root: Path
    name: str
    warehouse_path: Path
    manifest_path: Path | None  # dbt/target/manifest.json, when it exists
    sources_json_path: Path | None  # dbt/target/sources.json (source freshness)
    metadata_db_path: Path | None  # .tycoon/metadata.duckdb, when it exists
    requests_json_path: Path | None  # requests.json, when it exists


def _interpolate(value: str) -> str:
    """`${VAR}` from the environment, as the CLI does. Unknown variables are
    left as-is rather than erased — a visibly wrong path beats a silently
    truncated one."""
    return _ENV_VAR.sub(lambda m: os.environ.get(m.group(1), m.group(0)), value)


def read_project_info(root: Path | str) -> TycoonProjectInfo | None:
    """The project's pointers, or None when `root` is not a tycoon project.

    Returns None rather than raising for a missing `tycoon.yml`; a present but
    unparseable one raises ValueError, because "this is a tycoon project but
    its config is broken" should not silently degrade into "not a project".
    """
    root = Path(root)
    config_path = root / TYCOON_FILE
    if not config_path.is_file():
        return None

    try:
        data = yaml.safe_load(config_path.read_text()) or {}
    except yaml.YAMLError as exc:
        raise ValueError(f"could not parse {config_path}: {exc}") from exc

    database = data.get("database") or {}
    warehouse = database.get("warehouse")
    if not warehouse:
        raise ValueError(f"{config_path} has no database.warehouse")
    warehouse_path = root / _interpolate(str(warehouse))

    manifest_path: Path | None = None
    sources_json_path: Path | None = None
    dbt_dir = data.get("dbt_project_dir")
    if dbt_dir:
        target = root / _interpolate(str(dbt_dir)) / "target"
        manifest_path = (target / "manifest.json") if (target / "manifest.json").is_file() else None
        sources_json_path = (target / "sources.json") if (target / "sources.json").is_file() else None

    metadata_cfg = data.get("metadata") or {}
    meta_path_str = metadata_cfg.get("path") if isinstance(metadata_cfg, dict) else None
    if meta_path_str:
        metadata = root / _interpolate(str(meta_path_str))
    else:
        metadata = root / ".tycoon" / "metadata.duckdb"
    requests = root / "requests.json"

    return TycoonProjectInfo(
        root=root,
        name=str(data.get("name") or root.name),
        warehouse_path=warehouse_path,
        manifest_path=manifest_path,
        sources_json_path=sources_json_path,
        metadata_db_path=metadata if metadata.is_file() else None,
        requests_json_path=requests if requests.is_file() else None,
    )
