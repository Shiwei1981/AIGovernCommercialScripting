#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/common.sh"
cd "$ROOT_DIR"

load_env_file
validate_runtime_env
validate_deploy_env
assert_prod_safe_flags
require_commands curl python3

BASE_URL="${DEPLOY_APP_BASE_URL%/}"
SESSION_FILE="$(mktemp)"
PROTECTED_FILE="$(mktemp)"
HOME_FILE="$(mktemp)"
trap 'rm -f "$SESSION_FILE" "$PROTECTED_FILE" "$HOME_FILE"' EXIT

if ! [[ "$DEPLOY_SMOKE_MAX_RETRIES" =~ ^[0-9]+$ ]] || ! [[ "$DEPLOY_SMOKE_RETRY_INTERVAL_SEC" =~ ^[0-9]+$ ]]; then
  fail "SMOKE retry configuration must be numeric."
fi

for ((attempt = 1; attempt <= DEPLOY_SMOKE_MAX_RETRIES; attempt++)); do
  home_status="$(curl -sS -L -o "$HOME_FILE" -w '%{http_code}' "$BASE_URL/" || true)"
  session_status="$(curl -sS -o "$SESSION_FILE" -w '%{http_code}' "$BASE_URL/api/session" || true)"
  protected_status="$(curl -sS -o "$PROTECTED_FILE" -w '%{http_code}' "$BASE_URL/api/products/bootstrap" || true)"

  if [[ "$home_status" == "200" ]] &&
    [[ "$session_status" == "200" ]] &&
    grep -q '"authenticated":[[:space:]]*false' "$SESSION_FILE" &&
    [[ "$protected_status" == "401" ]]; then
    echo "Production smoke test passed for $BASE_URL"
    exit 0
  fi

  if (( attempt < DEPLOY_SMOKE_MAX_RETRIES )); then
    sleep "$DEPLOY_SMOKE_RETRY_INTERVAL_SEC"
  fi
done

echo "----- Last smoke test responses -----" >&2
echo "GET /                -> $home_status" >&2
echo "GET /api/session     -> $session_status" >&2
echo "GET /api/products/bootstrap -> $protected_status" >&2
echo "--- /api/session body ---" >&2
cat "$SESSION_FILE" >&2 || true
echo >&2
echo "--- /api/products/bootstrap body ---" >&2
cat "$PROTECTED_FILE" >&2 || true
echo >&2

fail "Production smoke test failed for $BASE_URL"
