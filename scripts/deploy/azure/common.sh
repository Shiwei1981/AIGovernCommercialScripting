#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
DEFAULT_ENV_FILE="$ROOT_DIR/.env.local"
VENV_PYTHON="$ROOT_DIR/.venv/bin/python"
VENV_PIP="$ROOT_DIR/.venv/bin/pip"

RUNTIME_REQUIRED_VARS=(
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

DEPLOY_REQUIRED_VARS=(
  DEPLOY_AZ_SUBSCRIPTION_ID
  DEPLOY_RESOURCE_GROUP
  DEPLOY_APP_SERVICE_PLAN
  DEPLOY_WEBAPP_NAME
  DEPLOY_APP_BASE_URL
  DEPLOY_AZ_DEPLOY_TENANT_ID
  DEPLOY_AZ_DEPLOY_CLIENT_ID
  DEPLOY_AZ_DEPLOY_CLIENT_SECRET
  DEPLOY_ACR_LOGIN_SERVER
  DEPLOY_CONTAINER_IMAGE_REPOSITORY
)

fail() {
  echo "ERROR: $*" >&2
  exit 1
}

resolve_value() {
  local preferred_name="$1"
  local fallback_name="$2"
  local default_value="${3-}"
  local value="${!preferred_name:-}"
  if [[ -n "$value" ]]; then
    printf '%s' "$value"
    return
  fi

  value="${!fallback_name:-}"
  if [[ -n "$value" ]]; then
    printf '%s' "$value"
    return
  fi

  printf '%s' "$default_value"
}

load_env_file() {
  local env_file="${ENV_FILE:-$DEFAULT_ENV_FILE}"
  [[ -f "$env_file" ]] || fail ".env.local was not found at $env_file"

  set -a
  # shellcheck disable=SC1090
  source "$env_file"
  set +a

  export ENV_FILE="$env_file"
  export DEPLOY_APP_ENV
  DEPLOY_APP_ENV="$(resolve_value PROD_APP_ENV APP_ENV production)"
  export DEPLOY_MOCK_AUTH_ENABLED
  DEPLOY_MOCK_AUTH_ENABLED="$(resolve_value PROD_MOCK_AUTH_ENABLED MOCK_AUTH_ENABLED false)"
  export DEPLOY_AZ_SUBSCRIPTION_ID
  DEPLOY_AZ_SUBSCRIPTION_ID="$(resolve_value PROD_AZ_SUBSCRIPTION_ID AZ_SUBSCRIPTION_ID "")"
  export DEPLOY_RESOURCE_GROUP
  DEPLOY_RESOURCE_GROUP="$(resolve_value PROD_AZ_RESOURCE_GROUP RESOURCE_GROUP "${AZ_RESOURCE_GROUP:-}")"
  export DEPLOY_APP_SERVICE_PLAN
  DEPLOY_APP_SERVICE_PLAN="$(resolve_value PROD_AZ_APP_SERVICE_PLAN AZ_APP_SERVICE_PLAN "")"
  export DEPLOY_WEBAPP_NAME
  DEPLOY_WEBAPP_NAME="$(resolve_value PROD_AZ_WEBAPP_NAME WEBAPP_NAME "${AZ_WEBAPP_NAME:-}")"
  export DEPLOY_APP_STARTUP_COMMAND
  DEPLOY_APP_STARTUP_COMMAND="$(resolve_value PROD_APP_STARTUP_COMMAND APP_STARTUP_COMMAND "python -m app.main")"
  export DEPLOY_APP_BASE_URL
  DEPLOY_APP_BASE_URL="$(resolve_value PROD_APP_BASE_URL APP_BASE_URL "")"
  export DEPLOY_AZ_DEPLOY_TENANT_ID
  DEPLOY_AZ_DEPLOY_TENANT_ID="$(resolve_value PROD_AZ_DEPLOY_TENANT_ID AZ_DEPLOY_TENANT_ID "")"
  export DEPLOY_AZ_DEPLOY_CLIENT_ID
  DEPLOY_AZ_DEPLOY_CLIENT_ID="$(resolve_value PROD_AZ_DEPLOY_CLIENT_ID AZ_DEPLOY_CLIENT_ID "")"
  export DEPLOY_AZ_DEPLOY_CLIENT_SECRET
  DEPLOY_AZ_DEPLOY_CLIENT_SECRET="$(resolve_value PROD_AZ_DEPLOY_CLIENT_SECRET AZ_DEPLOY_CLIENT_SECRET "")"
  export DEPLOY_ACR_LOGIN_SERVER
  DEPLOY_ACR_LOGIN_SERVER="$(resolve_value PROD_ACR_LOGIN_SERVER ACR_LOGIN_SERVER "")"
  export DEPLOY_CONTAINER_IMAGE_REPOSITORY
  DEPLOY_CONTAINER_IMAGE_REPOSITORY="$(resolve_value PROD_CONTAINER_IMAGE_REPOSITORY CONTAINER_IMAGE_REPOSITORY "")"
  export DEPLOY_CONTAINER_IMAGE_TAG
  DEPLOY_CONTAINER_IMAGE_TAG="$(resolve_value PROD_CONTAINER_IMAGE_TAG CONTAINER_IMAGE_TAG "")"
  export DEPLOY_SMOKE_MAX_RETRIES
  DEPLOY_SMOKE_MAX_RETRIES="$(resolve_value PROD_SMOKE_MAX_RETRIES SMOKE_MAX_RETRIES 60)"
  export DEPLOY_SMOKE_RETRY_INTERVAL_SEC
  DEPLOY_SMOKE_RETRY_INTERVAL_SEC="$(resolve_value PROD_SMOKE_RETRY_INTERVAL_SEC SMOKE_RETRY_INTERVAL_SEC 10)"
  export DEPLOY_SQL_MAX_ROWS
  DEPLOY_SQL_MAX_ROWS="$(resolve_value PROD_SQL_MAX_ROWS SQL_MAX_ROWS "${MAX_AI_SQL_ROWS:-100}")"
}

require_commands() {
  local missing=()
  local command_name
  for command_name in "$@"; do
    if ! command -v "$command_name" >/dev/null 2>&1; then
      missing+=("$command_name")
    fi
  done
  if [[ ${#missing[@]} -gt 0 ]]; then
    fail "Missing required command(s): ${missing[*]}"
  fi
}

require_non_empty_vars() {
  local missing=()
  local var_name
  for var_name in "$@"; do
    if [[ -z "${!var_name:-}" ]]; then
      missing+=("$var_name")
    fi
  done
  if [[ ${#missing[@]} -gt 0 ]]; then
    printf 'Missing required environment variable(s) in %s:\n' "${ENV_FILE:-$DEFAULT_ENV_FILE}" >&2
    printf '  - %s\n' "${missing[@]}" >&2
    exit 2
  fi
}

require_no_placeholder_vars() {
  local suspicious=()
  local var_name
  local value
  local lowered
  for var_name in "$@"; do
    value="${!var_name:-}"
    [[ -z "$value" ]] && continue
    lowered="${value,,}"
    if [[ "$lowered" == *your-* ]] ||
      [[ "$lowered" == *changeme* ]] ||
      [[ "$lowered" == *replace-me* ]] ||
      [[ "$lowered" == *replace_me* ]] ||
      ([[ "$value" == \<* ]] && [[ "$value" == *\> ]]); then
      suspicious+=("$var_name")
    fi
  done
  if [[ ${#suspicious[@]} -gt 0 ]]; then
    printf 'Placeholder-like values detected in %s:\n' "${ENV_FILE:-$DEFAULT_ENV_FILE}" >&2
    printf '  - %s\n' "${suspicious[@]}" >&2
    exit 3
  fi
}

validate_runtime_env() {
  require_non_empty_vars "${RUNTIME_REQUIRED_VARS[@]}"
  require_no_placeholder_vars "${RUNTIME_REQUIRED_VARS[@]}"
}

validate_deploy_env() {
  local missing=()
  [[ -n "${DEPLOY_AZ_SUBSCRIPTION_ID:-}" ]] || missing+=("AZ_SUBSCRIPTION_ID")
  [[ -n "${DEPLOY_RESOURCE_GROUP:-}" ]] || missing+=("AZ_RESOURCE_GROUP")
  [[ -n "${DEPLOY_APP_SERVICE_PLAN:-}" ]] || missing+=("AZ_APP_SERVICE_PLAN")
  [[ -n "${DEPLOY_WEBAPP_NAME:-}" ]] || missing+=("AZ_WEBAPP_NAME")
  [[ -n "${DEPLOY_APP_BASE_URL:-}" ]] || missing+=("APP_BASE_URL / PROD_APP_BASE_URL")
  [[ -n "${DEPLOY_AZ_DEPLOY_TENANT_ID:-}" ]] || missing+=("AZ_DEPLOY_TENANT_ID")
  [[ -n "${DEPLOY_AZ_DEPLOY_CLIENT_ID:-}" ]] || missing+=("AZ_DEPLOY_CLIENT_ID")
  [[ -n "${DEPLOY_AZ_DEPLOY_CLIENT_SECRET:-}" ]] || missing+=("AZ_DEPLOY_CLIENT_SECRET")
  [[ -n "${DEPLOY_ACR_LOGIN_SERVER:-}" ]] || missing+=("PROD_ACR_LOGIN_SERVER")
  [[ -n "${DEPLOY_CONTAINER_IMAGE_REPOSITORY:-}" ]] || missing+=("PROD_CONTAINER_IMAGE_REPOSITORY")
  if [[ ${#missing[@]} -gt 0 ]]; then
    printf 'Missing required environment variable(s) in %s:\n' "${ENV_FILE:-$DEFAULT_ENV_FILE}" >&2
    printf '  - %s\n' "${missing[@]}" >&2
    exit 2
  fi
  require_no_placeholder_vars "${DEPLOY_REQUIRED_VARS[@]}"
}

assert_prod_safe_flags() {
  if [[ "${DEPLOY_MOCK_AUTH_ENABLED,,}" == "true" ]]; then
    fail "PROD_MOCK_AUTH_ENABLED/MOCK_AUTH_ENABLED must be false for production deployment."
  fi
}

ensure_python_runtime() {
  require_commands python3
  if [[ ! -x "$VENV_PYTHON" ]]; then
    python3 -m venv "$ROOT_DIR/.venv"
  fi
  "$VENV_PYTHON" -m pip install --upgrade pip >/dev/null
  "$VENV_PIP" install -r "$ROOT_DIR/requirements.txt" >/dev/null
}

az_login_with_service_principal() {
  require_commands az
  require_non_empty_vars \
    DEPLOY_AZ_SUBSCRIPTION_ID \
    DEPLOY_AZ_DEPLOY_TENANT_ID \
    DEPLOY_AZ_DEPLOY_CLIENT_ID \
    DEPLOY_AZ_DEPLOY_CLIENT_SECRET

  local current_subscription=""
  local current_tenant=""
  local current_user=""

  current_subscription="$(az account show --query id -o tsv --only-show-errors 2>/dev/null || true)"
  current_tenant="$(az account show --query tenantId -o tsv --only-show-errors 2>/dev/null || true)"
  current_user="$(az account show --query user.name -o tsv --only-show-errors 2>/dev/null || true)"

  if [[ "$current_subscription" != "$DEPLOY_AZ_SUBSCRIPTION_ID" ]] ||
    [[ "$current_tenant" != "$DEPLOY_AZ_DEPLOY_TENANT_ID" ]] ||
    [[ "$current_user" != "$DEPLOY_AZ_DEPLOY_CLIENT_ID" ]]; then
    az login \
      --service-principal \
      --username "$DEPLOY_AZ_DEPLOY_CLIENT_ID" \
      --password "$DEPLOY_AZ_DEPLOY_CLIENT_SECRET" \
      --tenant "$DEPLOY_AZ_DEPLOY_TENANT_ID" \
      --only-show-errors >/dev/null
  fi

  az account set --subscription "$DEPLOY_AZ_SUBSCRIPTION_ID" --only-show-errors
}
