"""Template discovery and project scaffolding.

Discovers bundled templates from the ``src/tycoon/templates/`` directory and
provides helpers to scaffold new tycoon projects -- either blank or from a
named template.
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path

import typer
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

# Tycoon observability — dlt + dbt run-history metadata DB (disposable)
.tycoon/metadata.duckdb*

# Nao (AI agent) — chat SQLite and per-project sync artifacts
.tycoon/nao/db.sqlite*
.tycoon/nao/databases/
.tycoon/nao/repos/

# OS
.DS_Store
"""


def scaffold_blank_project(
    target: Path,
    name: str,
    stack: StackConfig | None = None,
    existing_dbt_path: str | None = None,
    existing_warehouse_path: str | None = None,
    existing_rill_path: str | None = None,
) -> None:
    """Create a minimal tycoon project with a ``tycoon.yml`` and supporting dirs.

    Behavior flexes by ``stack`` settings:
    - ``stack.transformation == none`` → don't scaffold or record dbt at all.
    - ``stack.transformation == dbt`` + ``transformation_managed`` → scaffold
      dbt project at ``existing_dbt_path`` (or target/dbt_project).
    - ``stack.transformation == dbt`` + not managed → just record the path.
    - ``stack.bi == rill`` + ``bi_managed`` → scaffold Rill dir.
    - ``stack.bi == rill`` + not managed → record the path only.
    - ``stack.bi == none`` → don't scaffold or record Rill.
    """
    from tycoon.project import BITool, TransformationTool, WarehouseType

    transformation = stack.transformation if stack else TransformationTool.dbt
    bi = stack.bi if stack else BITool.rill

    # ---- Warehouse resolution ----
    if stack and stack.warehouse == WarehouseType.motherduck:
        safe_name = name.replace("-", "_")
        raw_db_path = f"md:{safe_name}_raw"
        warehouse_db_path = f"md:{safe_name}"
    elif existing_warehouse_path:
        warehouse_db_path = existing_warehouse_path
        # Keep raw distinct from warehouse: dbt-duckdb's profile attaches the
        # raw DB read-only alongside the warehouse, and duckdb rejects a
        # same-file double-attach with a "Unique file handle conflict" error.
        warehouse_path_obj = Path(warehouse_db_path)
        if warehouse_path_obj.name == "raw.duckdb":
            raw_db_path = str(warehouse_path_obj.with_name("raw_source.duckdb"))
        else:
            raw_db_path = str(warehouse_path_obj.with_name("raw.duckdb"))
    else:
        raw_db_path = "data/raw.duckdb"
        warehouse_db_path = "data/warehouse.duckdb"

    # ---- tycoon.yml data ----
    project_data: dict = {
        "name": name,
        "version": "0.1.0",
        "database": {
            "raw": raw_db_path,
            "warehouse": warehouse_db_path,
        },
        "sources": {},
    }

    # dbt path — only record if dbt is active
    if transformation == TransformationTool.dbt and existing_dbt_path:
        dbt_abs = Path(existing_dbt_path).resolve()
        project_data["dbt_project_dir"] = _project_relative(target, dbt_abs)
    elif transformation == TransformationTool.dbt:
        project_data["dbt_project_dir"] = "dbt_project"

    # rill path — only record if Rill is active
    if bi == BITool.rill and existing_rill_path:
        rill_abs = Path(existing_rill_path).resolve()
        project_data["rill_dir"] = _project_relative(target, rill_abs)
    elif bi == BITool.rill:
        project_data["rill_dir"] = "rill"

    if stack:
        project_data["stack"] = {
            "ingestion": stack.ingestion.value,
            "ingestion_managed": stack.ingestion_managed,
            "warehouse": stack.warehouse.value,
            "transformation": stack.transformation.value,
            "transformation_managed": stack.transformation_managed,
            "bi": stack.bi.value,
            "bi_managed": stack.bi_managed,
            "orchestrator": stack.orchestrator.value,
            "orchestrator_managed": stack.orchestrator_managed,
        }

    yml_path = target / "tycoon.yml"
    yml_path.write_text(yaml.dump(project_data, default_flow_style=False, sort_keys=False))
    success(f"Created {yml_path.relative_to(target)}")

    # ---- data/ ----
    (target / "data").mkdir(parents=True, exist_ok=True)
    info("Created data/")

    # ---- dbt scaffold (if active, managed, and project doesn't already exist) ----
    if transformation == TransformationTool.dbt:
        dbt_abs = Path(existing_dbt_path).resolve() if existing_dbt_path else (target / "dbt_project")
        dbt_already_exists = dbt_abs.exists() and (dbt_abs / "dbt_project.yml").exists()

        if dbt_already_exists:
            info(f"Using existing dbt project at {dbt_abs}")
        elif stack is None or stack.transformation_managed:
            _scaffold_dbt_project(
                dbt_dir=dbt_abs,
                name=name,
                warehouse=stack.warehouse if stack else WarehouseType.duckdb,
                warehouse_db_path=warehouse_db_path,
                raw_db_path=raw_db_path,
                target=target,
            )

    # ---- Rill scaffold (if active and managed) ----
    if bi == BITool.rill:
        rill_abs = Path(existing_rill_path).resolve() if existing_rill_path else (target / "rill")
        rill_already_exists = rill_abs.exists() and (rill_abs / "rill.yaml").exists()
        if rill_already_exists:
            info(f"Using existing Rill project at {rill_abs}")
        elif stack is None or stack.bi_managed:
            scaffold_rill_dir(rill_abs)

    # ---- .gitignore ----
    _write_gitignore(target)


