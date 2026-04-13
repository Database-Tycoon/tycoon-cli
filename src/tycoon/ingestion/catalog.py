"""Registry of pre-built data source templates for tycoon.

Each entry provides metadata for display, credential prompting, and pipeline
dispatch. Sources are implemented in tycoon.ingestion.sources.<id>.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class CredentialField:
    key: str        # Key stored in tycoon.yml config dict
    label: str      # Human-readable prompt label
    hint: str       # Where to get the credential
    env_var: str    # Suggested environment variable name
    secret: bool = True


@dataclass
class ConfigField:
    key: str
    label: str
    hint: str
    required: bool = True
    default: str | None = None


@dataclass
class CatalogEntry:
    id: str
    display_name: str
    category: str
    description: str
    resources: list[str]
    credentials: list[CredentialField]
    config_fields: list[ConfigField] = field(default_factory=list)
    default_schema: str = ""
    docs_url: str = ""


CATALOG: dict[str, CatalogEntry] = {
    "github": CatalogEntry(
        id="github",
        display_name="GitHub",
        category="Developer Tools",
        description="Issues, pull requests, and commits from a repository",
        resources=["issues", "pull_requests", "commits"],
        credentials=[
            CredentialField(
                key="access_token",
                label="Personal Access Token",
                hint="Create at https://github.com/settings/tokens (needs repo scope)",
                env_var="GITHUB_TOKEN",
            ),
        ],
        config_fields=[
            ConfigField(key="owner", label="Repository owner (user or org)", hint='e.g. "dlt-hub"'),
            ConfigField(key="repo", label="Repository name", hint='e.g. "dlt"'),
        ],
        default_schema="raw_github",
        docs_url="https://dlthub.com/docs/dlt-ecosystem/verified-sources/github",
    ),
    "slack": CatalogEntry(
        id="slack",
        display_name="Slack",
        category="Communication",
        description="Channels, users, and message history",
        resources=["channels", "users", "messages"],
        credentials=[
            CredentialField(
                key="access_token",
                label="Bot/User OAuth Token",
                hint="Create a Slack app at https://api.slack.com/apps with channels:read, users:read, channels:history scopes",
                env_var="SLACK_ACCESS_TOKEN",
            ),
        ],
        config_fields=[
            ConfigField(
                key="channel_ids",
                label="Channel IDs (comma-separated, leave blank for all public channels)",
                hint='e.g. "C01234567,C89012345" — copy from channel URL',
                required=False,
                default="",
            ),
        ],
        default_schema="raw_slack",
        docs_url="https://dlthub.com/docs/dlt-ecosystem/verified-sources/slack",
    ),
    "stripe": CatalogEntry(
        id="stripe",
        display_name="Stripe",
        category="Payments",
        description="Customers, subscriptions, invoices, charges, and products",
        resources=["customers", "subscriptions", "invoices", "charges", "products"],
        credentials=[
            CredentialField(
                key="stripe_secret_key",
                label="Secret Key",
                hint="Found at https://dashboard.stripe.com/apikeys — use sk_live_... or sk_test_...",
                env_var="STRIPE_SECRET_KEY",
            ),
        ],
        default_schema="raw_stripe",
        docs_url="https://dlthub.com/docs/dlt-ecosystem/verified-sources/stripe_analytics",
    ),
    "hubspot": CatalogEntry(
        id="hubspot",
        display_name="HubSpot",
        category="CRM",
        description="Contacts, companies, deals, and tickets",
        resources=["contacts", "companies", "deals", "tickets"],
        credentials=[
            CredentialField(
                key="api_key",
                label="Private App Access Token",
                hint="Create at https://app.hubspot.com under Settings > Integrations > Private Apps",
                env_var="HUBSPOT_API_KEY",
            ),
        ],
        default_schema="raw_hubspot",
        docs_url="https://dlthub.com/docs/dlt-ecosystem/verified-sources/hubspot",
    ),
    "notion": CatalogEntry(
        id="notion",
        display_name="Notion",
        category="Productivity",
        description="Databases, pages, and workspace users",
        resources=["databases", "pages", "users"],
        credentials=[
            CredentialField(
                key="api_key",
                label="Integration Token",
                hint="Create at https://www.notion.so/my-integrations — then share your databases with the integration",
                env_var="NOTION_API_KEY",
            ),
        ],
        config_fields=[
            ConfigField(
                key="database_ids",
                label="Database IDs (comma-separated, leave blank to sync all)",
                hint='Copy the ID from your Notion database URL: notion.so/<workspace>/<database-id>',
                required=False,
                default="",
            ),
        ],
        default_schema="raw_notion",
        docs_url="https://dlthub.com/docs/dlt-ecosystem/verified-sources/notion",
    ),
    "rest_api": CatalogEntry(
        id="rest_api",
        display_name="REST API",
        category="Generic",
        description="Any REST API — defaults to the PokéAPI demo (no auth needed)",
        resources=["pokemon", "berry", "type"],
        credentials=[],
        config_fields=[
            ConfigField(
                key="base_url",
                label="API base URL",
                hint='e.g. "https://pokeapi.co/api/v2/" — leave blank to use the PokéAPI demo',
                required=False,
                default="https://pokeapi.co/api/v2/",
            ),
            ConfigField(
                key="resources",
                label="Resource names (comma-separated)",
                hint='e.g. "pokemon,berry,type" — each becomes a DuckDB table',
                required=False,
                default="pokemon,berry,type",
            ),
        ],
        default_schema="raw_rest",
        docs_url="https://dlthub.com/docs/dlt-ecosystem/verified-sources/rest_api",
    ),
    "filesystem": CatalogEntry(
        id="filesystem",
        display_name="CSV / Local Files",
        category="Generic",
        description="Load CSV files from a local directory into DuckDB",
        resources=["files"],
        credentials=[],
        config_fields=[
            ConfigField(
                key="path",
                label="Directory or file path (glob supported)",
                hint='e.g. "~/data/exports/" or "/tmp/sales*.csv"',
                required=True,
            ),
        ],
        default_schema="raw_files",
        docs_url="https://dlthub.com/docs/dlt-ecosystem/verified-sources/filesystem",
    ),
}


def get_entry(source_type: str) -> CatalogEntry | None:
    return CATALOG.get(source_type)
