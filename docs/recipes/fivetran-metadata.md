# Surface Fivetran connector state inside tycoon

If you run ingestion through Fivetran, tycoon doesn't try to replace
that — Fivetran's scheduler stays in charge. But tycoon *can* read
your connector state from the [Fivetran Metadata API](https://fivetran.com/docs/rest-api/metadata)
and mirror it into `.tycoon/metadata.duckdb`, so `tycoon data status`
and `tycoon data history` light up for the ingestion layer instead of
going dark.

## TL;DR

```bash
# 1. tycoon.yml — declare ingestion is Fivetran, supply API creds.
cat >> tycoon.yml <<'EOF'
stack:
  ingestion: fivetran
  ingestion_managed: false
  ingestion_metadata:
    api_key: ${FIVETRAN_API_KEY}
    api_secret: ${FIVETRAN_API_SECRET}
    group_id: my_group
EOF

# 2. Verify the credentials.
tycoon doctor      # shows "Fivetran auth OK (group_id=my_group)"

# 3. Pull connector state.
tycoon data fivetran sync

# 4. View the latest snapshot.
tycoon data fivetran list
tycoon data status              # also picks up the Fivetran panel
```

## Setup

Get an API key + secret from Fivetran (Settings → API Config in the web
UI, or the [Authentication API](https://fivetran.com/docs/rest-api/authentication-overview)).
Get your `group_id` from `GET /v1/groups` or from the URL of any group
in the web UI.

Tycoon reads credentials from environment via the standard `${VAR}`
interpolation in `tycoon.yml` — never paste raw secrets into the file.

```yaml
# tycoon.yml
stack:
  ingestion: fivetran
  ingestion_managed: false       # tycoon doesn't run Fivetran
  ingestion_metadata:
    api_key: ${FIVETRAN_API_KEY}
    api_secret: ${FIVETRAN_API_SECRET}
    group_id: my_group
```

## What gets pulled

`tycoon data fivetran sync` calls:

1. `GET /v1/groups/<group_id>/connectors` — lists every connector in
   the group, paginated.
2. `GET /v1/connectors/<id>` — for each, pulls full state including
   `succeeded_at`, `failed_at`, `paused`, `status.sync_state`,
   `status.setup_state`, `status.update_state`.

Everything lands in `.tycoon/metadata.duckdb` under
`fivetran_connectors`, one row per `(connector_id, captured_at)` pair.
History accumulates over time — the table is append-mostly so you can
see how a connector's state has moved.

## What you see

`tycoon data fivetran list` — latest snapshot per connector:

```text
─── Fivetran connectors ───
 Connector       Service     Schema       Sync state  Last activity
 customers_pg    postgres    raw_pg       scheduled   2h ago
 orders_shopify  shopify     raw_shopify  syncing     12m ago
 ad_spend        google_ads  raw_ads      scheduled   3d ago
```

`tycoon data status` includes the same panel beneath any dlt-side
sources.

`tycoon doctor` includes a "Fivetran auth OK" row when
`stack.ingestion = fivetran` and the credentials work.

## Auto-sync

Not in v0.1.6 — you call `tycoon data fivetran sync` manually (or
schedule it from cron). A future version may add
auto-sync on `tycoon data status` but the Fivetran API has rate limits
and we don't want to hammer it on every status check.

## What this isn't

- **Not a way to run Fivetran from tycoon.** Fivetran's own scheduler
  stays in charge. `ingestion_managed: false` is the contract.
- **Not column-level metadata.** Schemas / column lists are dbt's
  domain (use `dbt source freshness` for source-side checks).
- **Not real-time.** Each `sync` call is a snapshot — call it as often
  as you want a fresh view, but the data is only as fresh as your
  last `sync`.
- **Not Airbyte / Stitch / Meltano Cloud.** Each platform has a
  different metadata API. Open an issue if you want others.
