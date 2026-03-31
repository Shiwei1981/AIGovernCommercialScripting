CREATE OR ALTER VIEW governance_history.vw_generation_history_search
AS
SELECT
    g.generation_id,
    g.session_id,
    g.user_id,
    g.generation_status,
    g.created_at_utc,
    g.completed_at_utc,
    COUNT(sr.source_reference_id) AS source_count,
    MAX(ar.action_status) AS last_audit_status
FROM governance_history.generation_record g
LEFT JOIN governance_history.source_reference sr
    ON sr.generation_id = g.generation_id
LEFT JOIN governance_history.audit_record ar
    ON ar.generation_id = g.generation_id
GROUP BY
    g.generation_id,
    g.session_id,
    g.user_id,
    g.generation_status,
    g.created_at_utc,
    g.completed_at_utc;
GO

CREATE OR ALTER VIEW governance_history.vw_generation_audit_trace
AS
SELECT
    g.generation_id,
    g.session_id,
    g.user_id,
    ar.audit_event_id,
    ar.action_type,
    ar.action_status,
    ar.occurred_at_utc,
    sr.canonical_url,
    sr.published_at_utc
FROM governance_history.generation_record g
LEFT JOIN governance_history.audit_record ar
    ON ar.generation_id = g.generation_id
LEFT JOIN governance_history.source_reference sr
    ON sr.generation_id = g.generation_id;
GO
