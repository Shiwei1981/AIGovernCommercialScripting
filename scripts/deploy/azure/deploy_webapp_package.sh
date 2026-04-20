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

ARTIFACT_DIR="$ROOT_DIR/build/prod-deploy"
mkdir -p "$ARTIFACT_DIR"

acr_login_server="${DEPLOY_ACR_LOGIN_SERVER#https://}"
acr_login_server="${acr_login_server#http://}"
acr_login_server="${acr_login_server%/}"
acr_name="${acr_login_server%%.*}"
version_tag="$(tr -d '[:space:]' < "$ROOT_DIR/VERSION")"
[[ -n "$version_tag" ]] || fail "VERSION file is empty."

image_tag="$DEPLOY_CONTAINER_IMAGE_TAG"
if [[ -z "$image_tag" ]]; then
  image_tag="${version_tag}-$(date -u +%Y%m%d%H%M%S)"
fi
image_ref="${acr_login_server}/${DEPLOY_CONTAINER_IMAGE_REPOSITORY}:${image_tag}"
printf '%s\n' "$image_ref" > "$ARTIFACT_DIR/last-image.txt"

az acr build \
  --registry "$acr_name" \
  --image "${DEPLOY_CONTAINER_IMAGE_REPOSITORY}:${image_tag}" \
  --file Dockerfile \
  --platform linux \
  --timeout 3600 \
  --only-show-errors \
  "$ROOT_DIR"

az webapp config container set \
  --resource-group "$DEPLOY_RESOURCE_GROUP" \
  --name "$DEPLOY_WEBAPP_NAME" \
  --container-image-name "$image_ref" \
  --container-registry-url "https://${acr_login_server}" \
  --enable-app-service-storage false \
  --only-show-errors >/dev/null

acr_managed_identity="$(
  az webapp config show \
    --resource-group "$DEPLOY_RESOURCE_GROUP" \
    --name "$DEPLOY_WEBAPP_NAME" \
    --query acrUseManagedIdentityCreds \
    --output tsv \
    --only-show-errors
)"
[[ "$acr_managed_identity" == "true" ]] || fail "Azure Web App is no longer configured to pull ACR images with managed identity."

az webapp restart \
  --resource-group "$DEPLOY_RESOURCE_GROUP" \
  --name "$DEPLOY_WEBAPP_NAME" \
  --only-show-errors >/dev/null

echo "Built container image and updated Azure Web App: $DEPLOY_WEBAPP_NAME"
echo "Container image: $image_ref"
echo "Build record: $ARTIFACT_DIR/last-image.txt"
