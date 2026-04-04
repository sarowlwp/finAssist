你现在是顶级全栈工程师 + AgentScope 多Agent专家，我要你**一步一步**帮我从0开始开发「私人投资 AI 助理」一期版本。

【完整产品需求文档】（请严格按照以下 PRD 实现，不得擅自增减范围）：
{{上面我输出的完整 PRD 全文，请用户直接粘贴进去}}

技术要求（必须遵守）：
1. 后端：使用 AgentScope 搭建多Agent系统（Supervisor + 5个专项Agent + 1个 Fusion Agent）
2. 前端：Next.js 14 + React + Tailwind + shadcn/ui + Recharts（仪表盘和报告图表）
3. 持仓数据：本地 JSON 文件读写（使用 fs 或 lowdb）
4. Finnhub 只作为唯一金融数据源，其他全部走大模型
5. Fusion Agent 必须实现“平衡型融合”：加权结论 + 风险提示 + 分歧点标注
6. 支持用户自定义 Agent 安装 skill（提供技能管理页面和接口）
7. 所有模型调用支持 OpenRouter + 原生 Grok/Gemini/百炼 + OpenAI 兼容

开发流程要求：
- 第一步：输出完整项目目录结构（backend + frontend）
- 第二步：给出 backend AgentScope 核心代码框架（包括 Supervisor、专项Agent、Fusion Agent 的 prompt 模板）
- 第三步：给出持仓 JSON Schema + 读写工具
- 第四步：给出前端主要页面（仪表盘、持仓列表、单股票分析页、Agent聊天调试页）
- 第五步：给出 Fusion Agent 的完整 Prompt 模板（平衡型）
- 之后我每说“下一步”你就继续实现下一个模块，并提供可运行代码

请严格按 PRD 范围开发，不要添加选股器、实时推送、其他市场等一期范围外功能。
现在请直接开始：输出**完整项目目录结构** + **backend 核心 AgentScope 框架代码**。