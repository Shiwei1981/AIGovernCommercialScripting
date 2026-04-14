#!/usr/bin/env bash

set -u

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
AUTO_INSTALL="${AUTO_INSTALL:-1}"
APT_UPDATED=0
CAN_USE_APT=0
SUDO_CMD=""

PASS_COUNT=0
WARN_COUNT=0
FAIL_COUNT=0

pass() {
  echo "[PASS] $1"
  PASS_COUNT=$((PASS_COUNT + 1))
}

warn() {
  echo "[WARN] $1"
  WARN_COUNT=$((WARN_COUNT + 1))
}

fail() {
  echo "[FAIL] $1"
  FAIL_COUNT=$((FAIL_COUNT + 1))
}

section() {
  echo
  echo "== $1 =="
}

command_exists() {
  command -v "$1" >/dev/null 2>&1
}

ensure_azure_cli_repo() {
  local list_file="/etc/apt/sources.list.d/azure-cli.list"
  local keyring_file="/etc/apt/keyrings/microsoft.gpg"
  local dist=""
  local arch=""
  local tmp_keyring=""

  if [[ "$CAN_USE_APT" -ne 1 ]]; then
    warn "Cannot prepare Azure CLI apt repo (no sudo/root privileges)"
    return 1
  fi

  if [[ ! -f /etc/os-release ]]; then
    fail "Cannot prepare Azure CLI apt repo: /etc/os-release not found"
    return 1
  fi

  # shellcheck source=/dev/null
  . /etc/os-release
  if [[ "${ID-}" != "ubuntu" ]]; then
    warn "Skip Azure CLI apt repo setup on non-Ubuntu OS"
    return 1
  fi

  if ! command_exists curl || ! command_exists gpg || ! command_exists lsb_release; then
    warn "Missing curl/gpg/lsb_release, cannot prepare Azure CLI apt repo automatically"
    return 1
  fi

  dist="$(lsb_release -cs)"
  arch="$(dpkg --print-architecture)"
  tmp_keyring="$(mktemp)"

  # Always rewrite with a known-good absolute path to avoid malformed source entries.
  if ! $SUDO_CMD rm -f "$list_file"; then
    fail "Failed to remove stale Azure CLI source file: $list_file"
    rm -f "$tmp_keyring"
    return 1
  fi

  if ! $SUDO_CMD mkdir -p /etc/apt/keyrings; then
    fail "Failed to create /etc/apt/keyrings"
    rm -f "$tmp_keyring"
    return 1
  fi

  if ! curl -sLS https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > "$tmp_keyring"; then
    fail "Failed to download/dearmor Microsoft apt signing key"
    rm -f "$tmp_keyring"
    return 1
  fi

  if ! $SUDO_CMD install -m 0644 "$tmp_keyring" "$keyring_file"; then
    fail "Failed to install Microsoft apt signing key: $keyring_file"
    rm -f "$tmp_keyring"
    return 1
  fi
  rm -f "$tmp_keyring"

  if ! printf 'deb [arch=%s signed-by=%s] https://packages.microsoft.com/repos/azure-cli/ %s main\n' "$arch" "$keyring_file" "$dist" | $SUDO_CMD tee "$list_file" >/dev/null; then
    fail "Failed to write Azure CLI apt source: $list_file"
    return 1
  fi

  pass "Azure CLI apt source configured: $list_file"
  APT_UPDATED=0
  return 0
}

setup_apt_context() {
  if [[ ! -f /etc/os-release ]]; then
    return
  fi

  # shellcheck source=/dev/null
  . /etc/os-release
  if [[ "${ID-}" != "ubuntu" ]]; then
    return
  fi

  if ! command_exists apt-get; then
    return
  fi

  if [[ "$(id -u)" -eq 0 ]]; then
    SUDO_CMD=""
    CAN_USE_APT=1
    return
  fi

  if command_exists sudo; then
    SUDO_CMD="sudo"
    CAN_USE_APT=1
  fi
}

