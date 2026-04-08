# 私人投资 AI 助理

基于 AgentScope 多 Agent 系统的智能投资分析助手，支持多模型适配、持仓管理、深度股票分析和组合评估。

## 📋 技术栈

### 后端
- **框架**: FastAPI + Uvicorn
- **多 Agent 系统**: AgentScope（Supervisor + 5 专项 Agent + Fusion Agent）
- **数据验证**: Pydantic v2
- **金融数据**: Finnhub API
- **存储**: SQLite 数据库 + 本地 JSON 文件

### 前端
- **框架**: Next.js 14 + React
- **样式**: Tailwind CSS + shadcn/ui
- **图表**: Recharts
- **包管理**: npm

## 📁 项目结构

```
finAssist/
├── backend/                    # 后端服务
│   ├── main.py                 # FastAPI 应用入口
│   ├── config.py               # 全局配置
│   ├── agents/                 # Agent 系统
│   │   ├── base.py             # Agent 基类
│   │   ├── orchestrator.py     # Agent 编排器
│   │   ├── supervisor.py       # 总控 Agent
│   │   ├── news.py             # 新闻分析 Agent
│   │   ├── sec.py              # SEC 文件分析 Agent
│   │   ├── fundamentals.py     # 基本面分析 Agent
│   │   ├── technical.py        # 技术指标分析 Agent
│   │   └── fusion.py           # 融合 Agent
│   ├── routers/                # API 路由
│   │   ├── portfolio.py        # 持仓管理
│   │   ├── settings.py         # 设置管理
│   │   ├── analysis.py         # 分析任务
│   │   ├── agents.py           # Agent 交互
│   │   └── market.py           # 行情数据
│   ├── services/               # 业务服务
│   │   ├── finnhub.py          # Finnhub 数据服务
│   │   └── model_adapter.py    # 多模型适配层
│   ├── database.py            # 数据库连接和配置
│   ├── models.py              # SQLAlchemy 数据模型
│   └── scripts/               # 脚本文件
│       └── db/                # 数据库相关脚本
│           ├── init_db.py     # 数据库初始化脚本
│           ├── example_data.sql # 示例数据 SQL 文件
│           └── db_init_README.md # 数据库使用说明
│   └── storage/                # 数据存储
│       ├── settings.py         # 用户设置存储
│       └── portfolio.py        # 持仓数据存储
├── frontend/                   # 前端应用
│   ├── src/
│   │   ├── app/                # Next.js 页面路由
│   │   │   ├── page.tsx        # 仪表盘
│   │   │   ├── portfolio/      # 持仓管理页
│   │   │   ├── analysis/       # 股票分析页
│   │   │   ├── agents/         # Agent 聊天页
│   │   │   └── settings/       # 设置页
│   │   ├── components/         # UI 组件
│   │   └── lib/                # 工具库
│   │       └── api.ts          # API 客户端
│   └── next.config.mjs         # Next.js 配置
└── README.md
```

## 🚀 快速开始

### 前置要求

