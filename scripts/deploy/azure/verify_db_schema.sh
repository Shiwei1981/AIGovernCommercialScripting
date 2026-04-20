#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/common.sh"
cd "$ROOT_DIR"

load_env_file
validate_runtime_env
assert_prod_safe_flags
ensure_python_runtime

export APP_ENV="$DEPLOY_APP_ENV"
export MOCK_AUTH_ENABLED="$DEPLOY_MOCK_AUTH_ENABLED"
export SQL_MAX_ROWS="$DEPLOY_SQL_MAX_ROWS"

"$VENV_PYTHON" - "$ROOT_DIR" <<'PY'
from __future__ import annotations

import sys
from pathlib import Path
from urllib.parse import parse_qs, quote_plus, urlparse

import feedparser
import httpx


root_dir = Path(sys.argv[1])
sys.path.insert(0, str(root_dir))

from app.config import load_settings
from app.data.sql_client import SqlClient
from app.services.ai_client import invoke_model


def fail(message: str, code: int) -> None:
    print(f"ERROR: {message}")
    raise SystemExit(code)


EXPECTED_SCHEMA: dict[tuple[str, str], dict[str, set[str]]] = {
    ("SalesLT", "Product"): {
        "ProductID": {"int"},
        "Name": {"nvarchar", "varchar", "nchar", "char"},
        "ProductCategoryID": {"int"},
        "ProductModelID": {"int"},
    },
    ("SalesLT", "ProductCategory"): {
        "ProductCategoryID": {"int"},
        "Name": {"nvarchar", "varchar", "nchar", "char"},
    },
    ("SalesLT", "ProductDescription"): {
        "ProductDescriptionID": {"int"},
        "Description": {"nvarchar", "varchar", "ntext", "text"},
    },
    ("SalesLT", "ProductModel"): {
        "ProductModelID": {"int"},
        "Name": {"nvarchar", "varchar", "nchar", "char"},
    },
    ("SalesLT", "ProductModelProductDescription"): {
        "ProductModelID": {"int"},
        "ProductDescriptionID": {"int"},
        "Culture": {"nvarchar", "varchar", "nchar", "char"},
    },
    ("SalesLT", "Customer"): {
        "CustomerID": {"int"},
        "FirstName": {"nvarchar", "varchar", "nchar", "char"},
        "LastName": {"nvarchar", "varchar", "nchar", "char"},
        "CompanyName": {"nvarchar", "varchar", "nchar", "char"},
    },
    ("SalesLT", "CustomerAddress"): {
        "CustomerID": {"int"},
        "AddressID": {"int"},
    },
    ("SalesLT", "Address"): {
        "AddressID": {"int"},
        "City": {"nvarchar", "varchar", "nchar", "char"},
        "StateProvince": {"nvarchar", "varchar", "nchar", "char"},
    },
    ("SalesLT", "SalesOrderHeader"): {
        "SalesOrderID": {"int"},
        "CustomerID": {"int"},
        "OrderDate": {"date", "datetime", "datetime2", "smalldatetime", "datetimeoffset"},
        "TotalDue": {"decimal", "numeric", "money", "smallmoney", "float", "real"},
    },
    ("SalesLT", "SalesOrderDetail"): {
        "SalesOrderID": {"int"},
        "ProductID": {"int"},
    },
}

EXPECTED_AI_LOG_SCHEMA: dict[str, set[str]] = {
    "LogId": {"uniqueidentifier", "int", "bigint"},
    "StepName": {"nvarchar", "varchar", "nchar", "char"},
    "ModelName": {"nvarchar", "varchar", "nchar", "char"},
    "AIInputRaw": {"nvarchar", "varchar", "ntext", "text"},
    "AIOutputRaw": {"nvarchar", "varchar", "ntext", "text"},
    "ExecutionStatus": {"nvarchar", "varchar", "nchar", "char"},
    "ExecutionError": {"nvarchar", "varchar", "ntext", "text"},
    "ExecutedAtUtc": {"datetimeoffset", "datetime", "datetime2", "smalldatetime"},
    "ApiExecutionIdentity": {"nvarchar", "varchar", "nchar", "char"},
    "LoggedInUserIdentity": {"nvarchar", "varchar", "nchar", "char"},
    "CorrelationId": {"nvarchar", "varchar", "nchar", "char"},
}


settings = load_settings()
sql_client = SqlClient(settings)

# 1) Basic SQL connectivity.
try:
    ping = sql_client.query("SELECT TOP 1 1 AS ok")
except Exception as exc:  # pragma: no cover - runtime failure path
    fail(f"Azure SQL connectivity check failed: {exc}", 10)

if not ping or ping[0].get("ok") != 1:
    fail("Azure SQL connectivity check returned an unexpected result.", 11)