apt_install_package() {
  local package_name="$1"

  if [[ "$AUTO_INSTALL" != "1" ]]; then
    warn "Auto-install disabled (AUTO_INSTALL=$AUTO_INSTALL), skipped package: $package_name"
    return 1
  fi

  if [[ "$CAN_USE_APT" -ne 1 ]]; then
    warn "Cannot auto-install $package_name (apt unavailable or no sudo/root privileges)"
    return 1
  fi

  if [[ "$package_name" == "azure-cli" ]]; then
    ensure_azure_cli_repo || warn "Proceeding without Azure CLI repo auto-setup"
  fi

  if [[ "$APT_UPDATED" -eq 0 ]]; then
    if $SUDO_CMD apt-get update -y >/dev/null 2>&1; then
      pass "apt-get update completed"
      APT_UPDATED=1
    else
      fail "apt-get update failed, cannot install missing packages"
      return 1
    fi
  fi

  if $SUDO_CMD apt-get install -y "$package_name" >/dev/null 2>&1; then
    pass "Installed package: $package_name"
    return 0
  fi

  fail "Failed to install package: $package_name"
  return 1
}

ensure_command() {
  local cmd="$1"
  local package_name="$2"

  if command_exists "$cmd"; then
    pass "Command found: $cmd"
    return
  fi

  warn "Command missing: $cmd"

  if [[ -n "$package_name" ]] && apt_install_package "$package_name"; then
    if command_exists "$cmd"; then
      pass "Command ready after install: $cmd"
      return
    fi
  fi

  fail "Command missing: $cmd"
}

ensure_optional_command() {
  local cmd="$1"
  local package_name="$2"

  if command_exists "$cmd"; then
    pass "Optional command found: $cmd"
    return
  fi

  warn "Optional command missing: $cmd"
  if [[ -n "$package_name" ]]; then
    if apt_install_package "$package_name" && command_exists "$cmd"; then
      pass "Optional command ready after install: $cmd"
      return
    fi
  fi

  warn "Optional command still missing: $cmd"
}

check_min_version() {
  local current="$1"
  local required="$2"
  local sorted
  sorted="$(printf '%s\n%s\n' "$required" "$current" | sort -V | head -n1)"
  [[ "$sorted" == "$required" ]]
}

check_file_exists() {
  local rel_path="$1"
  local abs_path="$ROOT_DIR/$rel_path"
  if [[ -f "$abs_path" ]]; then
    pass "File exists: $rel_path"
  else
    fail "Missing file: $rel_path"
  fi
}

check_dir_exists() {
  local rel_path="$1"
  local abs_path="$ROOT_DIR/$rel_path"
  if [[ -d "$abs_path" ]]; then
    pass "Directory exists: $rel_path"
  else
    fail "Missing directory: $rel_path"
  fi
}

check_env_required() {
  local var_name="$1"
  local value="${!var_name-}"
  if [[ -n "$value" ]]; then
    pass "Env set: $var_name"
  else
    fail "Env missing: $var_name"
  fi
}

