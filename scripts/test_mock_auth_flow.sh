#!/usr/bin/env bash
set -euo pipefail

# Test-only smoke flow using mock auth. Requires APP_ENV=test and MOCK_AUTH_ENABLED=true.
BASE_URL="${BASE_URL:-http://localhost:${WEB_APP_PORT:-8000}}"
COOKIE_JAR="mock-smoke.cookies"

if [[ "${APP_ENV:-}" != "test" || "${MOCK_AUTH_ENABLED:-}" != "true" ]]; then
  echo "This script requires APP_ENV=test and MOCK_AUTH_ENABLED=true."
  exit 1
fi

echo "[1/4] establish mock session"
curl -sS -i -c "$COOKIE_JAR" "$BASE_URL/auth/callback?mock_user=mock-smoke-user" | grep -q "302"

echo "[2/4] bootstrap"
curl -sS -b "$COOKIE_JAR" "$BASE_URL/api/products/bootstrap" | grep -q "product_id"

echo "[3/4] customer query"
curl -sS -b "$COOKIE_JAR" -H "Content-Type: application/json" \
  -d '{"customer_description":"high value retailer"}' \
  "$BASE_URL/api/customers/query" | grep -q "generated_sql"

echo "[4/4] reset"
curl -sS -b "$COOKIE_JAR" -X POST "$BASE_URL/api/reset" | grep -q "\"ok\""

echo "Mock-auth smoke flow passed."
