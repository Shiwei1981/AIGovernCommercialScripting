# AIGovenDemoCommercialScripting 部署手册（POC：单 Docker 前后端一体化）

## 1. 目标与范围

本手册用于将本项目以单容器方式部署到 Azure Web App（Linux），并使用平台默认域名与平台证书进行 HTTPS 访问。

本手册覆盖组件：

- 前端：HTML5 + MSAL.js（构建后静态资源）
- 后端：FastAPI（Python 3.12）
- 身份：Microsoft Entra ID（Authorization Code + PKCE）
- 生成：Azure OpenAI
- 检索：Azure AI Search（allowlist + 六个月新鲜度）
- 持久化：Azure SQL（仅新增对象，不修改现有表）
- 部署：Docker + Azure Web App for Containers

适用场景：个人/团队 POC，优先“快速上线可演示”。

---

## 2. 架构说明（POC 推荐）

### 2.1 运行架构

1. 浏览器访问 Web App 默认域名：https://<your-app>.azurewebsites.net
2. Azure 平台在 443 终止 TLS，并将请求转发到容器内部 HTTP 端口
3. Web App 运行单个 Docker 容器：
   - FastAPI 提供 /api 接口
   - FastAPI 同时托管前端静态资源（/）
4. 前端通过 window.__env（运行时注入）读取 Entra 和 API 配置
5. 后端调用 Azure OpenAI、Azure AI Search、Azure SQL

### 2.2 为什么采用单容器

- POC 交付快，部署与回滚路径简单
- 不需要单独维护 Nginx/VM/systemd
- 可保留后续拆分能力（前后端解耦）

---

## 3. 先决条件

### 3.1 本地工具

- Docker 24+
- Azure CLI（az）
- Git
- SQL 客户端（sqlcmd 或 Azure Data Studio）

### 3.2 Azure 资源权限

- 资源组创建/修改权限
- Web App 与 App Service Plan 创建权限
- ACR（如使用）创建与推送权限
- Entra 应用注册配置权限
- Azure SQL 对象创建权限（新增 schema/table/view）

### 3.3 代码准备

- 使用当前仓库主分支或目标发布分支
- 确认以下文件存在：
  - Dockerfile
  - scripts/start_container.sh
  - backend/src/main.py
  - frontend/index.html
  - frontend/public/env-config.js

---

## 4. 环境变量设计（运行时注入）

不要把密钥写进 Docker 镜像。请通过 Azure Web App -> Configuration -> Application settings 注入。

### 4.1 必需变量

- ENTRA_TENANT_ID
- ENTRA_CLIENT_ID
- ENTRA_AUTHORITY
- ENTRA_REDIRECT_URI
- APP_BASE_URL
- API_BASE_URL
- AZURE_OPENAI_ENDPOINT
- AZURE_OPENAI_DEPLOYMENT
- AZURE_OPENAI_API_VERSION
- AZURE_OPENAI_API_KEY
- AI_SEARCH_ENDPOINT
- AI_SEARCH_INDEX_NAME
- AI_SEARCH_ALLOWLIST_PATH
- AI_SEARCH_API_KEY
- AZURE_SQL_CONNECTIONSTRING
- GOVERNANCE_SQL_SCHEMA（默认 governance_history）
- AUDIT_CONTRACT_VERSION（默认 0.1.0）

说明：

- 容器启动脚本会在运行时生成 /app/frontend_dist/env-config.js
- 前端读取 ENTRA_CLIENT_ID / ENTRA_AUTHORITY / ENTRA_REDIRECT_URI / API_BASE_URL
- 容器监听端口优先级：WEBSITES_PORT > PORT > 8000
- 对外 HTTPS 端口固定由 Azure 平台提供（443），容器内部不直接监听 443

### 4.2 POC 推荐值示例

- APP_BASE_URL=https://<your-app>.azurewebsites.net
- API_BASE_URL=/api
- ENTRA_REDIRECT_URI=https://<your-app>.azurewebsites.net/auth/callback

---

## 5. Entra ID 配置

