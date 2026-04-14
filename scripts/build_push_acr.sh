#!/usr/bin/env bash

set -euo pipefail

# ============================================================
# build_push_acr.sh
#
# 作用：
# 1) 登录 Azure 与 ACR
# 2) 在本地构建 Docker 镜像
# 3) 推送镜像到 ACR
#
# 用法示例：
#   bash scripts/build_push_acr.sh \
#     --acr-name myacr \
#     --image-repo commercialscripting \
#     --tag 0.1.0
#
# 可选参数：
#   --dockerfile <path>     默认 Dockerfile
#   --context <path>        默认当前仓库根目录
#   --platform <platform>   例如 linux/amd64（默认不指定）
#   --use-acr-build         使用 ACR 云端构建（无需本机 Docker）
# ============================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

ACR_NAME=""
IMAGE_REPO="commercialscripting"
IMAGE_TAG=""
DOCKERFILE_PATH="${REPO_ROOT}/Dockerfile"
BUILD_CONTEXT="${REPO_ROOT}"
PLATFORM=""
USE_ACR_BUILD=false

print_usage() {
	cat <<'EOF'
用法：
	bash scripts/build_push_acr.sh --acr-name <acrName> [选项]

必填参数：
	--acr-name <name>           Azure Container Registry 名称（不含 azurecr.io）

可选参数：
	--image-repo <repo>         镜像仓库名，默认 commercialscripting
	--tag <tag>                 镜像标签，默认自动生成（时间戳-短SHA）
	--dockerfile <path>         Dockerfile 路径，默认 ./Dockerfile
	--context <path>            docker build 上下文目录，默认仓库根目录
	--platform <platform>       例如 linux/amd64
	--use-acr-build             使用 ACR 云端构建（无需本机 Docker）
	-h, --help                  查看帮助

示例：
	bash scripts/build_push_acr.sh --acr-name myacr --image-repo commercialscripting --tag 0.1.0
EOF
}

log_info() {
	printf "\033[1;34m[INFO]\033[0m %s\n" "$*"
}

log_warn() {
	printf "\033[1;33m[WARN]\033[0m %s\n" "$*"
}

log_error() {
	printf "\033[1;31m[ERROR]\033[0m %s\n" "$*" >&2
}

require_command() {
	local cmd="$1"
	if ! command -v "$cmd" >/dev/null 2>&1; then
		log_error "未找到命令: ${cmd}"
		exit 1
	fi
}

while [[ $# -gt 0 ]]; do
	case "$1" in
		--acr-name)
			ACR_NAME="${2:-}"
			shift 2
			;;
		--image-repo)
			IMAGE_REPO="${2:-}"
			shift 2
			;;
		--tag)
			IMAGE_TAG="${2:-}"
			shift 2
			;;
		--dockerfile)
			DOCKERFILE_PATH="${2:-}"
			shift 2
			;;
		--context)
			BUILD_CONTEXT="${2:-}"
			shift 2
			;;
		--platform)
			PLATFORM="${2:-}"
			shift 2
			;;
		--use-acr-build)
			USE_ACR_BUILD=true
			shift 1
			;;
		-h|--help)
			print_usage
			exit 0
			;;
		*)
			log_error "未知参数: $1"
			print_usage
			exit 1
			;;
	esac
done

if [[ -z "${ACR_NAME}" ]]; then
	log_error "缺少必填参数 --acr-name"
	print_usage
	exit 1
fi

require_command az

if [[ "${USE_ACR_BUILD}" != "true" ]] && ! command -v docker >/dev/null 2>&1; then
	log_warn "未找到 docker，自动切换到 ACR 云端构建模式。"
	USE_ACR_BUILD=true
fi

if [[ ! -f "${DOCKERFILE_PATH}" ]]; then
	log_error "Dockerfile 不存在: ${DOCKERFILE_PATH}"
	exit 1
fi

if [[ ! -d "${BUILD_CONTEXT}" ]]; then
	log_error "构建上下文目录不存在: ${BUILD_CONTEXT}"
	exit 1
fi

if ! az account show >/dev/null 2>&1; then
	log_error "Azure CLI 未登录，请先执行: az login"
	exit 1
fi

if [[ -z "${IMAGE_TAG}" ]]; then
	# 默认标签：UTC 时间戳 + git 短 SHA（若当前目录不是 git 仓库则用 no-git）
	if git -C "${REPO_ROOT}" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
		GIT_SHA="$(git -C "${REPO_ROOT}" rev-parse --short HEAD)"
	else
		GIT_SHA="no-git"
	fi
	IMAGE_TAG="$(date -u +%Y%m%d%H%M%S)-${GIT_SHA}"
fi

log_info "查询 ACR 登录服务器地址..."
LOGIN_SERVER="$(az acr show --name "${ACR_NAME}" --query loginServer -o tsv)"

if [[ -z "${LOGIN_SERVER}" ]]; then
	log_error "无法获取 ACR 登录地址，请确认 ACR 名称正确: ${ACR_NAME}"
	exit 1
fi

FULL_IMAGE="${LOGIN_SERVER}/${IMAGE_REPO}:${IMAGE_TAG}"

log_info "登录 ACR: ${ACR_NAME}"
az acr login --name "${ACR_NAME}" >/dev/null

BUILD_ARGS=(build -f "${DOCKERFILE_PATH}" -t "${FULL_IMAGE}")
if [[ -n "${PLATFORM}" ]]; then
	BUILD_ARGS+=(--platform "${PLATFORM}")
fi
BUILD_ARGS+=("${BUILD_CONTEXT}")

if [[ "${USE_ACR_BUILD}" == "true" ]]; then
	log_info "使用 ACR 云端构建并推送镜像: ${FULL_IMAGE}"
	ACR_BUILD_ARGS=(acr build --registry "${ACR_NAME}" --image "${IMAGE_REPO}:${IMAGE_TAG}" --file "${DOCKERFILE_PATH}")
	if [[ -n "${PLATFORM}" ]]; then
		# ACR Tasks 支持通过 build-arg 传递给 Dockerfile，默认无需指定平台。
		log_warn "--platform 在 ACR 云端构建模式下将被忽略。"
	fi
	ACR_BUILD_ARGS+=("${BUILD_CONTEXT}")
	az "${ACR_BUILD_ARGS[@]}"
else
	log_info "开始构建镜像: ${FULL_IMAGE}"
	docker "${BUILD_ARGS[@]}"

	log_info "推送镜像到 ACR: ${FULL_IMAGE}"
	docker push "${FULL_IMAGE}"
fi

log_info "完成。镜像已推送：${FULL_IMAGE}"

cat <<EOF

下一步可执行：
1) 在 Azure Portal 的 Web App 容器配置中填写：
	 - Image: ${IMAGE_REPO}
	 - Tag:   ${IMAGE_TAG}

2) 或使用 Azure CLI 更新 Web App 容器：
	 az webapp config container set \
		 --name <webAppName> \
		 --resource-group <resourceGroup> \
		 --container-image-name ${FULL_IMAGE} \
		 --container-registry-url https://${LOGIN_SERVER}

3) 确认 Web App 配置中包含：
	 - WEBSITES_PORT=8000
EOF
