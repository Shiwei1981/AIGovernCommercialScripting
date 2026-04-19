#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:${WEB_APP_PORT:-8000}}"
COOKIE_JAR="smoke.cookies"
APP_ENV_VALUE="${APP_ENV:-dev}"
MOCK_AUTH_VALUE="${MOCK_AUTH_ENABLED:-false}"

echo "[1/7] session check"
curl -sS -c "$COOKIE_JAR" "$BASE_URL/api/session" | grep -q "authenticated"

if [[ "${APP_ENV_VALUE}" == "test" && "${MOCK_AUTH_VALUE}" == "true" ]]; then
  echo "[2/7] mock login (test mode)"
  curl -sS -i -b "$COOKIE_JAR" -c "$COOKIE_JAR" \
    "$BASE_URL/auth/callback?mock_user=smoke-user" | grep -q "302"
else
  echo "[2/7] real login required"
  if [[ -z "${SESSION_ID:-}" ]]; then
    echo "SESSION_ID is required for non-test smoke runs."
    echo "Sign in via browser, copy session_id cookie value, then run:"
    echo "SESSION_ID=<cookie-value> ./scripts/smoke_happy_path.sh"
    exit 1
  fi
  cat > "$COOKIE_JAR" <<EOF
# Netscape HTTP Cookie File
localhost	FALSE	/	FALSE	0	session_id	${SESSION_ID}
EOF
fi

echo "[3/7] bootstrap"
curl -sS -b "$COOKIE_JAR" "$BASE_URL/api/products/bootstrap" | grep -q "product_id"

echo "[4/7] customer query"
curl -sS -b "$COOKIE_JAR" -H "Content-Type: application/json" \
  -d '{"customer_description":"high value retailer"}' \
  "$BASE_URL/api/customers/query" | grep -q "generated_sql"

echo "[5/7] customer analysis"
curl -sS -b "$COOKIE_JAR" -X POST "$BASE_URL/api/customers/1/analysis" | grep -q "analysis_text"

echo "[6/7] trend search"
curl -sS -b "$COOKIE_JAR" -H "Content-Type: application/json" \
  -d '{"product_id":1}' "$BASE_URL/api/trends/search" | grep -q "summary_text"

echo "[7/7] ad copy and reset"
curl -sS -b "$COOKIE_JAR" -H "Content-Type: application/json" \
  -d '{"customer_description":"demo","customer_id":1,"product_id":1,"trend_summary":"demo summary"}' \
  "$BASE_URL/api/ad-copy/generate" | grep -q "ad_copy_text"
curl -sS -b "$COOKIE_JAR" -X POST "$BASE_URL/api/reset" | grep -q "\"ok\""

echo "Smoke happy path passed."
