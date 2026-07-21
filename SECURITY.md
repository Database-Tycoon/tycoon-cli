# Security Policy

## Supported versions

| Version | Supported |
| ------- | --------- |
| 0.1.x (latest release) | Yes |
| Anything older | No |

Only the latest 0.1.x release on PyPI receives security fixes. Upgrade with
`pip install --upgrade database-tycoon` (or `uv pip install --upgrade
database-tycoon`).

## Reporting a vulnerability

Please report vulnerabilities privately — do not open a public issue:

- Email: security@databasetycoon.com
- Or use GitHub's private vulnerability reporting on
  [Database-Tycoon/tycoon-cli](https://github.com/Database-Tycoon/tycoon-cli/security/advisories/new)

You should receive an acknowledgement within a few business days. Please
include the tycoon version (`tycoon --version`), reproduction steps, and
impact.

## Trust boundary: third-party code executed at runtime

tycoon is a local-first CLI that deliberately does **not** bundle ingestion
source code. Two commands download and run third-party code at run time, and
you should treat them with the same trust you give `pip install`:

1. **`tycoon data sources add` / `tycoon data sources catalog install`** —
   for catalog sources (github, slack, stripe, hubspot, notion, ...) tycoon
   runs `dlt init <source> duckdb`, which downloads the source's Python
   package from dlt-hub's
   [verified-sources](https://github.com/dlt-hub/verified-sources) repository
   into `~/.tycoon/sources/`. That code executes with your user's privileges
   on every ingestion run. tycoon prompts before downloading and prints what
   is being fetched and from where; it does not audit the downloaded code.

2. **Runtime dlt extras** — generic source types (`sql_database`,
   `filesystem`, ...) may require a dlt pip extra. When one is missing,
   tycoon offers to run `uv pip install` / `pip install` for
   `dlt[<extra>]==<installed dlt version>` (pinned so a runtime install can
   never change your dlt version). This installs packages from PyPI into the
   active environment, again only after an interactive confirmation.

If your environment forbids runtime package installation, decline the
prompts and pre-install the sources/extras through your own vetted channel —
both mechanisms are idempotent and skip work that is already present.

## Hardening in this repository

- GitHub Actions are pinned to full commit SHAs and updated via Dependabot;
  workflows run with least-privilege `permissions:` blocks.
- CI runs gitleaks (secret scanning) on the full git history; contributors
  can opt into the same scan locally via `uvx pre-commit install` (gitleaks +
  bandit hooks in `.pre-commit-config.yaml`).
