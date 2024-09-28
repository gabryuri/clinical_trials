{{ config(materialized='table') }}

select
id,
term,
_dlt_parent_id,
_dlt_list_idx,
_dlt_id
from {{ source('clinical_trials', 'studies__derived_section__condition_browse_module__ancestors') }}
