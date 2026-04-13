"""Template discovery and project scaffolding.

Discovers bundled templates from the ``src/tycoon/templates/`` directory and
provides helpers to scaffold new tycoon projects -- either blank or from a
named template.
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path

import yaml

from tycoon.project import StackConfig
from tycoon.utils.console import info, success, warn


def _project_relative(tycoon_root: Path, path: Path) -> str:
    """Return a path relative to tycoon_root if possible, else absolute string."""
    try:
        return os.path.relpath(path, start=tycoon_root)
    except ValueError:
        # Different drives on Windows
        return str(path)


# ---------------------------------------------------------------------------
# Template directory resolution
# ---------------------------------------------------------------------------

_TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"


def list_templates() -> list[str]:
    """Return names of available templates.

    Each subdirectory under ``src/tycoon/templates/`` that contains a
    ``tycoon.yml`` file is considered a template.
    """
    if not _TEMPLATES_DIR.is_dir():
        return []
    return sorted(
        d.name
        for d in _TEMPLATES_DIR.iterdir()
        if d.is_dir() and (d / "tycoon.yml").exists()
    )


def get_template_path(name: str) -> Path:
    """Return the path to a template directory.

    Raises ``FileNotFoundError`` if the template does not exist or has no
    ``tycoon.yml``.
    """
    path = _TEMPLATES_DIR / name
    if not path.is_dir() or not (path / "tycoon.yml").exists():
        available = list_templates()
        raise FileNotFoundError(
            f"Template '{name}' not found. "
            f"Available templates: {', '.join(available) or '(none)'}"
        )
    return path


# ---------------------------------------------------------------------------
# Blank project scaffolding
# ---------------------------------------------------------------------------

_RILL_YAML_CONTENT = """\
compiler: rillv1
olap_connector: duckdb
"""

_GITIGNORE_CONTENT = """\
# Tycoon
data/*.duckdb
data/*.duckdb.wal
*.duckdb.wal

# Python
__pycache__/
*.pyc
.venv/

# dbt
dbt_project/target/
dbt_project/dbt_packages/
dbt_project/logs/

# Tycoon AI memory logs
.tycoon/*.log

# OS
.DS_Store
"""


def scaffold_blank_project(
    target: Path,
    name: str,
    stack: StackConfig | None = None,
    existing_dbt_path: str | None = None,
    existing_warehouse_path: str | None = None,
) -> None:
    """Create a minimal tycoon project with an empty ``tycoon.yml``.

    Creates:
    - ``tycoon.yml`` with the given project name and database paths
    - ``data/`` directory
    - ``dbt_project/`` with minimal ``dbt_project.yml`` and ``profiles.yml``
      (skipped when ``existing_dbt_path`` is provided)
    - ``.gitignore``
    """
    from tycoon.project import WarehouseType

    # Resolve database paths based on warehouse type
    if stack and stack.warehouse == WarehouseType.motherduck:
        safe_name = name.replace("-", "_")
        raw_db_path = f"md:{safe_name}_raw"
        warehouse_db_path = f"md:{safe_name}"
    elif existing_warehouse_path:
        raw_db_path = existing_warehouse_path
        warehouse_db_path = existing_warehouse_path
    else:
        raw_db_path = "data/raw.duckdb"
        warehouse_db_path = "data/warehouse.duckdb"

    # Resolve dbt path — may be external, store relative to tycoon.yml
    if existing_dbt_path:
        dbt_abs = Path(existing_dbt_path).resolve()
        dbt_project_dir = _project_relative(target, dbt_abs)
    else:
        dbt_project_dir = "dbt_project"

    # tycoon.yml
    project_data: dict = {
        "name": name,
        "version": "0.1.0",
        "database": {
            "raw": raw_db_path,
            "warehouse": warehouse_db_path,
        },
        "dbt_project_dir": dbt_project_dir,
        "rill_dir": "rill",
        "sources": {},
    }
    if stack:
        project_data["stack"] = {
            "ingestion": stack.ingestion.value,
            "ingestion_managed": stack.ingestion_managed,
            "warehouse": stack.warehouse.value,
            "transformation_managed": stack.transformation_managed,
        }

    yml_path = target / "tycoon.yml"
    yml_path.write_text(yaml.dump(project_data, default_flow_style=False, sort_keys=False))
    success(f"Created {yml_path.relative_to(target)}")

    # data/
    (target / "data").mkdir(parents=True, exist_ok=True)
    info("Created data/")

    # dbt_project/ — scaffold at resolved external path, or skip if existing
    dbt_abs = Path(existing_dbt_path).resolve() if existing_dbt_path else None
    dbt_already_exists = dbt_abs and dbt_abs.exists() and (dbt_abs / "dbt_project.yml").exists()

    if dbt_already_exists:
        info(f"Using existing dbt project at {existing_dbt_path}")
    elif not stack or stack.transformation_managed:
        dbt_dir = dbt_abs if dbt_abs else (target / "dbt_project")
        dbt_dir.mkdir(parents=True, exist_ok=True)

        profile_name = name.replace("-", "_")

        dbt_project_yml = {
            "name": profile_name,
            "version": "1.0.0",
            "config-version": 2,
            "profile": profile_name,
        }
        (dbt_dir / "dbt_project.yml").write_text(
            yaml.dump(dbt_project_yml, default_flow_style=False, sort_keys=False)
        )

        # profiles.yml: warehouse DB is the dbt target; raw DB is attached read-only.
        # Paths are relative from dbt_dir, which may be a sibling of the tycoon root.
        if stack and stack.warehouse == WarehouseType.motherduck:
            profiles_data = {
                profile_name: {
                    "target": "dev",
                    "outputs": {
                        "dev": {
                            "type": "duckdb",
                            "path": warehouse_db_path,
                            "attach": [{"path": raw_db_path, "alias": "raw", "read_only": True}],
                        }
                    },
                }
            }
        else:
            warehouse_abs = (target / warehouse_db_path).resolve()
            raw_abs = (target / raw_db_path).resolve()
            warehouse_rel = os.path.relpath(warehouse_abs, start=dbt_dir)
            raw_rel = os.path.relpath(raw_abs, start=dbt_dir)
            profiles_data = {
                profile_name: {
                    "target": "dev",
                    "outputs": {
                        "dev": {
                            "type": "duckdb",
                            "path": warehouse_rel,
                            "attach": [{"path": raw_rel, "alias": "raw", "read_only": True}],
                        }
                    },
                }
            }

        (dbt_dir / "profiles.yml").write_text(
            yaml.dump(profiles_data, default_flow_style=False, sort_keys=False)
        )
        info(f"Created dbt project at {dbt_dir} with dbt_project.yml and profiles.yml")

    # rill/
    if not stack or stack.bi_managed:
        _scaffold_rill_dir(target)

    # .gitignore
    _write_gitignore(target)


# ---------------------------------------------------------------------------
# Template-based scaffolding
# ---------------------------------------------------------------------------


def scaffold_from_template(target: Path, template_name: str) -> None:
    """Copy a template into the target directory.

    Copies ``tycoon.yml`` from the template. For directories like
    ``dbt_project/`` and ``rill/``, checks whether they already exist in the
    target (e.g. when running inside the localhost-stack repo) and skips if so.

    Also creates ``data/`` and ``.gitignore`` if not present.
    """
    template_path = get_template_path(template_name)

    # Copy tycoon.yml
    src_yml = template_path / "tycoon.yml"
    dst_yml = target / "tycoon.yml"
    if dst_yml.exists():
        warn(f"tycoon.yml already exists, skipping")
    else:
        shutil.copy2(src_yml, dst_yml)
        success(f"Created tycoon.yml from template '{template_name}'")

    # Copy any subdirectories from the template (e.g. dbt_project/, rill/)
    for item in template_path.iterdir():
        if item.name == "tycoon.yml" or item.name == "README":
            continue
        dst = target / item.name
        if item.is_dir():
            if dst.exists():
                warn(f"{item.name}/ already exists, skipping")
            else:
                shutil.copytree(item, dst)
                success(f"Created {item.name}/ from template")
        elif item.is_file():
            if dst.exists():
                warn(f"{item.name} already exists, skipping")
            else:
                shutil.copy2(item, dst)
                success(f"Created {item.name} from template")

    # data/
    (target / "data").mkdir(parents=True, exist_ok=True)
    info("Ensured data/ directory exists")

    # rill/ — scaffold if the template didn't include one
    if not (target / "rill").exists():
        _scaffold_rill_dir(target)

    # .gitignore
    _write_gitignore(target)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write_gitignore(target: Path) -> None:
    """Write ``.gitignore`` if it does not already exist."""
    gitignore = target / ".gitignore"
    if gitignore.exists():
        warn(".gitignore already exists, skipping")
    else:
        gitignore.write_text(_GITIGNORE_CONTENT)
        info("Created .gitignore")


def _scaffold_rill_dir(target: Path) -> None:
    """Create a minimal rill/ project directory with rill.yaml."""
    rill_dir = target / "rill"
    rill_dir.mkdir(exist_ok=True)
    rill_yaml = rill_dir / "rill.yaml"
    if not rill_yaml.exists():
        rill_yaml.write_text(_RILL_YAML_CONTENT)
        info("Created rill/ with rill.yaml")
