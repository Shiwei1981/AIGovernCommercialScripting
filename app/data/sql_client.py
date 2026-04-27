from __future__ import annotations

import struct
from typing import Any

import pyodbc
from azure.identity import ClientSecretCredential

from app.config import Settings
from app.errors import AppError
from app.services.db_read_governance_service import DBReadGovernanceService
from app.services.purview_visibility_service import PurviewVisibilityService
from app.services.sql_resource_parser import SQLResourceParser

SQL_COPT_SS_ACCESS_TOKEN = 1256


class SqlClient:
    def __init__(self, settings: Settings):
        self._settings = settings
        self._column_cache: dict[tuple[str, str], list[str]] = {}
        self._governance = DBReadGovernanceService(
            SQLResourceParser(settings, self.get_table_columns),
            PurviewVisibilityService(settings),
        )

    def _connect(self):
        credential = ClientSecretCredential(
            tenant_id=self._settings.azure_tenant_id,
            client_id=self._settings.azure_client_id,
            client_secret=self._settings.azure_client_secret,
        )
        token = credential.get_token("https://database.windows.net/.default").token
        token_bytes = token.encode("utf-16-le")
        exptoken = struct.pack(f"<I{len(token_bytes)}s", len(token_bytes), token_bytes)
        connection_string = (
            "Driver={ODBC Driver 18 for SQL Server};"
            f"Server=tcp:{self._settings.sql_server},1433;"
            f"Database={self._settings.sql_database};Encrypt=yes;TrustServerCertificate=no;"
        )
        return pyodbc.connect(connection_string, attrs_before={SQL_COPT_SS_ACCESS_TOKEN: exptoken})

    def query(
        self,
        sql: str,
        params: tuple[Any, ...] = (),
        *,
        user_principal_name: str | None = None,
        apply_governance: bool = True,
    ) -> list[dict[str, Any]]:
        resources = None
        decisions = []
        if self._settings.db_read_governance_enabled and apply_governance:
            if not user_principal_name:
                raise AppError("Authenticated user UPN is required for database read governance.", 401)
            resources, decisions = self._governance.authorize(sql, user_principal_name)
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            result = [dict(zip(columns, row, strict=False)) for row in rows]
        if resources is None:
            return result
        return self._governance.apply_masks(result, resources, decisions)

    def execute(self, sql: str, params: tuple[Any, ...] = ()) -> int:
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            conn.commit()
            return cursor.rowcount

    def get_table_columns(self, schema_name: str, table_name: str) -> list[str]:
        key = (schema_name.lower(), table_name.lower())
        if key in self._column_cache:
            return self._column_cache[key]
        rows = self.query(
            """
            SELECT COLUMN_NAME
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ?
            ORDER BY ORDINAL_POSITION
            """,
            (schema_name, table_name),
            apply_governance=False,
        )
        columns = [str(row["COLUMN_NAME"]) for row in rows]
        self._column_cache[key] = columns
        return columns