check_url_env() {
  local var_name="$1"
  local value="${!var_name-}"
  if [[ -z "$value" ]]; then
    warn "Skip URL check because env is missing: $var_name"
    return
  fi

  if [[ "$value" =~ ^https?:// ]]; then
    pass "Env URL format ok: $var_name"
  else
    fail "Env URL invalid (must start with http:// or https://): $var_name"
  fi
}

check_path_env_file() {
  local var_name="$1"
  local value="${!var_name-}"
  if [[ -z "$value" ]]; then
    warn "Skip path check because env is missing: $var_name"
    return
  fi

  local abs_path
  if [[ "$value" = /* ]]; then
    abs_path="$value"
  else
    abs_path="$ROOT_DIR/$value"
  fi

  if [[ -f "$abs_path" && -r "$abs_path" ]]; then
    pass "Path from $var_name is readable: $value"
  else
    fail "Path from $var_name is not a readable file: $value"
  fi
}

section "Operating System"
if [[ -f /etc/os-release ]]; then
  # shellcheck source=/dev/null
  . /etc/os-release
  if [[ "${ID-}" == "ubuntu" ]]; then
    pass "OS is Ubuntu (${VERSION_ID-unknown})"
  else
    fail "OS is not Ubuntu (detected: ${ID-unknown})"
  fi
else
  fail "/etc/os-release not found"
fi

setup_apt_context

section "Required Commands"
ensure_command "git" "git"
ensure_command "python3" "python3"
ensure_command "node" "nodejs"
ensure_command "npm" "npm"
ensure_command "az" "azure-cli"
ensure_command "openssl" "openssl"
ensure_command "nginx" "nginx"

section "Optional Commands"
ensure_optional_command "jq" "jq"
ensure_optional_command "curl" "curl"
ensure_optional_command "sqlcmd" "mssql-tools18"

section "Version Checks"
if command_exists python3; then
  py_ver="$(python3 -V 2>&1 | awk '{print $2}')"
  if check_min_version "$py_ver" "3.12.3"; then
    pass "Python version ok: $py_ver (required >= 3.12.3)"
  else
    fail "Python version too low: $py_ver (required >= 3.12.3)"
  fi
fi

if command_exists node; then
  node_ver_raw="$(node -v 2>/dev/null)"
  node_ver="${node_ver_raw#v}"
  if check_min_version "$node_ver" "20.0.0"; then
    pass "Node.js version ok: $node_ver (required >= 20.0.0)"
  else
    fail "Node.js version too low: $node_ver (required >= 20.0.0)"
  fi
fi

if command_exists npm; then
  npm_ver="$(npm -v 2>/dev/null)"
  if check_min_version "$npm_ver" "10.0.0"; then
    pass "npm version ok: $npm_ver (required >= 10.0.0)"
  else
    fail "npm version too low: $npm_ver (required >= 10.0.0)"
  fi
fi

if command_exists nginx; then
  nginx_ver_raw="$(nginx -v 2>&1)"
  nginx_ver="$(echo "$nginx_ver_raw" | sed -n 's/.*nginx\/\([0-9.]*\).*/\1/p')"
  if [[ -z "$nginx_ver" ]]; then
    warn "Unable to parse nginx version: $nginx_ver_raw"
  elif check_min_version "$nginx_ver" "1.18.0"; then
    pass "Nginx version ok: $nginx_ver (required >= 1.18.0)"
  else
    fail "Nginx version too low: $nginx_ver (required >= 1.18.0)"
  fi
fi

section "Repository Layout"
check_dir_exists "backend"
check_dir_exists "frontend"
check_dir_exists "infra"
check_dir_exists "sql"
check_dir_exists "docs"

check_file_exists "backend/requirements/dev.txt"
check_file_exists "frontend/package.json"
check_file_exists "infra/arm/commercialscripting.main.json"
check_file_exists "infra/arm/commercialscripting.parameters.json"
check_file_exists "sql/migrations/001_create_governance_schema.sql"
check_file_exists "sql/migrations/002_create_governance_history_tables.sql"
check_file_exists "sql/views/001_governance_history_views.sql"
check_file_exists "docs/validation/allowlist.txt"
check_file_exists ".env.example"

section "Environment Variables"
for var in \
  ENTRA_TENANT_ID \
  ENTRA_CLIENT_ID \
  ENTRA_AUTHORITY \
  ENTRA_REDIRECT_URI \
  APP_BASE_URL \
  API_BASE_URL \
  AZURE_OPENAI_ENDPOINT \
  AZURE_OPENAI_DEPLOYMENT \
  AZURE_OPENAI_API_VERSION \
  AI_SEARCH_ENDPOINT \
  AI_SEARCH_INDEX_NAME \
  AI_SEARCH_ALLOWLIST_PATH \
  AZURE_SQL_CONNECTIONSTRING \
  GOVERNANCE_SQL_SCHEMA \
  TLS_CERT_PATH \
  TLS_KEY_PATH \
  AUDIT_CONTRACT_VERSION; do
  check_env_required "$var"
done

check_url_env "ENTRA_AUTHORITY"
check_url_env "ENTRA_REDIRECT_URI"
check_url_env "APP_BASE_URL"
check_url_env "API_BASE_URL"
check_url_env "AZURE_OPENAI_ENDPOINT"
check_url_env "AI_SEARCH_ENDPOINT"

check_path_env_file "AI_SEARCH_ALLOWLIST_PATH"
check_path_env_file "TLS_CERT_PATH"
check_path_env_file "TLS_KEY_PATH"

section "Azure CLI Session"
if command_exists az; then
  if az account show >/dev/null 2>&1; then
    subscription_name="$(az account show --query name -o tsv 2>/dev/null)"
    pass "Azure CLI logged in (subscription: ${subscription_name:-unknown})"
  else
    fail "Azure CLI not logged in. Run: az login"
  fi
fi

section "Summary"
echo "PASS: $PASS_COUNT"
echo "WARN: $WARN_COUNT"
echo "FAIL: $FAIL_COUNT"

if [[ $FAIL_COUNT -gt 0 ]]; then
  echo
  echo "Preflight check failed. Fix required items and rerun."
  exit 1
fi

echo
echo "Preflight check passed. Environment is ready for deployment steps."
exit 0
