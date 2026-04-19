IF OBJECT_ID('dbo.AIGenerationLog', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.AIGenerationLog (
        LogId UNIQUEIDENTIFIER NOT NULL PRIMARY KEY,
        StepName NVARCHAR(100) NOT NULL,
        ModelName NVARCHAR(200) NOT NULL,
        AIInputRaw NVARCHAR(MAX) NOT NULL,
        AIOutputRaw NVARCHAR(MAX) NOT NULL,
        ExecutionStatus NVARCHAR(20) NOT NULL,
        ExecutionError NVARCHAR(MAX) NULL,
        ExecutedAtUtc DATETIMEOFFSET NOT NULL,
        ApiExecutionIdentity NVARCHAR(256) NOT NULL,
        LoggedInUserIdentity NVARCHAR(256) NOT NULL,
        CorrelationId NVARCHAR(64) NOT NULL
    );
END
ELSE
BEGIN
    IF COL_LENGTH('dbo.AIGenerationLog', 'AIInputRaw') IS NULL
        ALTER TABLE dbo.AIGenerationLog ADD AIInputRaw NVARCHAR(MAX) NOT NULL DEFAULT N'';
    IF COL_LENGTH('dbo.AIGenerationLog', 'AIOutputRaw') IS NULL
        ALTER TABLE dbo.AIGenerationLog ADD AIOutputRaw NVARCHAR(MAX) NOT NULL DEFAULT N'';
    IF COL_LENGTH('dbo.AIGenerationLog', 'LogId') IS NULL
        ALTER TABLE dbo.AIGenerationLog ADD LogId UNIQUEIDENTIFIER NOT NULL DEFAULT NEWID();
    IF COL_LENGTH('dbo.AIGenerationLog', 'StepName') IS NULL
        ALTER TABLE dbo.AIGenerationLog ADD StepName NVARCHAR(100) NOT NULL DEFAULT N'';
    IF COL_LENGTH('dbo.AIGenerationLog', 'ExecutionStatus') IS NULL
        ALTER TABLE dbo.AIGenerationLog ADD ExecutionStatus NVARCHAR(20) NOT NULL DEFAULT N'success';
    IF COL_LENGTH('dbo.AIGenerationLog', 'ExecutionError') IS NULL
        ALTER TABLE dbo.AIGenerationLog ADD ExecutionError NVARCHAR(MAX) NULL;
    IF COL_LENGTH('dbo.AIGenerationLog', 'ExecutedAtUtc') IS NULL
        ALTER TABLE dbo.AIGenerationLog ADD ExecutedAtUtc DATETIMEOFFSET NOT NULL DEFAULT SYSDATETIMEOFFSET();
    IF COL_LENGTH('dbo.AIGenerationLog', 'ApiExecutionIdentity') IS NULL
        ALTER TABLE dbo.AIGenerationLog ADD ApiExecutionIdentity NVARCHAR(256) NOT NULL DEFAULT N'';
    IF COL_LENGTH('dbo.AIGenerationLog', 'LoggedInUserIdentity') IS NULL
        ALTER TABLE dbo.AIGenerationLog ADD LoggedInUserIdentity NVARCHAR(256) NOT NULL DEFAULT N'';
    IF COL_LENGTH('dbo.AIGenerationLog', 'CorrelationId') IS NULL
        ALTER TABLE dbo.AIGenerationLog ADD CorrelationId NVARCHAR(64) NOT NULL DEFAULT N'';
END
