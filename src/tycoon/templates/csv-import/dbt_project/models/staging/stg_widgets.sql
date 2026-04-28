{{ config(materialized='table') }}

-- dlt's filesystem + read_csv() pipeline unions rows from every CSV under
-- data/input/ into a single `_read_csv` table in the raw_files schema.
-- For the widgets demo we stage that table 1:1; if you add more CSVs you
-- can filter by columns or split into per-source staging models.

SELECT
    CAST(id AS INTEGER)   AS widget_id,
    TRIM(name)            AS widget_name,
    CAST(qty AS INTEGER)  AS quantity
FROM {{ source('files', '_read_csv') }}
