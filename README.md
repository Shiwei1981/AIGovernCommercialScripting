# AIGovenDemoCommercialScripting

## 项目简介 | Overview

CommercialScripting 子项目用于实现“受治理的脚本生成工作流”，提供前端页面、无状态 Python 后端、检索增强生成能力、历史查询和审计追踪能力，并输出可被下游治理项目消费的共享契约数据。  
The CommercialScripting child project implements a governed script-generation workflow, including a frontend app, stateless Python backend, retrieval-augmented generation, history search, and audit traceability, while producing shared contract data for downstream governance projects.

## 项目目标 | Goals

- 基于 Entra ID 的用户认证与访问控制  
    Entra ID based user authentication and access control
- 基于 Azure OpenAI 的生成能力（含文档验证与兼容性约束）  
    Azure OpenAI generation with documentation validation and compatibility constraints
- 基于 Azure AI Search 的新闻检索增强（仅 allowlist 来源，且满足 6 个月新鲜度）  
    Azure AI Search retrieval over allowlisted news sources with six-month freshness
- 基于 Azure SQL 的生成历史与审计证据持久化  
    Azure SQL persistence for generation history and audit evidence
- 支持按用户 ID、会话 ID、生成 ID 的查询与追溯  
    Query and traceability by user ID, session ID, and generation ID

## 技术栈 | Tech Stack

- 前端 Frontend: HTML5 + Vanilla JavaScript + MSAL Browser
- 后端 Backend: FastAPI (Python 3.12.x)
- 鉴权 Auth: Microsoft Entra ID (PKCE flow)
- 生成 Generation: Azure OpenAI (Direct SDK first)
- 检索 Retrieval: Azure AI Search
- 持久化 Persistence: Azure SQL
- 基础设施 Infrastructure: ARM JSON (with documented VM manual binding steps)

## 目录结构 | Project Structure

```text
AIGovernCommercialScripting/
├── backend/                    # FastAPI backend / 后端
│   ├── requirements/          # Python deps (base/dev) / 依赖
│   ├── src/                   # API, services, repositories, models, config
│   └── tests/                 # unit / integration / contract
├── frontend/                   # HTML5 frontend / 前端
│   ├── public/                # entry HTML / 入口页面
│   ├── src/                   # pages, auth, API client
│   └── tests/e2e/             # E2E tests (Python Playwright)
├── infra/arm/                  # ARM templates
├── sql/                        # SQL migrations and views
├── docs/                       # deployment/setup/validation docs
└── specs/001-governed-script-workflow/
                                                                # spec, plan, tasks, checklists, contracts
```

## 先决条件 | Prerequisites

- Linux 或 macOS（Windows 可用但命令需适配）  
    Linux or macOS (Windows is supported with command adjustments)
- Python 3.12.x
- Node.js 18+
- 可访问 Azure 资源：Entra、Azure OpenAI、Azure AI Search、Azure SQL  
    Accessible Azure resources: Entra, Azure OpenAI, Azure AI Search, Azure SQL

## 环境变量 | Environment Variables

建议先复制根目录示例文件并填充实际值。  
Copy the root environment template and fill in real values first.

```bash
cp .env.example .env
```

关键变量（完整列表见 docs/setup/environment-variables.md）：  
Key variables (full list in docs/setup/environment-variables.md):

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
- GOVERNANCE_SQL_SCHEMA
- TLS_CERT_PATH
- TLS_KEY_PATH
- AUDIT_CONTRACT_VERSION

注意事项 | Notes:

- 严禁将真实密钥或凭据提交到仓库  
    Never commit real secrets or credentials to the repository.
- 当前部署基线使用 API Key 环境变量注入（OpenAI/Search）  
    The current deployment baseline uses API key injection via environment variables (OpenAI/Search).
- 建议通过 App Service 设置或 Key Vault 引用管理密钥  
    Manage keys through App Service settings or Key Vault references.

## 快速开始 | Quick Start

