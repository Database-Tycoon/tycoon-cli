---
name: dbt-dag-modeling
description: Best practices for dbt manifest parsing, model materialization, lineage DAG derivation, test coverage analysis, source freshness SLAs, and OSI semantic models.
---

# dbt DAG Modeling Skill Guide

## 1. Core Catalog & Lineage Modules
- **Manifest Loader**: `src/dbtycoon/catalog/dbt_manifest.py` (Reads dbt `manifest.json`, `run_results.json`, and `sources.json`).
- **SQL Lineage Parser**: `src/dbtycoon/catalog/sql_lineage.py` & `column_lineage.py` (Parses view SQL using `sqlglot` without database execution).
- **Semantic Models (OSI)**: `src/dbtycoon/catalog/osi.py` (Ingests semantic models; keeps `joins[]` separate from DAG `edges[]`).

## 2. Data Contract Boundaries
- **`/city.json`**: Defined in `src/dbtycoon/export/city_json.py` and validated in `web/src/contract.ts`. Must remain byte-stable for Version 1.
- **`/runs.json`**: Defined in `src/dbtycoon/export/run_json.py` and validated in `web/src/contract_runs.ts`.

## 3. Provenance & Honesty Rules
- **Named Absences**: Never invent facts or fallback to "fine/passing". Unmeasured attributes must explicitly report as `unknown` or present named absence notes.
