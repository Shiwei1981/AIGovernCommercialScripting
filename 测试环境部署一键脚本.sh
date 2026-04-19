#!/usr/bin/env bash
# One-click deployment script for Linux test environment.
# This script MUST NOT create cloud resources. It only validates and starts the app.

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

ENV_FILE="$ROOT_DIR/.env.local"
LOG_DIR="$ROOT_DIR/logs"
APP_LOG="$LOG_DIR/test-env-app.log"
PID_FILE="$ROOT_DIR/.test_env_app.pid"

echo "[STEP 1/8] Loading environment variables from .env.local"
if [[ ! -f "$ENV_FILE" ]]; then
  echo "ERROR: .env.local was not found at $ENV_FILE"
  exit 1
fi

set -a
source "$ENV_FILE"
set +a

REQUIRED_VARS=(
  APP_ENV
  WEB_APP_PORT
  AZURE_TENANT_ID
  AZURE_CLIENT_ID
  AZURE_CLIENT_SECRET
  OIDC_AUTHORITY_URL
  OIDC_CALLBACK_URL_TEST
  OIDC_CALLBACK_URL_PROD
  SQL_SERVER
  SQL_DATABASE
  OPENAI_ENDPOINT
  OPENAI_API_VERSION
  OPENAI_DEPLOYMENT
  GOOGLE_NEWS_RSS_BASE_URL
)

MISSING_VARS=()
for var_name in "${REQUIRED_VARS[@]}"; do
  if [[ -z "${!var_name:-}" ]]; then
    MISSING_VARS+=("$var_name")
  fi
done

