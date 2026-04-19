DECLARE @step_col NVARCHAR(128) =
    CASE
        WHEN COL_LENGTH('dbo.AIGenerationLog', 'StepName') IS NOT NULL THEN 'StepName'
        WHEN COL_LENGTH('dbo.AIGenerationLog', 'step_name') IS NOT NULL THEN 'step_name'
        ELSE 'Scenario'
    END;

DECLARE @input_col NVARCHAR(128) =
    CASE
        WHEN COL_LENGTH('dbo.AIGenerationLog', 'AIInputRaw') IS NOT NULL THEN 'AIInputRaw'
        ELSE 'PromptInput'
    END;

DECLARE @output_col NVARCHAR(128) =
    CASE
        WHEN COL_LENGTH('dbo.AIGenerationLog', 'AIOutputRaw') IS NOT NULL THEN 'AIOutputRaw'
        ELSE 'AIOutput'
    END;

DECLARE @status_col NVARCHAR(128) =
    CASE
        WHEN COL_LENGTH('dbo.AIGenerationLog', 'ExecutionStatus') IS NOT NULL THEN 'ExecutionStatus'
        WHEN COL_LENGTH('dbo.AIGenerationLog', 'status') IS NOT NULL THEN 'status'
        ELSE 'IsError'
    END;

DECLARE @user_col NVARCHAR(128) =
    CASE
        WHEN COL_LENGTH('dbo.AIGenerationLog', 'LoggedInUserIdentity') IS NOT NULL THEN 'LoggedInUserIdentity'
        WHEN COL_LENGTH('dbo.AIGenerationLog', 'requester_entra_id') IS NOT NULL THEN 'requester_entra_id'
        ELSE 'ActorOid'
    END;

DECLARE @sql NVARCHAR(MAX) = N'
SELECT
    ' + QUOTENAME(@step_col) + N' AS StepName,
    COUNT(*) AS total_logs,
    SUM(CASE WHEN LEN(COALESCE(' + QUOTENAME(@input_col) + N', '''')) > 0 THEN 1 ELSE 0 END) AS with_input,
    SUM(CASE WHEN LEN(COALESCE(' + QUOTENAME(@output_col) + N', '''')) > 0
        OR LOWER(COALESCE(CAST(' + QUOTENAME(@status_col) + N' AS NVARCHAR(20)), '''')) = ''failure''
        THEN 1 ELSE 0 END) AS with_output_or_failure,
    SUM(CASE WHEN COALESCE(' + QUOTENAME(@user_col) + N', '''') <> '''' THEN 1 ELSE 0 END) AS with_user_identity
FROM dbo.AIGenerationLog
GROUP BY ' + QUOTENAME(@step_col) + N'
ORDER BY ' + QUOTENAME(@step_col) + N';';

EXEC sp_executesql @sql;
