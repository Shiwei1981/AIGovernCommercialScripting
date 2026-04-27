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
az_login_with_service_principal

az webapp config set \
  --resource-group "$DEPLOY_RESOURCE_GROUP" \
  --name "$DEPLOY_WEBAPP_NAME" \
  --startup-file "$DEPLOY_APP_STARTUP_COMMAND" \
  --always-on true \
  --http20-enabled true \
  --only-show-errors >/dev/null

az webapp config appsettings set \
  --resource-group "$DEPLOY_RESOURCE_GROUP" \
  --name "$DEPLOY_WEBAPP_NAME" \
  --settings \
    APP_ENV="$DEPLOY_APP_ENV" \
    WEB_APP_PORT="$WEB_APP_PORT" \
    WEBSITES_PORT="$WEB_APP_PORT" \
    AZURE_TENANT_ID="$AZURE_TENANT_ID" \
    AZURE_CLIENT_ID="$AZURE_CLIENT_ID" \
    AZURE_CLIENT_SECRET="$AZURE_CLIENT_SECRET" \
    OIDC_AUTHORITY_URL="$OIDC_AUTHORITY_URL" \
    OIDC_CALLBACK_URL_TEST="$OIDC_CALLBACK_URL_TEST" \
    OIDC_CALLBACK_URL_PROD="$OIDC_CALLBACK_URL_PROD" \
    SQL_SERVER="$SQL_SERVER" \
    SQL_DATABASE="$SQL_DATABASE" \
    OPENAI_ENDPOINT="$OPENAI_ENDPOINT" \
    OPENAI_API_VERSION="$OPENAI_API_VERSION" \
    OPENAI_DEPLOYMENT="$OPENAI_DEPLOYMENT" \
    GOOGLE_NEWS_RSS_BASE_URL="$GOOGLE_NEWS_RSS_BASE_URL" \
    SQL_MAX_ROWS="$DEPLOY_SQL_MAX_ROWS" \
    MOCK_AUTH_ENABLED="$DEPLOY_MOCK_AUTH_ENABLED" \
    DB_READ_GOVERNANCE_ENABLED="$DEPLOY_DB_READ_GOVERNANCE_ENABLED" \
    QUERYVISIBILITY_API_URL="$QUERYVISIBILITY_API_URL" \
    QUERYVISIBILITY_OPENAPI_URL="$QUERYVISIBILITY_OPENAPI_URL" \
    QUERYVISIBILITY_OPENAPI_PATH="$QUERYVISIBILITY_OPENAPI_PATH" \
    MASK_API_URL="$MASK_API_URL" \
    MASK_OPENAPI_URL="$MASK_OPENAPI_URL" \
    MASK_OPENAPI_PATH="$MASK_OPENAPI_PATH" \
    WEBSITE_DNS_SERVER=168.63.129.16 \
    SCM_DO_BUILD_DURING_DEPLOYMENT=false \
    ENABLE_ORYX_BUILD=false \
    PYTHONUNBUFFERED=1 \
  --only-show-errors >/dev/null

echo "Applied production app settings to Azure Web App: $DEPLOY_WEBAPP_NAME"
