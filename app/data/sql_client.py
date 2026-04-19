from __future__ import annotations

import struct
from typing import Any

import pyodbc
from azure.identity import ClientSecretCredential

from app.config import Settings

SQL_COPT_SS_ACCESS_TOKEN = 1256


class SqlClient:
    def __init__(self, settings: Settings):
        self._settings = settings

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

    def query(self, sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            return [dict(zip(columns, row, strict=False)) for row in rows]

    def execute(self, sql: str, params: tuple[Any, ...] = ()) -> int:
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            conn.commit()
            return cursor.rowcount
