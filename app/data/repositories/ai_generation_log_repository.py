from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from app.data.sql_client import SqlClient


class AIGenerationLogRepository:
    def __init__(self, sql_client: SqlClient | None):
        self._sql_client = sql_client
        self._memory_logs: list[dict[str, Any]] = []
        self._db_columns: list[dict[str, Any]] | None = None

    def _get_db_columns(self) -> list[dict[str, Any]]:
        if self._sql_client is None:
            return []
        if self._db_columns is None:
            self._db_columns = self._sql_client.query(
                """
                SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_NAME = 'AIGenerationLog'
                ORDER BY ORDINAL_POSITION
                """
            )
        return self._db_columns

    @staticmethod
    def _fallback_value(data_type: str, executed_at: str) -> Any:
        normalized = data_type.lower()
        if normalized == "uniqueidentifier":
            return str(uuid4())
        if normalized in {"bit"}:
            return 0
        if normalized in {"int", "bigint", "smallint", "tinyint", "decimal", "numeric", "float", "real"}:
            return 0
        if normalized in {"datetime", "datetime2", "smalldatetime", "datetimeoffset", "date", "time"}:
            return executed_at
        return ""

    def save(
        self,
        *,
        step_name: str,
        model_name: str,
        ai_input_raw: str,
        ai_output_raw: str,
        execution_status: str,
        execution_error: str | None,
        api_execution_identity: str,
        logged_in_user_identity: str,
        correlation_id: str,
    ) -> None:
        record = {
            "log_id": str(uuid4()),
            "step_name": step_name,
            "model_name": model_name,
            "ai_input_raw": ai_input_raw,
            "ai_output_raw": ai_output_raw,
            "execution_status": execution_status,
            "execution_error": execution_error,
            "executed_at_utc": datetime.now(UTC).isoformat(),
            "api_execution_identity": api_execution_identity,
            "logged_in_user_identity": logged_in_user_identity,
            "correlation_id": correlation_id,
        }
        if self._sql_client is None:
            self._memory_logs.append(record)
            return

        db_columns = self._get_db_columns()
        mapped_values = {
            "logid": record["log_id"],
            "traceid": record["log_id"],
            "trace_id": correlation_id,
            "scenario": step_name,
            "stepname": step_name,
            "step_name": step_name,
            "actoroid": logged_in_user_identity,
            "requester_entra_id": logged_in_user_identity,
            "requestid": correlation_id,
            "modelname": model_name,
            "model_or_deployment": model_name,
            "promptinput": ai_input_raw,
            "aiinputraw": ai_input_raw,
            "request_payload_json": ai_input_raw,
            "aioutput": ai_output_raw,
            "aioutputraw": ai_output_raw,
            "response_payload_json": ai_output_raw,
            "iserror": 1 if execution_status == "failure" else 0,
            "executionstatus": execution_status,
            "status": execution_status,
            "errormessage": execution_error,
            "executionerror": execution_error,
            "error_detail": execution_error,
            "createdatutc": record["executed_at_utc"],
            "created_at_utc": record["executed_at_utc"],
            "executedatutc": record["executed_at_utc"],
            "apiexecutionidentity": api_execution_identity,
            "runtime_client_id": api_execution_identity,
            "loggedinuseridentity": logged_in_user_identity,
            "correlationid": correlation_id,
            "session_id": correlation_id,
            "operation_name": step_name,
            "apiendpoint": "",
            "businessobjecttype": "",
            "businessobjectid": "",
            "token_usage_json": "",
            "latency_ms": 0,
        }

        insert_columns: list[str] = []
        insert_values: list[Any] = []
        for column in db_columns:
            column_name = str(column["COLUMN_NAME"])
            lower_name = column_name.lower()
            if lower_name == "id":
                continue
            value = mapped_values.get(lower_name)
            if value is not None:
                insert_columns.append(column_name)
                insert_values.append(value)
                continue
            if str(column["IS_NULLABLE"]).upper() == "NO":
                insert_columns.append(column_name)
                insert_values.append(self._fallback_value(str(column["DATA_TYPE"]), record["executed_at_utc"]))

        column_sql = ", ".join(f"[{name}]" for name in insert_columns)
        placeholder_sql = ", ".join("?" for _ in insert_values)
        self._sql_client.execute(
            f"INSERT INTO AIGenerationLog ({column_sql}) VALUES ({placeholder_sql})",
            tuple(insert_values),
        )

    def list_memory_logs(self) -> list[dict[str, Any]]:
        return list(self._memory_logs)