def _scaffold_dbt_project(
    dbt_dir: Path,
    name: str,
    warehouse,
    warehouse_db_path: str,
    raw_db_path: str,
    target: Path,
) -> None:
    """Write dbt_project.yml + profiles.yml into ``dbt_dir``."""
    from tycoon.project import WarehouseType

    dbt_dir.mkdir(parents=True, exist_ok=True)
    profile_name = name.replace("-", "_")

    (dbt_dir / "dbt_project.yml").write_text(
        yaml.dump(
            {
                "name": profile_name,
                "version": "1.0.0",
                "config-version": 2,
                "profile": profile_name,
            },
            default_flow_style=False,
            sort_keys=False,
        )
    )

    # Compute the metadata DB path relative to the dbt project — same shape
    # as the raw / warehouse paths. Pre-create the metadata DB with the
    # empty observability schema so the first `dbt run` doesn't fail on
    # ATTACH.
    metadata_abs = (target / ".tycoon" / "metadata.duckdb").resolve()
    metadata_rel_for_dbt = os.path.relpath(metadata_abs, start=dbt_dir)
    try:
        from tycoon.observability import ensure_schema
        ensure_schema(metadata_abs)
    except Exception:
        # Best-effort — observability scaffolding shouldn't block project setup.
        pass

    metadata_attach = {
        "path": metadata_rel_for_dbt,
        "alias": "tycoon_meta",
        "read_only": True,
    }

    if warehouse == WarehouseType.motherduck:
        profiles_data = {
            profile_name: {
                "target": "dev",
                "outputs": {
                    "dev": {
                        "type": "duckdb",
                        "path": warehouse_db_path,
                        "attach": [
                            {"path": raw_db_path, "alias": "raw", "read_only": True},
                            metadata_attach,
                        ],
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
                        "attach": [
                            {"path": raw_rel, "alias": "raw", "read_only": True},
                            metadata_attach,
                        ],
                    }
                },
            }
        }

    (dbt_dir / "profiles.yml").write_text(
        yaml.dump(profiles_data, default_flow_style=False, sort_keys=False)
    )
    info(f"Created dbt project at {dbt_dir} with dbt_project.yml and profiles.yml")

    # Generate the _tycoon staging models so users have a working dbt
    # surface over the metadata from the very first run.
    try:
        from tycoon.scaffolding.observability_dbt import scaffold_observability_models
        scaffold_observability_models(dbt_dir)
    except Exception:
        # Best-effort — observability scaffolding shouldn't block project setup.
        pass


# ---------------------------------------------------------------------------
# Template parameterization
# ---------------------------------------------------------------------------

