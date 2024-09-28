{{ config(materialized='table') }}

SELECT
c.id as condition_id, 
c.term as condition_term_raw,
s.protocol_section__identification_module__nct_id as nct_id,
s.protocol_section__identification_module__organization__full_name as org_full_name,
s.protocol_section__status_module__overall_status as study_status,
case when s.protocol_section__status_module__overall_status != 'RECRUITING' then 0 else 1 end is_recruiting,
s.protocol_section__design_module__study_type as study_type

FROM{{ ref('studies') }} s 
LEFT JOIN  {{ ref('conditions') }} c ON s._dlt_id = c._dlt_parent_id