### 5.1 注册应用

1. 在 Entra 中创建应用（SPA）
2. Redirect URI 添加：
   - https://<your-app>.azurewebsites.net/auth/callback
3. 开启 Authorization Code + PKCE（SPA 默认）

### 5.2 API 权限与 Scope

1. 配置 access_as_user（若后端按 scope 校验）
2. 完成管理员同意（视租户策略）

### 5.3 与应用配置映射

- ENTRA_TENANT_ID <- Directory (tenant) ID
- ENTRA_CLIENT_ID <- Application (client) ID
- ENTRA_AUTHORITY <- https://login.microsoftonline.com/<tenant-id>
- ENTRA_REDIRECT_URI <- 上文 callback

---

## 6. Azure SQL 初始化（仅新增对象）

执行顺序：

1. sql/migrations/001_create_governance_schema.sql
2. sql/migrations/002_create_governance_history_tables.sql
3. sql/views/001_governance_history_views.sql

示例：

```bash
sqlcmd -S <server>.database.windows.net -d aigovernadvworksdb -G -i sql/migrations/001_create_governance_schema.sql
sqlcmd -S <server>.database.windows.net -d aigovernadvworksdb -G -i sql/migrations/002_create_governance_history_tables.sql
sqlcmd -S <server>.database.windows.net -d aigovernadvworksdb -G -i sql/views/001_governance_history_views.sql
```

验收点：

- governance_history schema 存在
- generation_record/source_reference/audit_record 三张表存在
- 查询视图可访问

---

## 7. Azure AI Search 与 OpenAI 准备

### 7.1 AI Search

- 索引含 canonical URL 与 published_at_utc 字段
- 数据源在 allowlist 中
- 检索逻辑限制近六个月
- 在 Azure Portal -> Search 服务 -> Keys 获取 AI_SEARCH_API_KEY

### 7.2 OpenAI

- 准备 endpoint / deployment / api version
- 在 Azure Portal -> Azure OpenAI -> Keys and Endpoint 获取 AZURE_OPENAI_API_KEY
- 确保 Web App 可访问对应 Azure OpenAI 资源

---

## 8. 镜像构建与推送

可选两种方式：

- 方式 A：本地构建并推送 ACR（推荐）
- 方式 B：Web App 从 GitHub Actions 构建（后续扩展）

以下以 ACR 为例。

### 8.1 创建 ACR（如未创建）

```bash
az acr create \
  --resource-group <rg> \
  --name <acrName> \
  --sku Basic
```

### 8.2 登录 ACR

```bash
az acr login --name <acrName>
```

### 8.3 构建并推送镜像

```bash
# 在仓库根目录
IMAGE=<acrName>.azurecr.io/commercialscripting:0.1.0

docker build -t "$IMAGE" .
docker push "$IMAGE"
```

---

## 9. 创建 Azure Web App（Linux 容器）

### 9.1 创建 Plan 与 Web App

```bash
az appservice plan create \
  --name <planName> \
  --resource-group <rg> \
  --is-linux \
  --sku B1

az webapp create \
  --name <webAppName> \
  --resource-group <rg> \
  --plan <planName> \
  --deployment-container-image-name <acrName>.azurecr.io/commercialscripting:0.1.0
```

### 9.2 配置容器镜像来源（ACR）

```bash
az webapp config container set \
  --name <webAppName> \
  --resource-group <rg> \
  --container-image-name <acrName>.azurecr.io/commercialscripting:0.1.0 \
  --container-registry-url https://<acrName>.azurecr.io
```

如使用 ACR 管理身份拉取，请额外配置 Web App 的托管身份与 AcrPull 角色。

### 9.3 设置应用配置（环境变量）