# Metadata file sibling to tycoon.yml inside each template directory.
# Declares parameters the template exposes for scaffold-time substitution.
# Format:
#
#   parameters:
#     - name: owner
#       description: GitHub username or organization
#       example: octocat
#       required: true
#     - name: repo
#       description: Repository name
#       example: hello-world
#       required: true
#
# Placeholders in any template file are written as ``{{ name }}`` (with
# optional whitespace). Substitution happens at scaffold time — once the
# project is written, the values are fixed and the declaration is gone.
_TEMPLATE_METADATA_FILENAME = "template.yml"

# Files (relative to the template root) whose contents get parameter
# substitution applied. Kept small and explicit rather than "everything"
# so scaffolding can't accidentally mangle binary or unrelated files.
_SUBSTITUTABLE_SUFFIXES = {".yml", ".yaml", ".sql", ".md", ".txt"}


def load_template_parameters(template_name: str) -> list[dict]:
    """Return the parameter declarations for a template, or [] if none.

    Parameters are declared in the template's ``template.yml`` metadata
    file. Each entry is a dict with keys: ``name``, ``description``,
    ``example`` (optional), ``required`` (optional, default True).
    """
    template_path = get_template_path(template_name)
    meta_path = template_path / _TEMPLATE_METADATA_FILENAME
    if not meta_path.exists():
        return []

    try:
        data = yaml.safe_load(meta_path.read_text()) or {}
    except yaml.YAMLError as exc:
        raise ValueError(f"Invalid YAML in {meta_path}: {exc}") from exc

    params = data.get("parameters", []) or []
    if not isinstance(params, list):
        raise ValueError(
            f"{meta_path}: 'parameters' must be a list, got {type(params).__name__}"
        )

    normalized: list[dict] = []
    for i, entry in enumerate(params):
        if not isinstance(entry, dict) or "name" not in entry:
            raise ValueError(
                f"{meta_path}: parameters[{i}] must be a dict with a 'name' key"
            )
        normalized.append(
            {
                "name": entry["name"],
                "description": entry.get("description", ""),
                "example": entry.get("example", ""),
                "required": entry.get("required", True),
            }
        )
    return normalized


def _substitute_params(text: str, params: dict[str, str]) -> str:
    """Replace every ``{{ name }}`` occurrence (with optional whitespace)
    with the corresponding value from ``params``.

    Unknown placeholders are left untouched — templates may intentionally
    contain literal ``{{ ... }}`` (e.g. dbt Jinja references inside SQL).
    Callers should validate that all declared parameters were supplied
    before invoking this function.
    """
    import re

    def replace(match: re.Match) -> str:
        key = match.group(1).strip()
        return params.get(key, match.group(0))

    return re.sub(r"\{\{\s*([A-Za-z_][A-Za-z0-9_]*)\s*\}\}", replace, text)


def _substitute_tree(target: Path, params: dict[str, str]) -> None:
    """Walk ``target`` and substitute ``{{ name }}`` placeholders in every
    text file with an allowlisted suffix. Files without those suffixes
    (binary images, data blobs, etc.) are skipped."""
    if not params:
        return
    for path in target.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() not in _SUBSTITUTABLE_SUFFIXES:
            continue
        try:
            original = path.read_text()
        except (OSError, UnicodeDecodeError):
            continue
        rewritten = _substitute_params(original, params)
        if rewritten != original:
            path.write_text(rewritten)


def _resolve_template_parameters(
    template_name: str,
    supplied: dict[str, str] | None,
) -> dict[str, str]:
    """Return the concrete parameter values for a template.

    For each declared parameter:
    * If the name appears in ``supplied`` — use it verbatim.
    * Otherwise — prompt the user interactively with the example as
      the default hint (typer.prompt). Required params block; optional
      params allow an empty answer that's skipped in substitution.

    Extra keys in ``supplied`` that don't match any declared parameter
    are ignored (with a warning) — users typo things.
    """
    declared = load_template_parameters(template_name)
    if not declared:
        if supplied:
            warn(
                f"Template '{template_name}' does not declare any parameters; "
                f"ignoring --param: {', '.join(supplied)}"
            )
        return {}

    supplied = dict(supplied or {})
    resolved: dict[str, str] = {}

    declared_names = {d["name"] for d in declared}
    for key in list(supplied):
        if key not in declared_names:
            warn(f"Ignoring unknown parameter '{key}' (not declared by template)")
            supplied.pop(key)

    for spec in declared:
        name = spec["name"]
        if name in supplied:
            resolved[name] = supplied[name]
            continue

        prompt_label = spec["name"]
        if spec["description"]:
            prompt_label = f"{spec['description']} ({name})"
        default = spec["example"] if not spec["required"] else None

        if default is None:
            value = typer.prompt(prompt_label)
        else:
            value = typer.prompt(prompt_label, default=default, show_default=True)

        if spec["required"] and not value:
            raise ValueError(f"Required parameter '{name}' was not supplied")

        resolved[name] = str(value)

    return resolved


