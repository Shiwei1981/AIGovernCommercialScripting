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
require_commands az python3
az_login_with_service_principal

acr_login_server="${DEPLOY_ACR_LOGIN_SERVER#https://}"
acr_login_server="${acr_login_server#http://}"
acr_login_server="${acr_login_server%/}"
acr_name="${acr_login_server%%.*}"

resource_group_exists="$(az group exists --name "$DEPLOY_RESOURCE_GROUP" --output tsv --only-show-errors)"
[[ "$resource_group_exists" == "true" ]] || fail "Azure resource group not found: $DEPLOY_RESOURCE_GROUP"

plan_name="$(
  az appservice plan show \
    --resource-group "$DEPLOY_RESOURCE_GROUP" \
    --name "$DEPLOY_APP_SERVICE_PLAN" \
    --query name \
    --output tsv \
    --only-show-errors 2>/dev/null
)" || fail "Azure App Service plan not found: $DEPLOY_APP_SERVICE_PLAN"

webapp_json="$(
  az webapp show \
    --resource-group "$DEPLOY_RESOURCE_GROUP" \
    --name "$DEPLOY_WEBAPP_NAME" \
    --query "{name:name,kind:kind,state:state,reserved:reserved,serverFarmId:serverFarmId,appServicePlanId:appServicePlanId,defaultHostName:defaultHostName}" \
    --output json \
    --only-show-errors 2>/dev/null
)" || fail "Azure Web App not found: $DEPLOY_WEBAPP_NAME"

python3 - "$webapp_json" "$DEPLOY_APP_SERVICE_PLAN" <<'PY'
import json
import sys

payload = json.loads(sys.argv[1])
expected_plan = sys.argv[2]

name = payload.get("name", "")
reserved = payload.get("reserved")
server_farm_id = payload.get("serverFarmId") or payload.get("appServicePlanId", "")
state = payload.get("state", "")
default_host = payload.get("defaultHostName", "")
actual_plan = server_farm_id.rsplit("/", 1)[-1] if server_farm_id else ""

if not name:
    raise SystemExit("ERROR: Azure Web App payload did not contain a valid name.")
if reserved is not True:
    raise SystemExit("ERROR: Azure Web App is not a Linux Web App. Production deployment script assumes Linux App Service.")
if actual_plan != expected_plan:
    raise SystemExit(
        f"ERROR: Azure Web App is attached to plan '{actual_plan}', expected '{expected_plan}'."
    )

print(f"Validated Web App '{name}' on plan '{actual_plan}' (state={state}, host={default_host})")
PY

integrated_subnet_id="$(
  az webapp vnet-integration list \
    --resource-group "$DEPLOY_RESOURCE_GROUP" \
    --name "$DEPLOY_WEBAPP_NAME" \
    --query "[0].vnetResourceId" \
    --output tsv \
    --only-show-errors 2>/dev/null || true
)"
integrated_vnet_id="${integrated_subnet_id%/subnets/*}"

container_json="$(
  az webapp config show \
    --resource-group "$DEPLOY_RESOURCE_GROUP" \
    --name "$DEPLOY_WEBAPP_NAME" \
    --query "{linuxFxVersion:linuxFxVersion,acrUseManagedIdentityCreds:acrUseManagedIdentityCreds}" \
    --output json \
    --only-show-errors
)"

python3 - "$container_json" "$acr_login_server" "$DEPLOY_CONTAINER_IMAGE_REPOSITORY" <<'PY'
import json
import sys

payload = json.loads(sys.argv[1])
expected_registry = sys.argv[2].strip().lower()
expected_repo = sys.argv[3].strip().lower()
linux_fx = str(payload.get("linuxFxVersion") or "")
managed_identity = payload.get("acrUseManagedIdentityCreds")

if not linux_fx.upper().startswith("DOCKER|"):
    raise SystemExit("ERROR: Azure Web App is not configured as a custom container app.")

