IF NOT EXISTS (SELECT 1 FROM sys.schemas WHERE name = 'governance_history')
BEGIN
    EXEC('CREATE SCHEMA governance_history');
END;
GO

IF OBJECT_ID('governance_history.generation_record', 'U') IS NULL
BEGIN
    CREATE TABLE governance_history.generation_record (
        generation_id UNIQUEIDENTIFIER NOT NULL PRIMARY KEY,
        session_id NVARCHAR(128) NOT NULL,
        user_id NVARCHAR(128) NOT NULL,
        user_display_name NVARCHAR(256) NULL,
        prompt_text NVARCHAR(MAX) NOT NULL,
        response_text NVARCHAR(MAX) NULL,
        generation_status NVARCHAR(32) NOT NULL,
        grounding_mode NVARCHAR(32) NOT NULL,
        model_deployment NVARCHAR(128) NOT NULL,
        used_rest_fallback BIT NOT NULL,
        failure_reason NVARCHAR(1024) NULL,
        created_at_utc DATETIME2 NOT NULL,
        completed_at_utc DATETIME2 NULL,
        request_correlation_id NVARCHAR(128) NOT NULL
    );
END;
GO

IF OBJECT_ID('governance_history.source_reference', 'U') IS NULL
BEGIN
    CREATE TABLE governance_history.source_reference (
        source_reference_id UNIQUEIDENTIFIER NOT NULL PRIMARY KEY,
        generation_id UNIQUEIDENTIFIER NOT NULL,
        search_document_id NVARCHAR(128) NULL,
        source_title NVARCHAR(512) NOT NULL,
        canonical_url NVARCHAR(1024) NOT NULL,
        published_at_utc DATETIME2 NOT NULL,
        retrieved_at_utc DATETIME2 NOT NULL,
        freshness_eligible BIT NOT NULL,
        search_score FLOAT NULL,
        excerpt_text NVARCHAR(MAX) NULL,
        source_rank INT NOT NULL,
        CONSTRAINT FK_source_reference_generation FOREIGN KEY (generation_id)
            REFERENCES governance_history.generation_record(generation_id)
    );
END;
GO

IF OBJECT_ID('governance_history.audit_record', 'U') IS NULL
BEGIN
    CREATE TABLE governance_history.audit_record (
        audit_event_id UNIQUEIDENTIFIER NOT NULL PRIMARY KEY,
        generation_id UNIQUEIDENTIFIER NULL,
        session_id NVARCHAR(128) NOT NULL,
        user_id NVARCHAR(128) NOT NULL,
        action_type NVARCHAR(64) NOT NULL,
        action_status NVARCHAR(32) NOT NULL,
        occurred_at_utc DATETIME2 NOT NULL,
        request_correlation_id NVARCHAR(128) NOT NULL,
        client_app_id NVARCHAR(128) NOT NULL,
        client_ip_hash NVARCHAR(256) NULL,
        details_json NVARCHAR(MAX) NULL,
        CONSTRAINT FK_audit_record_generation FOREIGN KEY (generation_id)
            REFERENCES governance_history.generation_record(generation_id)
    );
END;
GO