```bash
az webapp config appsettings set \
  --name <webAppName> \
  --resource-group <rg> \
  --settings \
    WEBSITES_PORT=8000 \
    APP_BASE_URL=https://<webAppName>.azurewebsites.net \
    API_BASE_URL=/api \
    ENTRA_TENANT_ID=<tenant-id> \
    ENTRA_CLIENT_ID=<client-id> \
    ENTRA_AUTHORITY=https://login.microsoftonline.com/<tenant-id> \
    ENTRA_REDIRECT_URI=https://<webAppName>.azurewebsites.net/auth/callback \
    AZURE_OPENAI_ENDPOINT=<openai-endpoint> \
    AZURE_OPENAI_DEPLOYMENT=<openai-deployment> \
    AZURE_OPENAI_API_VERSION=<api-version> \
    AZURE_OPENAI_API_KEY='<openai-api-key>' \
    AI_SEARCH_ENDPOINT=<search-endpoint> \
    AI_SEARCH_INDEX_NAME=<index-name> \
    AI_SEARCH_ALLOWLIST_PATH=/app/docs/validation/allowlist.txt \
    AI_SEARCH_API_KEY='<ai-search-api-key>' \
    AZURE_SQL_CONNECTIONSTRING='<sql-connection-string>' \
    GOVERNANCE_SQL_SCHEMA=governance_history
```

说明：Web App 会重启容器以应用新变量。

---

## 10. 首次发布后的验证

### 10.1 基础可用性

- 打开 https://<webAppName>.azurewebsites.net
- 访问 https://<webAppName>.azurewebsites.net/healthz 返回 {"status":"ok"}

### 10.2 登录验证

- 点击 Sign in
- 完成 Entra 登录并返回页面
- 浏览器无证书告警（平台默认证书）

### 10.3 业务验证

- POST /api/generations 可返回生成结果
- GET /api/generations 可按 user/session/generation 查询
- GET /api/generations/{id}/audit 返回审计链路

### 10.4 数据验证

- SQL 中新增对象可查询
- 审计与生成记录一致且可追溯

---

## 11. 日志、诊断与排障

### 11.1 查看容器日志

```bash
az webapp log config \
  --name <webAppName> \
  --resource-group <rg> \
  --docker-container-logging filesystem

az webapp log tail \
  --name <webAppName> \
  --resource-group <rg>
```

### 11.2 常见问题

1. 登录循环/回调失败：
   - 检查 ENTRA_REDIRECT_URI 与 Entra 注册值一致
   - 确认域名使用 azurewebsites 默认域名

2. 前端可打开但 API 报 401/403：
   - 检查 token audience/scope 与后端校验规则
   - 检查 ENTRA_AUTHORITY / TENANT_ID 是否一致

3. API 500：
  - 检查 OpenAI/Search/SQL 变量（尤其 AZURE_OPENAI_API_KEY、AI_SEARCH_API_KEY）
   - 检查 SQL 连接串是否可连通

4. 前端配置没生效：
   - 检查 /env-config.js 是否返回最新内容
   - 变更 App Settings 后确认容器已重启

---

## 12. 回滚策略（POC）

推荐基于镜像版本回滚：

1. 保留历史镜像 tag（如 0.1.0、0.1.1）
2. Web App 指回旧 tag
3. 重启并验证 healthz 与核心流程

示例：

```bash
az webapp config container set \
  --name <webAppName> \
  --resource-group <rg> \
  --container-image-name <acrName>.azurecr.io/commercialscripting:0.1.0
```

---

## 13. 安全与合规建议（POC 到生产过渡）

当前 POC 建议：

- 使用平台默认域名与证书
- 敏感配置放 App Settings，不入库
- 仅开放最小权限

后续生产化建议：

- 将密钥迁移到 Key Vault
- 使用托管身份访问 ACR、OpenAI、Search、SQL
- 启用 Application Insights 与告警
- 前后端逐步拆分部署，独立扩缩容

---

## 14. 关键文件索引

- Dockerfile
- scripts/start_container.sh
- backend/src/main.py
- backend/src/config/settings.py
- frontend/index.html
- frontend/public/env-config.js
- docs/setup/environment-variables.md
- sql/migrations/001_create_governance_schema.sql
- sql/migrations/002_create_governance_history_tables.sql
- sql/views/001_governance_history_views.sql