# 2) Validate existing schema-first business tables used by the codebase.
schema_errors: list[str] = []
for (schema_name, table_name), expected_columns in EXPECTED_SCHEMA.items():
    rows = sql_client.query(
        """
        SELECT COLUMN_NAME, DATA_TYPE
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ?
        """,
        (schema_name, table_name),
    )
    if not rows:
        schema_errors.append(f"Missing required table: {schema_name}.{table_name}")
        continue

    existing = {str(row["COLUMN_NAME"]): str(row["DATA_TYPE"]).lower() for row in rows}
    for column_name, accepted_types in expected_columns.items():
        actual_type = existing.get(column_name)
        if actual_type is None:
            schema_errors.append(f"Missing required column: {schema_name}.{table_name}.{column_name}")
            continue
        if actual_type not in accepted_types:
            accepted = ", ".join(sorted(accepted_types))
            schema_errors.append(
                f"Unexpected type for {schema_name}.{table_name}.{column_name}: "
                f"{actual_type} (expected one of: {accepted})"
            )

if schema_errors:
    joined = "\n  - ".join(schema_errors)
    fail(
        "Existing SalesLT business schema does not match the project design/code contract.\n"
        "Project design only allows automatic schema alignment for dbo.AIGenerationLog; "
        "fix the existing SalesLT business tables manually before redeploying.\n"
        "  - " + joined,
        12,
    )

# 3) Align AIGenerationLog with the minimum required schema.
migration_sql = (root_dir / "scripts/sql/001_ai_generation_log.sql").read_text(encoding="utf-8")
try:
    sql_client.execute(migration_sql)
except Exception as exc:  # pragma: no cover - runtime failure path
    fail(f"AIGenerationLog migration failed: {exc}", 13)

rows = sql_client.query(
    """
    SELECT COLUMN_NAME, DATA_TYPE
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = 'dbo' AND TABLE_NAME = 'AIGenerationLog'
    """
)
if not rows:
    fail("AIGenerationLog table was not found after running the alignment SQL.", 14)

existing_log_columns = {str(row["COLUMN_NAME"]): str(row["DATA_TYPE"]).lower() for row in rows}
log_errors: list[str] = []
for column_name, accepted_types in EXPECTED_AI_LOG_SCHEMA.items():
    actual_type = existing_log_columns.get(column_name)
    if actual_type is None:
        log_errors.append(f"Missing required column: dbo.AIGenerationLog.{column_name}")
        continue
    if actual_type not in accepted_types:
        accepted = ", ".join(sorted(accepted_types))
        log_errors.append(
            f"Unexpected type for dbo.AIGenerationLog.{column_name}: "
            f"{actual_type} (expected one of: {accepted})"
        )

if log_errors:
    joined = "\n  - ".join(log_errors)
    fail("AIGenerationLog schema is still incompatible after alignment.\n  - " + joined, 15)

# 4) Validate Azure OpenAI availability with the configured deployment.
try:
    openai_output = invoke_model(settings, "Reply with exactly: OK")
except Exception as exc:  # pragma: no cover - runtime failure path
    fail(f"Azure OpenAI validation call failed: {exc}", 16)

if not isinstance(openai_output, str) or not openai_output.strip():
    fail("Azure OpenAI validation returned empty output.", 17)

# 5) Validate Google News RSS and at least one downstream publisher fetch.
rss_url = (
    f"{settings.google_news_rss_base_url}?q={quote_plus('AI sales trend')}"
    "&hl=en-US&gl=US&ceid=US:en"
)
feed = feedparser.parse(rss_url)
entries = list(feed.entries)[:5]
if not entries:
    fail("Google News RSS returned no entries.", 18)

publisher_fetch_ok = False
last_fetch_error = "No publisher fetch was attempted."
for entry in entries:
    link = entry.get("link", "")
    parsed = urlparse(link)
    if "news.google.com" in parsed.netloc:
        target_url = parse_qs(parsed.query).get("url", [])
        if target_url:
            link = target_url[0]
    if not link:
        continue
    try:
        response = httpx.get(link, timeout=10.0, follow_redirects=True)
    except Exception as exc:  # pragma: no cover - runtime failure path
        last_fetch_error = str(exc)
        continue
    if response.status_code < 500 and len(response.text.strip()) >= 100:
        publisher_fetch_ok = True
        break
    last_fetch_error = f"status={response.status_code}, length={len(response.text.strip())}"

if not publisher_fetch_ok:
    fail(f"Publisher page fetch validation failed: {last_fetch_error}", 19)

print("Validated SalesLT schema, aligned AIGenerationLog, and confirmed SQL/OpenAI/RSS dependencies.")
PY