- Python 3.10+
- Node.js 18+
- npm 9+
- Finnhub API Key（[免费注册](https://finnhub.io/)）

### 1. 克隆项目

```bash
git clone <repository-url>
cd finAssist
```

### 2. 后端配置与启动

```bash
# 进入后端目录
cd backend

# 创建虚拟环境（推荐）
python -m venv venv
source venv/bin/activate  # macOS/Linux
# 或
venv\Scripts\activate     # Windows

# 安装依赖
pip install -r requirements.txt

# 配置环境变量（可选，也可在设置页面配置）
export FINNHUB_API_KEY="your_finnhub_api_key"

# 数据库初始化（可选，首次启动会自动执行）
# 该命令会创建数据库表结构并导入示例数据
python scripts/db/init_db.py

# 启动后端服务（默认端口 8001）
python main.py
```

后端服务将在 `http://localhost:8001` 启动，API 文档访问 `http://localhost:8001/docs`

### 3. 前端配置与启动

```bash
# 打开新终端，进入前端目录
cd frontend

# 安装依赖
npm install

# 启动开发服务器（默认端口 3000）
npm run dev
```

前端应用将在 `http://localhost:3000` 启动

## 🗄️ 数据库初始化

系统使用 SQLite 数据库存储数据，数据库会在首次启动时自动初始化。

### 数据库表结构

| 表名 | 说明 |
|------|------|
| `portfolio_holdings` | 用户持仓数据 |
| `analysis_reports` | 分析报告主表 |
| `agent_reports` | Agent 详细报告表 |
| `analysis_tasks` | 分析任务状态表 |
| `finnhub_cache` | Finnhub API 数据缓存 |

### 数据库初始化脚本

在 `backend/scripts/db/` 目录下提供了 `init_db.py` 脚本，用于手动管理数据库：

```bash
cd backend
source venv/bin/activate

# 完整初始化（创建表 + 导入示例数据）
python scripts/db/init_db.py

# 重置数据库（删除所有数据并重新初始化）
python scripts/db/init_db.py reset

# 仅导入示例持仓数据
python scripts/db/init_db.py sample
```

### 示例数据

初始化后会自动导入以下示例数据：
- **6条持仓数据**：AAPL、NVDA、TSLA、INTC、MSFT、AMZN
- **3条分析报告**：包含完整的 Agent 分析内容
- **9条 Agent 报告**：每个分析报告包含新闻、财务、技术等维度
- **1条待处理任务**：演示任务队列功能

### 数据库操作详细说明

更多数据库操作说明请查看 `backend/scripts/db/db_init_README.md`

## ⚙️ 配置说明

### 模型配置

支持以下模型提供商，可在设置页面或后端配置：

| 提供商 | 配置项 | 说明 |
|--------|--------|------|
| OpenRouter | `provider: openrouter` | 多模型聚合平台，支持多种模型 |
| OpenAI | `provider: openai` | OpenAI 官方 API |
| Grok | `provider: grok` | xAI Grok 模型 |
| Gemini | `provider: gemini` | Google Gemini 模型 |
| 百炼 | `provider: dashscope` | 阿里云百炼平台 |

配置示例（通过 API 或设置页面）：

```json
{
  "provider": "openrouter",
  "api_key": "your_api_key",
  "model": "anthropic/claude-3.5-sonnet",
  "base_url": "https://openrouter.ai/api/v1"
}
```

### Finnhub API 配置

1. 访问 [Finnhub](https://finnhub.io/) 注册免费账号
2. 获取 API Key
3. 通过以下方式配置：
   - 环境变量：`export FINNHUB_API_KEY="your_key"`
   - 设置页面：访问 `/settings` 页面配置

### 投资风格配置

系统支持以下投资风格，影响 Agent 分析侧重点：

- **保守型**：注重风险控制，偏好稳定收益
- **稳健型**：平衡风险与收益
- **平衡型**：风险与收益均衡（默认）
- **积极型**：追求较高收益，接受一定风险
- **激进型**：追求最大收益，高风险高回报

## 🤖 Agent 系统

系统包含 7 个 Agent，协同完成投资分析：

| Agent | 职责 |
|-------|------|
| **Supervisor** | 总控调度，拆解任务，分配给专项 Agent |
| **News Agent** | 分析最新新闻和市场情绪 |
| **SEC Agent** | 分析 SEC 文件（10-K、10-Q 等） |
| **Fundamentals Agent** | 基本面分析（财务指标、估值等） |
| **Technical Agent** | 技术指标分析（MA、RSI、MACD 等） |
| **Custom Skill Agent** | 执行用户自定义分析技能 |
| **Fusion Agent** | 融合各 Agent 结论，输出平衡型投资建议 |

## 📡 API 文档

启动后端后访问 `http://localhost:8001/docs` 查看完整的 Swagger API 文档。

### 主要接口

| 路径 | 方法 | 说明 |
|------|------|------|
| `/api/portfolio` | GET | 获取持仓列表 |
| `/api/portfolio` | POST | 添加持仓 |
| `/api/portfolio/{ticker}` | PUT | 更新持仓 |
| `/api/portfolio/{ticker}` | DELETE | 删除持仓 |
| `/api/analysis/ticker` | POST | 触发单股票分析 |
| `/api/analysis/portfolio` | POST | 触发组合分析 |
| `/api/agents/{name}/chat` | POST | 与 Agent 对话 |
| `/api/settings` | GET | 获取用户设置 |
| `/api/settings/model-config` | PUT | 更新模型配置 |
| `/api/market/quote/{ticker}` | GET | 获取股票报价 |

## 🔄 服务重启方法

在开发过程中，修改代码后需要重启服务才能看到更新。

### 后端服务重启
1. 停止正在运行的后端服务
   ```bash
   pkill -f "uvicorn" 2>/dev/null || true
   rm -f backend/uvicorn.pid
   ```

2. 启动后端服务（使用虚拟环境）
   ```bash
   cd backend
   source venv/bin/activate
   python3 main.py
   ```

3. 验证后端服务是否正常运行
   - 访问 http://localhost:8001
   - 检查是否有 "Uvicorn running on" 信息

### 前端服务重启
1. 停止正在运行的前端服务
   ```bash
   pkill -f "next" 2>/dev/null || true
   rm -f frontend/next.pid
   ```

2. 启动前端服务
   ```bash
   cd frontend
   npm run dev
   ```

3. 验证前端服务是否正常运行
   - 访问 http://localhost:3000
   - 检查是否有 "Ready in" 信息

## 📝 注意事项

1. **端口冲突**：后端默认使用 8001 端口，如被占用请修改 `backend/main.py` 中的 `port` 参数
2. **API Key 安全**：请勿将 API Key 提交到代码仓库
3. **Finnhub 限制**：免费版 API 有调用频率限制（60 次/分钟）
4. **数据存储**：所有数据存储在 SQLite 数据库中，路径为 `backend/data/finance_assistant.db`

## 🛠️ 开发指南

### 添加新的 Agent

1. 在 `backend/agents/` 下创建新的 Agent 文件
2. 继承 `BaseAgent` 类并实现 `analyze()` 方法
3. 在 `orchestrator.py` 中注册新 Agent
4. 在前端 `agents/page.tsx` 中添加对应选项

### 添加新的 API 路由

1. 在 `backend/routers/` 下创建新的路由文件
2. 在 `backend/main.py` 中注册路由
3. 更新前端 API 客户端 `frontend/src/lib/api.ts`

## 📄 License

MIT