# ---------------------------------------------------------------------------
# Template-based scaffolding
# ---------------------------------------------------------------------------


def scaffold_from_template(
    target: Path,
    template_name: str,
    parameters: dict[str, str] | None = None,
) -> None:
    """Copy a template into the target directory.

    Copies ``tycoon.yml`` from the template. For directories like
    ``dbt_project/`` and ``rill/``, checks whether they already exist in the
    target (e.g. when running inside the localhost-stack repo) and skips if so.

    Also creates ``data/`` and ``.gitignore`` if not present.

    If the template declares parameters in ``template.yml`` (see
    :func:`load_template_parameters`), missing values are prompted for
    interactively. ``{{ name }}`` placeholders in text files with
    allowlisted suffixes (``.yml/.yaml/.sql/.md/.txt``) are then replaced
    with the resolved values.
    """
    template_path = get_template_path(template_name)

    # Resolve parameter values before copying anything so a prompt
    # failure doesn't leave a half-scaffolded project behind.
    resolved_params = _resolve_template_parameters(template_name, parameters)

    # Copy tycoon.yml
    src_yml = template_path / "tycoon.yml"
    dst_yml = target / "tycoon.yml"
    if dst_yml.exists():
        warn("tycoon.yml already exists, skipping")
    else:
        shutil.copy2(src_yml, dst_yml)
        success(f"Created tycoon.yml from template '{template_name}'")

    # Copy any subdirectories from the template (e.g. dbt_project/, rill/)
    # The template.yml metadata file itself is not copied into the target —
    # it's build-time metadata, not runtime config.
    for item in template_path.iterdir():
        if item.name in ("tycoon.yml", "README", _TEMPLATE_METADATA_FILENAME):
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

    # Substitute parameters across everything we just copied.
    _substitute_tree(target, resolved_params)

    # data/
    (target / "data").mkdir(parents=True, exist_ok=True)
    info("Ensured data/ directory exists")

    # rill/ — scaffold if the template didn't include one
    if not (target / "rill").exists():
        scaffold_rill_dir(target / "rill")

    # .gitignore
    _write_gitignore(target)

    # Ensure .tycoon/metadata.duckdb exists with the empty observability
    # schema so any dbt profile that ATTACHes it (csv-import does, by
    # default) doesn't fail on the very first `dbt run`. Best-effort —
    # observability bookkeeping should never block project setup.
    try:
        from tycoon.observability import ensure_schema
        ensure_schema(target / ".tycoon" / "metadata.duckdb")
    except Exception:
        pass

    # Generate _tycoon staging models if the template ships a dbt project
    # but didn't pre-include them. Idempotent — overwrites the
    # auto-generated files only.
    template_dbt = target / "dbt_project"
    if template_dbt.exists() and (template_dbt / "dbt_project.yml").exists():
        try:
            from tycoon.scaffolding.observability_dbt import scaffold_observability_models
            scaffold_observability_models(template_dbt)
        except Exception:
            pass


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


def scaffold_rill_dir(rill_dir: Path) -> None:
    """Create a minimal Rill project directory with rill.yaml."""
    rill_dir.mkdir(parents=True, exist_ok=True)
    rill_yaml = rill_dir / "rill.yaml"
    if not rill_yaml.exists():
        rill_yaml.write_text(_RILL_YAML_CONTENT)
        info(f"Created {rill_dir}/ with rill.yaml")
