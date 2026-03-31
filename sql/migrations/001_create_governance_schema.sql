-- Baseline governance schema; existing tables remain unchanged.
IF NOT EXISTS (SELECT 1 FROM sys.schemas WHERE name = 'governance_history')
BEGIN
    EXEC('CREATE SCHEMA governance_history');
END;
