#!/usr/bin/env bash
# One-click production deployment for the existing Azure Web App.
# The script only validates/configures/deploys existing resources and will stop on any missing input.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"
# shellcheck disable=SC1091
source "$ROOT_DIR/scripts/deploy/azure/common.sh"

# Step 1: Load .env.local and fail fast on missing or placeholder-like values.
echo "[STEP 1/7] Loading .env.local and validating production settings"
load_env_file
validate_runtime_env
validate_deploy_env
assert_prod_safe_flags

# Step 2: Prepare the local Python runtime used for DB/OpenAI/RSS validation before deployment.
echo "[STEP 2/7] Preparing local Python runtime"
ensure_python_runtime

# Step 3: Confirm the target Azure resources already exist and match the configured production URL.
echo "[STEP 3/7] Validating existing Azure resources"
bash "$ROOT_DIR/scripts/deploy/azure/validate_resources.sh"

# Step 4: Verify the database objects used by the application and align AIGenerationLog if needed.
echo "[STEP 4/7] Validating database schema and aligning AIGenerationLog"
bash "$ROOT_DIR/scripts/deploy/azure/verify_db_schema.sh"

# Step 5: Push the runtime app settings and startup command into the existing Azure Web App.
echo "[STEP 5/7] Applying production app settings"
bash "$ROOT_DIR/scripts/deploy/azure/configure_app_settings.sh"

# Step 6: Build the current source tree into a container image, push to ACR, and switch the Web App.
echo "[STEP 6/7] Building and deploying container image"
bash "$ROOT_DIR/scripts/deploy/azure/deploy_webapp_package.sh"

# Step 7: Validate that the deployed production site is reachable and enforcing auth boundaries.
echo "[STEP 7/7] Running production smoke test"
bash "$ROOT_DIR/scripts/deploy/azure/smoke_test_webapp.sh"

echo "Production deployment completed successfully."
echo "Production URL: $DEPLOY_APP_BASE_URL"
