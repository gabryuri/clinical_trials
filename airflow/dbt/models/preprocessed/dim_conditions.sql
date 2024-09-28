{{ config(materialized='table') }}

SELECT DISTINCT
c.id as condition_id, 
c.term as condition_term_raw
FROM {{ ref('conditions') }} c 