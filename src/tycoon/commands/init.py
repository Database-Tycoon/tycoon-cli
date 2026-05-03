"""tycoon init -- scaffold a new tycoon project."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Annotated, Optional

import typer
import yaml

from tycoon.project import (
    BITool,
    IngestionTool,
    OrchestratorTool,
    StackConfig,
    TransformationTool,
    WarehouseType,
)
from tycoon.scaffolding.templates import (
    list_templates,
    scaffold_blank_project,
    scaffold_from_template,
)
from tycoon.utils.console import console, error, header, info, next_steps, success, warn


def _prompt_choice(prompt: str, options: list[str]) -> int:
    """Print a numbered menu and return the 1-based choice as an int."""
    for i, opt in enumerate(options, 1):
        console.print(f"  {i}) {opt}")
    while True:
        raw = typer.prompt(prompt)
        try:
            choice = int(raw)
            if 1 <= choice <= len(options):
                return choice
        except ValueError:
            pass
        warn(f"Please enter a number between 1 and {len(options)}.")


@dataclass
class DetectedItem:
    """An auto-detected stack component on disk."""

    path: Path
    kind: str  # "inline" (inside target) | "sibling" (sibling of target)


@dataclass
class DetectionResults:
    """Structured output of `_detect_existing`."""

    dbt: list[DetectedItem] = field(default_factory=list)
    rill: list[DetectedItem] = field(default_factory=list)
    warehouse: list[DetectedItem] = field(default_factory=list)

    def has_any(self) -> bool:
        return bool(self.dbt or self.rill or self.warehouse)


# Canonical inline subdirs to probe
_DBT_INLINE_DIRS = ("dbt_project", "dbt", "transformation")
_RILL_INLINE_DIRS = ("rill", "dashboards")


def _detect_existing(target: Path) -> DetectionResults:
    """Scan the target directory (and its siblings) for existing stack components.

    Looks for:
      - dbt: ``<target>/<subdir>/dbt_project.yml`` for canonical subdirs, plus
        ``dbt_project.yml`` in the target root, and any sibling directory of
        ``target`` that contains a ``dbt_project.yml``.
      - rill: ``<target>/<subdir>/rill.yaml`` and sibling dirs.
      - warehouse: any ``<target>/data/*.duckdb`` that doesn't look like a raw
        ingestion DB (names starting with ``raw_`` or ending in ``_raw``).
    """
    results = DetectionResults()

    # dbt — target root (rare but possible)
    if (target / "dbt_project.yml").exists():
        results.dbt.append(DetectedItem(path=target, kind="inline"))

    # dbt — canonical inline subdirs
    for sub in _DBT_INLINE_DIRS:
        candidate = target / sub
        if (candidate / "dbt_project.yml").exists():
            results.dbt.append(DetectedItem(path=candidate, kind="inline"))

    # rill — canonical inline subdirs
    for sub in _RILL_INLINE_DIRS:
        candidate = target / sub
        if (candidate / "rill.yaml").exists():
            results.rill.append(DetectedItem(path=candidate, kind="inline"))

    # warehouse — data/*.duckdb (excluding files that look like raw ingestion DBs)
    data_dir = target / "data"
    if data_dir.exists():
        for db_file in sorted(data_dir.glob("*.duckdb")):
            name = db_file.stem
            if name.startswith("raw_") or name.endswith("_raw") or name == "raw":
                continue
            results.warehouse.append(DetectedItem(path=db_file, kind="inline"))

    # Siblings — walk one level up, check dirs that look relevant
    parent = target.parent
    if parent.exists() and parent != target:
        for sibling in sorted(parent.iterdir()):
            if not sibling.is_dir() or sibling == target or sibling.name.startswith("."):
                continue
            if (sibling / "dbt_project.yml").exists():
                results.dbt.append(DetectedItem(path=sibling, kind="sibling"))
            if (sibling / "rill.yaml").exists():
                results.rill.append(DetectedItem(path=sibling, kind="sibling"))

    return results


@dataclass
class WizardResult:
    """Output of the init wizard."""

    stack: StackConfig
    dbt_path: str | None = None  # where dbt project lives (None => skipped)
    rill_path: str | None = None  # where Rill project lives (None => skipped)
    warehouse_path: str | None = None  # DuckDB path or cloud conn string
    llm_provider: str | None = None  # ask.llm.provider; None => skipped


def _print_section(title: str) -> None:
    console.print()
    console.print(f"[bold cyan]── {title} ──────────────────[/bold cyan]")


def _clone_repo(url: str, dest: Path) -> bool:
    """git clone <url> into <dest>. Returns True on success."""
    import subprocess

    if dest.exists():
        warn(f"{dest} already exists; leaving it alone.")
        return True
    try:
        subprocess.run(["git", "clone", url, str(dest)], check=True)
        success(f"Cloned into {dest}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        error(f"git clone failed: {exc}")
        return False


def _prompt_register_project(component: str, default_sibling: Path) -> str | None:
    """Shared sub-flow for "register existing" — returns absolute path string or None on failure."""
    raw = typer.prompt(
        f"Local path or GitHub URL for your {component} project",
        default="",
    ).strip()
    if not raw:
        warn("No path provided; treating this component as skipped.")
        return None

    if raw.startswith(("http://", "https://", "git@")):
        clone_here = typer.confirm(
            f"Clone into {default_sibling}?",
            default=True,
        )
        dest = default_sibling if clone_here else Path(
            typer.prompt(f"Where should the {component} project be cloned?", default=str(default_sibling))
        ).expanduser().resolve()
        if not _clone_repo(raw, dest):
            return None
        return str(dest)

    path = Path(raw).expanduser().resolve()
    if not path.exists():
        warn(f"Path {path} does not exist; treating this component as skipped.")
        return None
    return str(path)


def _prompt_ingestion() -> tuple[IngestionTool, bool]:
    _print_section("Ingestion")
    console.print("How do you load data into your warehouse?")
    choice = _prompt_choice("Choice", [
        "dlt — tycoon manages it (scaffolds and runs dlt pipelines)",
        "External (Airbyte / Fivetran / Meltano / custom) — tycoon records only",
        "Skip — no ingestion configured",
    ])
    if choice == 1:
        return IngestionTool.dlt, True
    if choice == 2:
        sub = _prompt_choice("Which external tool?", ["Airbyte", "Fivetran", "Meltano", "Custom"])
        tool = [IngestionTool.airbyte, IngestionTool.fivetran, IngestionTool.meltano, IngestionTool.none][sub - 1]
        # "Custom" falls through to IngestionTool.none since we don't have a generic 'external' enum value,
        # but managed=False still signals tycoon won't run it.
        return tool, False
    return IngestionTool.none, False


def _prompt_warehouse(project_name: str) -> tuple[WarehouseType, str]:
    _print_section("Warehouse")
    console.print("Where should your data live?")
    choice = _prompt_choice("Choice", [
        "Local DuckDB at ./data/warehouse.duckdb  [recommended]",
        "Use an existing DuckDB file (provide path)",
        "Cloud — MotherDuck / Snowflake / BigQuery",
    ])
    if choice == 1:
        return WarehouseType.duckdb, "data/warehouse.duckdb"
    if choice == 2:
        raw = typer.prompt("Path to your DuckDB file", default="data/warehouse.duckdb")
        return WarehouseType.duckdb, raw
    # Cloud
    cloud_sub = _prompt_choice("Cloud warehouse", ["MotherDuck", "Snowflake", "BigQuery"])
    if cloud_sub == 1:
        md_name = typer.prompt("MotherDuck database name", default=project_name.replace("-", "_"))
        return WarehouseType.motherduck, f"md:{md_name}"
    if cloud_sub == 2:
        info("Snowflake: tycoon will write your dbt profile; query/schema commands are DuckDB-only for now.")
        return WarehouseType.snowflake, ""
    info("BigQuery: tycoon will write your dbt profile; query/schema commands are DuckDB-only for now.")
    return WarehouseType.bigquery, ""


def _prompt_dbt(
    target: Path,
    project_name: str,
    detected: DetectionResults,
) -> tuple[TransformationTool, bool, str | None]:
    """Returns (tool, managed, path)."""
    _print_section("dbt (transformation)")
    console.print("How should tycoon handle dbt?")

    options: list[str] = []
    detected_paths: list[Path] = [d.path for d in detected.dbt]
    for item in detected.dbt:
        options.append(f"Use detected project at {item.path} ({item.kind})")

    default_new = target.parent / f"{project_name}-dbt"
    options.append(f"Create new dbt project at {default_new} (sibling repo)")
    options.append("Register existing project (local path or GitHub URL)")
    options.append("Skip — `tycoon data transform` becomes a no-op")

    choice = _prompt_choice("Choice", options)

    # Detected
    if choice <= len(detected_paths):
        return TransformationTool.dbt, False, str(detected_paths[choice - 1])
    # Create new (sibling)
    if choice == len(detected_paths) + 1:
        return TransformationTool.dbt, True, str(default_new)
    # Register existing
    if choice == len(detected_paths) + 2:
        registered = _prompt_register_project("dbt", default_new)
        if registered:
            return TransformationTool.dbt, False, registered
        return TransformationTool.none, False, None
    # Skip
    return TransformationTool.none, False, None


def _prompt_rill(
    target: Path,
    detected: DetectionResults,
) -> tuple[BITool, bool, str | None]:
    """Returns (tool, managed, path)."""
    _print_section("Rill (BI)")
    console.print("How should tycoon handle Rill?")

    options: list[str] = []
    detected_paths: list[Path] = [d.path for d in detected.rill]
    for item in detected.rill:
        options.append(f"Use detected project at {item.path} ({item.kind})")

    default_new = target / "rill"
    options.append(f"Create new inline at {default_new}")
    options.append("Register existing project (local path)")
    options.append("Skip — `tycoon data analyze --rill` becomes a no-op")

    choice = _prompt_choice("Choice", options)

    # Detected
    if choice <= len(detected_paths):
        return BITool.rill, False, str(detected_paths[choice - 1])
    # Create new (inline)
    if choice == len(detected_paths) + 1:
        return BITool.rill, True, str(default_new)
    # Register
    if choice == len(detected_paths) + 2:
        registered = _prompt_register_project("Rill", default_new)
        if registered:
            return BITool.rill, False, registered
        return BITool.none, False, None
    # Skip
    return BITool.none, False, None


@dataclass(frozen=True)
class DbtWarehouseTarget:
    """Structured view of a dbt profile's active output target.

    ``adapter_type`` is the raw dbt adapter type (``duckdb``, ``snowflake``,
    ``bigquery``, ``redshift``, ``postgres``, ...). ``identifier`` is the
    best single-field locator for the warehouse:

    * duckdb (local)  → absolute filesystem path
    * duckdb (md:*)   → the full ``md:<name>`` string
    * snowflake       → ``<account>`` (dbt's ``account`` field)
    * bigquery        → ``<project>``
    * redshift        → ``<host>``
    * anything else   → whatever looks distinctive (may be empty)

    ``display`` is a human-friendly string for prompts / warnings. For
    DuckDB and MotherDuck this equals ``identifier``; for Snowflake it's
    ``snowflake://<account>[/<database>]`` so users can see *which*
    Snowflake they're pointed at.
    """

    adapter_type: str
    identifier: str
    display: str
    details: dict[str, str]

    @property
    def tycoon_warehouse_type(self) -> str | None:
        """Map adapter_type → tycoon's WarehouseType string, or None if unknown.

        MotherDuck is a DuckDB adapter with an ``md:*`` path — the caller
        should pass ``identifier`` in when resolving ambiguity.
        """
        if self.adapter_type == "duckdb":
            return "motherduck" if self.identifier.startswith("md:") else "duckdb"
        if self.adapter_type in {"snowflake", "bigquery", "redshift"}:
            return self.adapter_type
        return None


def _profiles_yml_search_paths(
    dbt_project_dir: Path,
    profiles_dir: Path | None,
) -> list[Path]:
    """Build the ordered list of ``profiles.yml`` candidates.

    When ``profiles_dir`` is supplied, it wins outright (matches dbt's
    own ``--profiles-dir`` semantics). Otherwise we walk dbt's default
    lookup order: co-located ``profiles.yml`` if present, then
    ``~/.dbt/profiles.yml``.
    """
    if profiles_dir is not None:
        return [profiles_dir / "profiles.yml"]
    return [
        dbt_project_dir / "profiles.yml",
        Path.home() / ".dbt" / "profiles.yml",
    ]


def _read_dbt_target(
    dbt_project_dir: Path,
    profiles_dir: Path | None = None,
    profile_name: str | None = None,
    target_name: str | None = None,
) -> dict | None:
    """Return the active dbt target dict, or None if it can't be resolved.

    Resolution rules — each defaultable field lets the caller override
    so ``tycoon register dbt --profiles-dir / --profile / --target`` (and
    its persisted ``tycoon.yml`` equivalents) work the way dbt's own CLI
    flags do:

    - ``profiles_dir`` (CLI override) → ``<dbt_project_dir>/profiles.yml``
      → ``~/.dbt/profiles.yml``.
    - ``profile_name`` (CLI override) → ``profile:`` field in
      ``dbt_project.yml``.
    - ``target_name`` (CLI override) → profile's ``target:`` field →
      ``"dev"``.
    """
    if profile_name is None:
        try:
            project_yml = yaml.safe_load((dbt_project_dir / "dbt_project.yml").read_text())
        except (OSError, yaml.YAMLError):
            return None
        if not isinstance(project_yml, dict):
            return None
        profile_name = project_yml.get("profile")
        if not profile_name:
            return None

    for candidate in _profiles_yml_search_paths(dbt_project_dir, profiles_dir):
        if not candidate.exists():
            continue
        try:
            profiles = yaml.safe_load(candidate.read_text())
        except (OSError, yaml.YAMLError):
            continue
        if not isinstance(profiles, dict):
            continue
        profile = profiles.get(profile_name)
        if not isinstance(profile, dict):
            continue
        chosen_target = target_name or profile.get("target", "dev")
        target = profile.get("outputs", {}).get(chosen_target, {})
        if isinstance(target, dict):
            return target
    return None


def _extract_dbt_warehouse_target(
    dbt_project_dir: Path,
    profiles_dir: Path | None = None,
    profile_name: str | None = None,
    target_name: str | None = None,
) -> DbtWarehouseTarget | None:
    """Extract a structured warehouse target from a dbt project's active profile.

    Returns ``None`` if the profile can't be read. For DuckDB / MotherDuck
    targets ``identifier`` is the filesystem path (or ``md:<name>``); for
    Snowflake it's the ``account``; for BigQuery it's the ``project``. The
    ``details`` map keeps per-adapter extras (database / dataset / host)
    so callers can render richer warnings without re-parsing profiles.
    """
    target = _read_dbt_target(
        dbt_project_dir,
        profiles_dir=profiles_dir,
        profile_name=profile_name,
        target_name=target_name,
    )
    if target is None:
        return None
    adapter_type = target.get("type") or ""

    if adapter_type == "duckdb":
        path = target.get("path")
        if not path:
            return None
        if str(path).startswith("md:"):
            return DbtWarehouseTarget(
                adapter_type="duckdb",
                identifier=str(path),
                display=str(path),
                details={},
            )
        abs_path = Path(path)
        if not abs_path.is_absolute():
            abs_path = (dbt_project_dir / abs_path).resolve()
        return DbtWarehouseTarget(
            adapter_type="duckdb",
            identifier=str(abs_path),
            display=str(abs_path),
            details={},
        )

    if adapter_type == "snowflake":
        account = str(target.get("account") or "")
        database = str(target.get("database") or "")
        display = f"snowflake://{account}" + (f"/{database}" if database else "")
        return DbtWarehouseTarget(
            adapter_type="snowflake",
            identifier=account,
            display=display,
            details={
                "database": database,
                "schema": str(target.get("schema") or ""),
                "warehouse": str(target.get("warehouse") or ""),
                "role": str(target.get("role") or ""),
            },
        )

    if adapter_type == "bigquery":
        project = str(target.get("project") or "")
        dataset = str(target.get("dataset") or target.get("schema") or "")
        display = f"bigquery://{project}" + (f"/{dataset}" if dataset else "")
        return DbtWarehouseTarget(
            adapter_type="bigquery",
            identifier=project,
            display=display,
            details={
                "dataset": dataset,
                "method": str(target.get("method") or ""),
                "location": str(target.get("location") or ""),
            },
        )

    if adapter_type == "redshift":
        host = str(target.get("host") or "")
        database = str(target.get("dbname") or target.get("database") or "")
        display = f"redshift://{host}" + (f"/{database}" if database else "")
        return DbtWarehouseTarget(
            adapter_type="redshift",
            identifier=host,
            display=display,
            details={"database": database, "schema": str(target.get("schema") or "")},
        )

    # Unknown / unmapped adapter — surface the raw type so callers can
    # still warn about a mismatch against tycoon's configured warehouse.
    return DbtWarehouseTarget(
        adapter_type=adapter_type,
        identifier="",
        display=adapter_type,
        details={},
    )


def _extract_dbt_duckdb_path(dbt_project_dir: Path) -> str | None:
    """Backwards-compat shim: DuckDB path string (incl. ``md:*``) or None.

    Existing callers that only care about the DuckDB/MotherDuck alignment
    use this; cross-adapter callers should use ``_extract_dbt_warehouse_target``.
    """
    target = _extract_dbt_warehouse_target(dbt_project_dir)
    if target is None or target.adapter_type != "duckdb":
        return None
    return target.identifier


def _normalize_warehouse_for_compare(value: str) -> str:
    """Canonicalize a warehouse value for equality check.

    ``md:*`` strings are returned verbatim; filesystem paths are resolved
    against CWD if relative and returned as absolute.
    """
    if value.startswith("md:"):
        return value
    abs_path = Path(value).expanduser()
    if not abs_path.is_absolute():
        abs_path = (Path.cwd() / abs_path).resolve()
    else:
        abs_path = abs_path.resolve()
    return str(abs_path)


def _maybe_align_warehouse(wizard_warehouse_path: str, dbt_project_dir: Path) -> str:
    """Warn if the dbt project targets a different DuckDB/MotherDuck than the
    wizard's warehouse choice. Prompt to adopt the dbt target."""
    dbt_path = _extract_dbt_duckdb_path(dbt_project_dir)
    if not dbt_path:
        return wizard_warehouse_path

    if _normalize_warehouse_for_compare(wizard_warehouse_path) == _normalize_warehouse_for_compare(dbt_path):
        return wizard_warehouse_path

    console.print()
    warn(
        f"Your dbt project targets [bold]{dbt_path}[/bold], "
        f"but you chose [bold]{wizard_warehouse_path}[/bold] for the warehouse."
    )
    info("If these diverge, dbt writes to one place and `tycoon data query` reads from another.")
    adopt = typer.confirm(
        f"Use the dbt project's target ({dbt_path}) as tycoon's warehouse?",
        default=True,
    )
    if adopt:
        success(f"Adopted {dbt_path} as the warehouse.")
        return dbt_path
    return wizard_warehouse_path


def _detect_local_llm() -> list[tuple[str, int]]:
    """Probe LM Studio's :1234 and Ollama's :11434 ports for an
    OpenAI-compatible ``/models`` endpoint. Returns a list of
    ``(provider, model_count)`` for whichever runtimes are reachable.

    The wizard uses the model count to break ties: when both runtimes
    are up, the one with models loaded is the obvious pick (the other
    needs a model install regardless). Bounded at 2s per probe so
    wizard latency stays acceptable even when both ports are dead.
    """
    from tycoon.commands.ask import _probe_local_llm
    from tycoon.nao import _LM_STUDIO_PRESET, _OLLAMA_PRESET

    detected: list[tuple[str, int]] = []
    lm_ok, lm_count, _ = _probe_local_llm(_LM_STUDIO_PRESET["base_url"], "lm-studio")
    if lm_ok:
        detected.append(("lm-studio", lm_count))
    ol_ok, ol_count, _ = _probe_local_llm(_OLLAMA_PRESET["base_url"], "ollama")
    if ol_ok:
        detected.append(("ollama", ol_count))
    return detected


def _prompt_llm() -> str | None:
    """Pick an LLM provider for the `tycoon ask` AI agent.

    Auto-detection: before showing the menu, probe LM Studio and
    Ollama's default ports. If exactly one is reachable, offer a
    one-keystroke confirmation instead of the full 7-option menu.
    Either runtime running locally is the strongest signal we can get
    that the user wants it — short-circuit accordingly.

    Returns the provider shortcut string (e.g. ``lm-studio``) or ``None``
    if the user opts out. The shortcut is consumed by
    ``scaffold_blank_project`` and persisted as ``ask.llm.provider`` in
    tycoon.yml; ``tycoon register llm <provider>`` later expands it to
    a full nao config.

    Defaults to LM Studio in the menu because it's the lowest-friction
    option: no account, no API key, runs offline, doesn't send schema
    or rows over the wire. This matters a lot when the warehouse holds
    anything sensitive — the entire point of a local-first stack.
    """
    _print_section("AI analytics agent (`tycoon ask`)")

    # Auto-detect path: probe ports + model counts.
    #   - Exactly one runtime up → ask only for confirmation.
    #   - Both up + only one has models loaded → suggest the loaded one
    #     (the other would just need a model install anyway).
    #   - Both up + both have models → fall through to the menu (truly
    #     ambiguous; user knows which they want).
    #   - Both up + neither has models → fall through to the menu (no
    #     basis for picking, both will need an install).
    # User can always decline the suggestion to fall through.
    detected = _detect_local_llm()
    suggestion: tuple[str, int] | None = None
    if len(detected) == 1:
        suggestion = detected[0]
    elif len(detected) == 2:
        loaded = [d for d in detected if d[1] >= 1]
        if len(loaded) == 1:
            suggestion = loaded[0]

    if suggestion is not None:
        provider, model_count = suggestion
        label = "LM Studio" if provider == "lm-studio" else "Ollama"
        loaded_note = (
            f"{model_count} model(s) loaded"
            if model_count >= 1
            else "no models loaded yet"
        )
        console.print(
            f"Detected [bold]{label}[/bold] running locally "
            f"([dim]{loaded_note}[/dim]) — the recommended pick for "
            "natural-language analytics over your warehouse."
        )
        if typer.confirm(f"Use {label}?", default=True):
            return provider
        console.print()  # Falls through to the full menu below.

    if len(detected) == 2 and suggestion is None:
        # Both reachable, both have models OR both have none — surface
        # the state so the user picks knowingly.
        notes = [
            f"{'LM Studio' if p == 'lm-studio' else 'Ollama'} ({c} model(s))"
            for p, c in detected
        ]
        console.print(
            f"[dim]Detected both runtimes locally: {', '.join(notes)}. "
            "Pick one below.[/dim]"
        )

    console.print(
        "Pick an LLM provider for natural-language queries over your data.\n"
        "[dim]Without one, `tycoon ask chat` is unavailable — the rest of "
        "tycoon (init, ingest, transform, query, sync, history) works "
        "regardless.\n"
        "Recommended local model: Qwen 2.5 Coder 7B Instruct (~4.7 GB). "
        "Pull instructions surface after you pick a local provider.[/dim]"
    )
    choice = _prompt_choice("Choice", [
        "LM Studio — local, OpenAI-compatible, no API key (recommended)",
        "Ollama — local, OpenAI-compatible, no API key",
        "OpenAI",
        "Anthropic",
        "Gemini",
        "Mistral",
        "Skip — `tycoon ask chat` will be unavailable until you run "
        "`tycoon register llm <provider>`",
    ])
    return [
        "lm-studio", "ollama", "openai", "anthropic", "gemini", "mistral", None
    ][choice - 1]


def _prompt_orchestrator() -> tuple[OrchestratorTool, bool]:
    _print_section("Orchestrator")
    console.print("How should tycoon handle scheduling?")
    choice = _prompt_choice("Choice", [
        "Dagster — tycoon manages it (runs `dagster dev`, auto-generates assets)",
        "External (Airflow / Prefect / Dagster Cloud / other) — tycoon records only",
        "Skip — I'll run pipelines manually via tycoon CLI",
    ])
    if choice == 1:
        return OrchestratorTool.dagster, True
    if choice == 2:
        sub = _prompt_choice("Which external orchestrator?", ["Airflow", "Prefect", "Other"])
        tool = [OrchestratorTool.airflow, OrchestratorTool.prefect, OrchestratorTool.other][sub - 1]
        return tool, False
    return OrchestratorTool.none, False


def _run_wizard(target: Path, project_name: str) -> WizardResult:
    """Run the interactive setup questionnaire, per-component.

    Order follows the data flow: ingestion → warehouse → dbt → rill → orchestrator.
    """
    detected = _detect_existing(target)
    if detected.has_any():
        info("Detected existing components:")
        for item in detected.dbt:
            console.print(f"  [dim]dbt   [{item.kind}]:[/dim] {item.path}")
        for item in detected.rill:
            console.print(f"  [dim]rill  [{item.kind}]:[/dim] {item.path}")
        for item in detected.warehouse:
            console.print(f"  [dim]warehouse [{item.kind}]:[/dim] {item.path}")
        console.print()

    ingestion, ingestion_managed = _prompt_ingestion()
    warehouse, warehouse_path = _prompt_warehouse(project_name)
    transformation, transformation_managed, dbt_path = _prompt_dbt(target, project_name, detected)

    # Alignment check: if dbt project wasn't just scaffolded by us, see if it
    # targets a different warehouse than the user chose.
    if (
        transformation == TransformationTool.dbt
        and not transformation_managed
        and dbt_path
        and warehouse in (WarehouseType.duckdb, WarehouseType.motherduck)
    ):
        aligned = _maybe_align_warehouse(warehouse_path, Path(dbt_path))
        if aligned != warehouse_path:
            warehouse_path = aligned
            if aligned.startswith("md:"):
                warehouse = WarehouseType.motherduck
            else:
                warehouse = WarehouseType.duckdb

    bi, bi_managed, rill_path = _prompt_rill(target, detected)
    llm_provider = _prompt_llm()
    orchestrator, orchestrator_managed = _prompt_orchestrator()

    stack = StackConfig(
        ingestion=ingestion,
        ingestion_managed=ingestion_managed,
        warehouse=warehouse,
        transformation=transformation,
        transformation_managed=transformation_managed,
        bi=bi,
        bi_managed=bi_managed,
        orchestrator=orchestrator,
        orchestrator_managed=orchestrator_managed,
    )
    return WizardResult(
        stack=stack,
        dbt_path=dbt_path,
        rill_path=rill_path,
        warehouse_path=warehouse_path,
        llm_provider=llm_provider,
    )


def _mode_next_steps(
    stack: StackConfig,
    existing_dbt_path: str | None,
    *,
    ask_chained: bool = False,
) -> None:
    """Print next steps appropriate to the configured stack mode.

    When ``ask_chained=True``, the AI agent setup already ran during
    init — point the user at ``tycoon ask chat`` directly instead of
    asking them to run ``tycoon register llm`` first.
    """
    ask_step = (
        ("tycoon ask chat", "launch the AI analytics agent")
        if ask_chained
        else ("tycoon register llm <provider>", "wire up the AI analytics agent")
    )
    if not stack.ingestion_managed and existing_dbt_path:
        # BYO full pipeline
        next_steps(
            ("tycoon doctor", "verify your stack configuration"),
            ("tycoon data transform run", "run dbt transformations"),
            ask_step,
        )
    elif not stack.ingestion_managed:
        # Warehouse-only
        next_steps(
            ("tycoon doctor", "verify your stack configuration"),
            ("tycoon data transform run", "scaffold and run dbt models"),
            ask_step,
        )
    else:
        # Greenfield / dlt-managed
        next_steps(
            ("tycoon data sources catalog", "browse available data sources"),
            ("tycoon data sources add", "add your first data source"),
            ask_step,
        )


def _parse_param_pairs(raw: list[str]) -> dict[str, str]:
    """Parse repeated --param name=value options into a dict.

    Rejects entries without '=' or with empty names. Later occurrences of
    the same name silently overwrite earlier ones, matching how repeated
    CLI flags conventionally behave.
    """
    out: dict[str, str] = {}
    for entry in raw:
        if "=" not in entry:
            raise typer.BadParameter(
                f"--param must be in 'name=value' form; got '{entry}'"
            )
        name, _, value = entry.partition("=")
        name = name.strip()
        if not name:
            raise typer.BadParameter(f"--param name must be non-empty; got '{entry}'")
        out[name] = value
    return out


def init_cmd(
    template: Annotated[
        Optional[str],
        typer.Option(
            "--template",
            "-t",
            help="Template name to scaffold from.",
        ),
    ] = None,
    name: Annotated[
        Optional[str],
        typer.Option(
            "--name",
            "-n",
            help="Project name (defaults to current directory name).",
        ),
    ] = None,
    list_templates_flag: Annotated[
        bool,
        typer.Option(
            "--list-templates",
            help="List available templates and exit.",
        ),
    ] = False,
    param: Annotated[
        Optional[list[str]],
        typer.Option(
            "--param",
            "-p",
            help=(
                "Template parameter in 'name=value' form. Repeat for multiple. "
                "Parameters declared by the template but not supplied here "
                "will be prompted for interactively."
            ),
        ),
    ] = None,
) -> None:
    """Initialize a new tycoon project in the current directory."""
    if list_templates_flag:
        templates = list_templates()
        if not templates:
            info("No templates available.")
        else:
            header("Available Templates")
            for t in templates:
                console.print(f"  - {t}")
        raise typer.Exit(0)

    target = Path.cwd()
    project_name = name or target.name

    if (target / "tycoon.yml").exists():
        warn("tycoon.yml already exists in this directory.")
        error("Use a different directory or remove the existing tycoon.yml first.")
        raise typer.Exit(1)

    header(f"Initializing tycoon project: {project_name}")

    if template:
        parameters = _parse_param_pairs(param or [])
        try:
            scaffold_from_template(target, template, parameters=parameters)
        except FileNotFoundError as exc:
            error(str(exc))
            raise typer.Exit(1)
        except ValueError as exc:
            # Bad template.yml or missing required parameter
            error(str(exc))
            raise typer.Exit(1)
        console.print()
        success(f"Project '{project_name}' initialized from template '{template}'!")
        next_steps(
            ("tycoon data sources catalog", "browse available data sources"),
            ("tycoon data sources add", "add your first data source"),
            ("tycoon register llm <provider>", "wire up the AI analytics agent"),
        )
    else:
        result = _run_wizard(target, project_name)
        console.print()
        scaffold_blank_project(
            target,
            project_name,
            stack=result.stack,
            existing_dbt_path=result.dbt_path,
            existing_warehouse_path=result.warehouse_path,
            existing_rill_path=result.rill_path,
            llm_provider=result.llm_provider,
        )
        console.print()
        success(f"Project '{project_name}' initialized successfully!")

        # Chain the AI agent setup if the user picked a provider in the
        # wizard AND nao_core is importable. Without the [ask] extra,
        # we print a fallback hint and leave it for the user to install
        # the extra and re-run via `tycoon register llm <provider>`.
        ask_chained = False
        if result.llm_provider is not None:
            console.print()
            try:
                import nao_core  # noqa: F401
            except ImportError:
                info(
                    "AI agent setup skipped — `nao_core` not installed.\n"
                    "Install the [ask] extra and register the provider to "
                    "finish wiring up `tycoon ask chat`:\n"
                    "  [bold]pip install 'database-tycoon[ask]'[/bold]\n"
                    f"  [bold]tycoon register llm {result.llm_provider}[/bold]"
                )
            else:
                # Build a fresh config that sees the just-written
                # tycoon.yml (scaffold writes via project_data, not via
                # the cached singleton). Pass it through explicitly so
                # we don't mutate module-level state.
                from tycoon.commands.ask import setup_ask_stack
                from tycoon.config import TycoonConfig

                _print_section("AI agent setup")
                setup_ask_stack(TycoonConfig(project_root=target))
                ask_chained = True

        _mode_next_steps(result.stack, result.dbt_path, ask_chained=ask_chained)