image_ref = linux_fx.split("|", 1)[1].strip().lower()
expected_prefix = f"{expected_registry}/{expected_repo}:"
if not image_ref.startswith(expected_prefix):
    raise SystemExit(
        "ERROR: Azure Web App container image does not point to the expected ACR repository. "
        f"Current image='{image_ref}', expected prefix='{expected_prefix}'."
    )

if managed_identity is not True:
    raise SystemExit(
        "ERROR: Azure Web App is not configured to pull the container image with managed identity."
    )
PY

acr_json="$(
  az acr show \
    --name "$acr_name" \
    --query "{name:name,loginServer:loginServer}" \
    --output json \
    --only-show-errors 2>/dev/null
)" || fail "Azure Container Registry not found: $acr_name"

python3 - "$acr_json" "$acr_login_server" <<'PY'
import json
import sys

payload = json.loads(sys.argv[1])
expected_registry = sys.argv[2].strip().lower()
actual_registry = str(payload.get("loginServer") or "").strip().lower()

if actual_registry != expected_registry:
    raise SystemExit(
        f"ERROR: Azure Container Registry login server mismatch: actual='{actual_registry}', expected='{expected_registry}'."
    )

print(f"Validated Azure Container Registry '{payload.get('name')}' ({actual_registry})")
PY

sql_server_name="${SQL_SERVER%%.*}"
sql_server_rg="$(
  az resource list \
    --name "$sql_server_name" \
    --resource-type "Microsoft.Sql/servers" \
    --query "[0].resourceGroup" \
    --output tsv \
    --only-show-errors
)"
[[ -n "$sql_server_rg" ]] || fail "Azure SQL server resource was not found for: $sql_server_name"

sql_public_network_access="$(
  az sql server show \
    --resource-group "$sql_server_rg" \
    --name "$sql_server_name" \
    --query publicNetworkAccess \
    --output tsv \
    --only-show-errors
)"

if [[ "${sql_public_network_access,,}" == "disabled" ]]; then
  [[ -n "$integrated_subnet_id" ]] || fail "Azure SQL public access is disabled, but Azure Web App has no VNet Integration configured."
  [[ -n "$integrated_vnet_id" ]] || fail "Unable to determine the integrated VNet resource ID for Azure Web App."

  sql_dns_zone_rg="$(
    az network private-dns zone list \
      --query "[?name=='privatelink.database.windows.net'] | [0].resourceGroup" \
      --output tsv \
      --only-show-errors
  )"
  [[ -n "$sql_dns_zone_rg" ]] || fail "Azure SQL public access is disabled, but no 'privatelink.database.windows.net' Private DNS zone was found."

  sql_dns_link_count="$(
    az network private-dns link vnet list \
      --resource-group "$sql_dns_zone_rg" \
      --zone-name privatelink.database.windows.net \
      --query "[?virtualNetwork.id=='$integrated_vnet_id'] | length(@)" \
      --output tsv \
      --only-show-errors
  )"
  [[ "$sql_dns_link_count" != "0" ]] || fail "Azure SQL public access is disabled, but the integrated VNet is not linked to 'privatelink.database.windows.net'."
fi

expected_host="$(
  python3 - "$DEPLOY_APP_BASE_URL" <<'PY'
from urllib.parse import urlparse
import sys

host = urlparse(sys.argv[1]).netloc.strip().lower()
if not host:
    raise SystemExit("ERROR: APP_BASE_URL is invalid and does not contain a hostname.")
print(host)
PY
)"

hostname_bindings="$(
  az webapp config hostname list \
    --resource-group "$DEPLOY_RESOURCE_GROUP" \
    --webapp-name "$DEPLOY_WEBAPP_NAME" \
    --query "[].name" \
    --output tsv \
    --only-show-errors
)"

if ! grep -Fxiq "$expected_host" <<<"$hostname_bindings"; then
  fail "APP_BASE_URL host '$expected_host' is not bound to Azure Web App '$DEPLOY_WEBAPP_NAME'."
fi

echo "Validated Azure resource group, App Service plan, Web App, ACR, SQL private DNS prerequisites, and hostname binding."