### 1) 安装后端依赖 | Install Backend Dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r backend/requirements/dev.txt
```

### 2) 启动后端服务 | Run Backend Service

```bash
uvicorn src.main:app --app-dir backend --host 0.0.0.0 --port 8000 --reload
```

健康检查 | Health check:

- GET /healthz

### 3) 启动前端静态页面（开发） | Run Frontend Static Site (Dev)

前端当前为无打包静态页面，可使用 Python 启动静态服务。  
Frontend is currently a non-bundled static site; use Python to serve files.

```bash
python3 -m http.server 5173 --directory frontend
```

浏览器访问 | Open in browser:

- http://localhost:5173/public/index.html

## API 概览 | API Overview

后端默认前缀为 /api。  
Backend routes are prefixed with /api.

- POST /api/generations
- GET /api/generations
- GET /api/generations/{generation_id}
- GET /api/generations/{generation_id}/audit

## 测试与质量检查 | Testing and Quality

### 后端 | Backend

```bash
ruff check backend
pytest backend/tests -q
```

### 前端 E2E | Frontend E2E

当前 E2E 通过 Python Playwright 套件执行。  
E2E tests are currently executed with Python Playwright.

```bash
pytest frontend/tests/e2e -q
```

## CI

GitHub Actions 已配置基础后端流水线。  
GitHub Actions includes a baseline backend pipeline.

- Ruff static checks
- Pytest automated tests

工作流文件 | Workflow file: .github/workflows/ci.yml

## 数据与数据库边界 | Data and Database Boundaries

- 使用数据库：aigovernadvworksdb  
    Database: aigovernadvworksdb
- 不允许修改已有表  
    Existing tables must not be modified
- 仅在新 schema 中新增 append-only 对象（表/视图/辅助对象）  
    Only add append-only objects (tables/views/helpers) in new schemas

SQL 变更目录 | SQL change locations:

- sql/migrations/
- sql/views/

## 部署说明 | Deployment Notes

- 资源与部署基线以 ARM JSON 为主  
    ARM JSON is the deployment baseline
- VM 证书安装、DNS 绑定、部分 Entra 同意流程允许文档化手工步骤  
    VM certificate install, DNS binding, and some Entra consent steps are documented manual exceptions

参考文档 | References:

- docs/deployment/vm-manual-binding-steps.md
- docs/validation/azure-documentation-validation.md
- docs/setup/repository-bootstrap.md

## 契约与规范 | Contracts and Specs

共享契约与特性文档位于：  
Shared contracts and feature docs are located at:

- specs/001-governed-script-workflow/contracts/
- specs/001-governed-script-workflow/spec.md
- specs/001-governed-script-workflow/plan.md
- specs/001-governed-script-workflow/tasks.md

## 分支与协作建议 | Branching and Collaboration

- 当前特性分支：001-governed-script-workflow  
    Current feature branch: 001-governed-script-workflow
- 变更前先同步规格与任务  
    Sync spec and tasks before making code changes
- 提交前至少通过 Ruff + Pytest  
    Run Ruff and Pytest before commit

## 常见问题 | FAQ

### 1) CI 报 ruff 未找到 | CI reports "ruff: command not found"

本地先安装开发依赖：  
Install development dependencies locally first:

```bash
pip install -r backend/requirements/dev.txt
```

### 2) 本地认证回调失败 | Local auth callback fails

检查 ENTRA_REDIRECT_URI 与实际访问地址、端口和协议是否一致（建议 HTTPS 场景与 Entra 配置保持完全匹配）。  
Verify ENTRA_REDIRECT_URI matches the actual host, port, and protocol (for HTTPS setups, keep it exactly aligned with Entra app registration).

### 3) 检索结果缺少来源链接 | Retrieval results missing source URLs

检查 AI Search 索引字段映射、allowlist 数据和入库规范，确保 canonical URL 与发布时间字段完整。  
Check AI Search field mapping, allowlist data quality, and ingestion rules to ensure canonical URL and publication date are always populated.

---

如需扩展 README（例如补充架构图、时序图、生产部署手册），建议在 docs/ 下新增专题文档并在此处链接。  
For further expansion (architecture diagram, sequence diagram, production runbook), add dedicated docs under docs/ and link them here.