if [[ ${#MISSING_VARS[@]} -gt 0 ]]; then
  echo "ERROR: Missing required environment variables in .env.local:"
  printf '  - %s\n' "${MISSING_VARS[@]}"
  exit 2
fi

PLACEHOLDER_VARS=()
for var_name in "${REQUIRED_VARS[@]}"; do
  var_value="${!var_name}"
  if [[ "$var_value" =~ your- ]] || [[ "$var_value" =~ changeme ]] || [[ "$var_value" =~ \<.*\> ]]; then
    PLACEHOLDER_VARS+=("$var_name")
  fi
done

if [[ ${#PLACEHOLDER_VARS[@]} -gt 0 ]]; then
  echo "ERROR: Placeholder-like values detected in .env.local:"
  printf '  - %s\n' "${PLACEHOLDER_VARS[@]}"
  echo "Please replace them with real test-environment values."
  exit 3
fi

if [[ "${APP_ENV}" != "test" && "${MOCK_AUTH_ENABLED}" == "true" ]]; then
  echo "ERROR: MOCK_AUTH_ENABLED=true is not allowed when APP_ENV=${APP_ENV}."
  echo "Set MOCK_AUTH_ENABLED=false for Linux manual UI self-test deployment."
  exit 5
fi

if [[ -z "${SQL_MAX_ROWS:-}" ]]; then
  export SQL_MAX_ROWS="${MAX_AI_SQL_ROWS:-1000}"
fi

echo "[STEP 2/8] Preparing local Python runtime"
if [[ ! -d "$ROOT_DIR/.venv" ]]; then
  python3 -m venv "$ROOT_DIR/.venv"
fi
source "$ROOT_DIR/.venv/bin/activate"
python -m pip install --upgrade pip >/dev/null
pip install -r "$ROOT_DIR/requirements.txt" >/dev/null

: <<'STEP3_DISABLED'
echo "[STEP 3/8] Verifying Azure SQL / OpenAI / RSS dependencies and DB schema"
python - <<'PY'
import sys
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import feedparser
import httpx

from app.config import load_settings
from app.data.sql_client import SqlClient
from app.services.ai_client import invoke_model

def fail(message: str, code: int = 10) -> None:
    print(f"ERROR: {message}")
    sys.exit(code)

settings = load_settings()
sql_client = SqlClient(settings)

# 1) Basic SQL connectivity
try:
    ping = sql_client.query("SELECT TOP 1 1 AS ok")
except Exception as exc:
    fail(f"Azure SQL connectivity check failed: {exc}", 11)

if not ping or ping[0].get("ok") != 1:
    fail("Azure SQL connectivity check returned unexpected result.", 12)

# 2) Verify required business tables and columns
required_schema = {
    ("SalesLT", "Product"): ["ProductID", "Name", "ProductCategoryID", "ProductModelID"],
    ("SalesLT", "ProductCategory"): ["ProductCategoryID", "Name"],
    ("SalesLT", "ProductDescription"): ["ProductDescriptionID", "Description"],
    ("SalesLT", "ProductModel"): ["ProductModelID", "Name"],
    ("SalesLT", "ProductModelProductDescription"): ["ProductModelID", "ProductDescriptionID", "Culture"],
    ("SalesLT", "Customer"): ["CustomerID", "FirstName", "LastName", "CompanyName"],
    ("SalesLT", "CustomerAddress"): ["CustomerID", "AddressID"],
    ("SalesLT", "Address"): ["AddressID", "City", "StateProvince"],
    ("SalesLT", "SalesOrderHeader"): ["SalesOrderID", "CustomerID", "OrderDate", "TotalDue"],
    ("SalesLT", "SalesOrderDetail"): ["SalesOrderID", "ProductID"],
}

for (schema_name, table_name), required_columns in required_schema.items():
    rows = sql_client.query(
        """
        SELECT COLUMN_NAME
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ?
        """,
        (schema_name, table_name),
    )
    existing = {row["COLUMN_NAME"] for row in rows}
    missing = [col for col in required_columns if col not in existing]
    if missing:
        fail(f"Schema mismatch for {schema_name}.{table_name}, missing columns: {missing}", 13)

# 3) Align AIGenerationLog structure with code expectations
migration_sql = Path("scripts/sql/001_ai_generation_log.sql").read_text(encoding="utf-8")
try:
    sql_client.execute(migration_sql)
except Exception as exc:
    fail(f"AIGenerationLog migration failed: {exc}", 14)

required_log_columns = ["AIInputRaw", "AIOutputRaw", "ExecutionError", "LoggedInUserIdentity", "CorrelationId"]
log_rows = sql_client.query(
    """
    SELECT COLUMN_NAME
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_NAME = 'AIGenerationLog'
    """
)
existing_log_cols = {row["COLUMN_NAME"] for row in log_rows}
missing_log_cols = [col for col in required_log_columns if col not in existing_log_cols]
if missing_log_cols:
    fail(f"AIGenerationLog still missing required columns: {missing_log_cols}", 15)

# 4) Validate Azure OpenAI availability
try:
    openai_output = invoke_model(settings, "Reply with exactly: OK")
except Exception as exc:
    fail(f"Azure OpenAI validation call failed: {exc}", 16)

if not isinstance(openai_output, str) or not openai_output.strip():
    fail("Azure OpenAI validation returned empty output.", 17)

# 5) Validate Google News RSS and publisher-page fetch
rss_url = f"{settings.google_news_rss_base_url}?q=AI+sales+trend&hl=en-US&gl=US&ceid=US:en"
parsed = feedparser.parse(rss_url)
entries = list(parsed.entries)[:5]
if not entries:
    fail("Google News RSS returned no entries.", 18)

link = entries[0].get("link", "")
parsed_link = urlparse(link)
if "news.google.com" in parsed_link.netloc:
    q = parse_qs(parsed_link.query).get("url", [])
    if q:
        link = q[0]

try:
    resp = httpx.get(link, timeout=10.0, follow_redirects=True)
except Exception as exc:
    fail(f"Publisher page fetch failed: {exc}", 19)

if resp.status_code >= 500 or len(resp.text.strip()) < 100:
    fail(
        f"Publisher page fetch returned insufficient content: status={resp.status_code}, length={len(resp.text)}",
        20,
    )

print("Dependency and schema validation passed.")
PY
STEP3_DISABLED

echo "[STEP 4/8] Ensuring no stale test server process is referenced"
if [[ -f "$PID_FILE" ]]; then
  old_pid="$(cat "$PID_FILE" || true)"
  if [[ -n "${old_pid:-}" ]] && kill -0 "$old_pid" 2>/dev/null; then
    echo "Stopping stale process: $old_pid"
    kill "$old_pid"
    sleep 2
  fi
  rm -f "$PID_FILE"
fi

echo "[STEP 5/8] Starting application service (console attached)"
mkdir -p "$LOG_DIR"
: > "$APP_LOG"
PYTHONUNBUFFERED=1 python -m app.main \
  > >(tee -a "$APP_LOG") \
  2> >(tee -a "$APP_LOG" >&2) &
new_pid=$!
echo "$new_pid" > "$PID_FILE"

stopped_by_signal=0
cleanup_pid_file() {
  rm -f "$PID_FILE"
}

stop_service() {
  stopped_by_signal=1
  if kill -0 "$new_pid" 2>/dev/null; then
    echo
    echo "Stopping service process: $new_pid"
    if ! kill "$new_pid" 2>/dev/null; then
      echo "Service process $new_pid was already stopped."
    fi
  fi
}

trap cleanup_pid_file EXIT
trap stop_service INT TERM

echo "[STEP 6/8] Waiting for service readiness"
max_wait=60
ready=0
for ((i=1; i<=max_wait; i++)); do
  if ! kill -0 "$new_pid" 2>/dev/null; then
    echo "ERROR: Service process exited before readiness check passed."
    echo "----- Last 80 lines of app log -----"
    tail -n 80 "$APP_LOG" || true
    exit 4
  fi
  if curl -fsS "http://127.0.0.1:${WEB_APP_PORT}/api/session" >/dev/null 2>&1; then
    ready=1
    break
  fi
  sleep 1
done

if [[ "$ready" -ne 1 ]]; then
  echo "ERROR: Service did not become ready within ${max_wait}s."
  echo "----- Last 80 lines of app log -----"
  tail -n 80 "$APP_LOG" || true
  exit 4
fi

echo "[STEP 7/8] Service is running"
echo "PID: $new_pid"
echo "URL: http://127.0.0.1:${WEB_APP_PORT}"
echo "Log: $APP_LOG"

echo "[STEP 8/8] Console output attached (Press Ctrl+C to stop service)"
echo "Next: follow '测试环境部署手册.md' for manual UI self-test steps."

set +e
wait "$new_pid"
app_exit_code=$?
set -e

if [[ "$stopped_by_signal" -eq 1 ]]; then
  echo "Service stopped by user."
  exit 0
fi

if [[ "$app_exit_code" -ne 0 ]]; then
  echo "Service exited unexpectedly with code: $app_exit_code"
fi

exit "$app_exit_code"
