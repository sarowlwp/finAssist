# Per-Agent Model Configuration UI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为每个 Agent 添加单独的模型配置界面，让用户可以为每个 Agent 配置不同的模型提供商和模型名称

**Architecture:** 在现有的设置页面基础上，添加一个新的 Agent 模型配置部分，为每个 Agent 显示配置卡片，包含提供商和模型选择器。使用与通用配置相同的 UI 组件和验证逻辑。

**Tech Stack:** Next.js 14, React, TypeScript, Tailwind CSS, Shadcn UI, FastAPI

---

## File Structure Changes

### Files to Modify:
1. `frontend/src/app/settings/page.tsx` - 添加 Agent 模型配置界面
2. `frontend/src/components/ui/select.tsx` - 可能需要修改或增强（如果需要）
3. `backend/routers/analysis.py` - 为旧版投资组合分析接口添加 per-agent 配置支持

---

## Bite-Sized Tasks

### Task 1: 查看并理解现有设置页面

**Files:**
- Read: `frontend/src/app/settings/page.tsx`
- Read: `frontend/src/lib/api.ts`
- Read: `backend/routers/analysis.py`

- [ ] **Step 1: 查看现有设置页面**

```bash
cat frontend/src/app/settings/page.tsx
```

- [ ] **Step 2: 查看 API 方法**

```bash
cat frontend/src/lib/api.ts | grep -A 20 "agent"
```

---

### Task 2: 实现 Agent 模型配置 UI

**Files:**
- Modify: `frontend/src/app/settings/page.tsx`

- [ ] **Step 1: 添加 Agent 模型配置界面**

在 `SettingsPage` 组件中添加以下代码：

```typescript
// Agent 模型配置数据类型
interface AgentModelConfig {
  provider: string;
  model: string;
}

interface AgentConfigState {
  [agentName: string]: AgentModelConfig;
}

// 在 component 中添加状态
const [agentModelConfigs, setAgentModelConfigs] = useState<AgentConfigState>({});
const [editingAgent, setEditingAgent] = useState<string | null>(null);
const [agentConfigForm, setAgentConfigForm] = useState<AgentModelConfig>({
  provider: 'openrouter',
  model: 'anthropic/claude-3.5-sonnet'
});

// 在 useEffect 中获取 Agent 配置
useEffect(() => {
  const fetchAgentConfigs = async () => {
    const agents = ['supervisor', 'fusion', 'news', 'sec', 'fundamentals', 'technical', 'custom_skill'];
    const configs: AgentConfigState = {};
    
    for (const agent of agents) {
      try {
        const config = await settingsApi.getAgentModelConfig(agent);
        configs[agent] = config;
      } catch (error) {
        console.error(`获取 ${agent} 配置失败:`, error);
      }
    }
    
    setAgentModelConfigs(configs);
  };

  fetchAgentConfigs();
}, []);

// 编辑 Agent 配置
const handleEditAgentConfig = (agentName: string) => {
  setEditingAgent(agentName);
  const config = agentModelConfigs[agentName] || {
    provider: 'openrouter',
    model: 'anthropic/claude-3.5-sonnet'
  };
  setAgentConfigForm(config);
};

// 保存 Agent 配置
const handleSaveAgentConfig = async () => {
  if (editingAgent) {
    try {
      const updatedSettings = await settingsApi.updateAgentModelConfig(editingAgent, agentConfigForm);
      setAgentModelConfigs(prev => ({
        ...prev,
        [editingAgent]: agentConfigForm
      }));
      setEditingAgent(null);
    } catch (error) {
      console.error(`保存 ${editingAgent} 配置失败:`, error);
    }
  }
};
```

- [ ] **Step 2: 添加 Agent 配置 UI 渲染**

在 `return` 语句中添加以下 JSX：

```typescript
{/* Agent 模型配置 */}
<div className="space-y-6">
  <div className="flex items-center justify-between">
    <div>
      <h3 className="text-lg font-semibold">Agent 模型配置</h3>
      <p className="text-sm text-gray-500 dark:text-gray-400">
        为每个 Agent 单独配置模型提供商和模型
      </p>
    </div>
  </div>

  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
    {['supervisor', 'fusion', 'news', 'sec', 'fundamentals', 'technical', 'custom_skill'].map(agent => (
      <div
        key={agent}
        className="p-4 rounded-lg border bg-card text-card-foreground shadow-sm"
      >
        <div className="flex items-center justify-between mb-3">
          <h4 className="font-medium capitalize">{agent} Agent</h4>
          <Button
            size="sm"
            variant={editingAgent === agent ? "default" : "outline"}
            onClick={() => handleEditAgentConfig(agent)}
          >
            {editingAgent === agent ? '保存' : '编辑'}
          </Button>
        </div>

        {editingAgent === agent ? (
          <div className="space-y-3">
            <Select
              value={agentConfigForm.provider}
              onValueChange={(value) =>
                setAgentConfigForm(prev => ({ ...prev, provider: value }))
              }
            >
              <SelectTrigger className="w-full text-sm">
                <SelectValue placeholder="选择提供商" />
              </SelectTrigger>
              <SelectContent>
                {getSupportedProviders().map(provider => (
                  <SelectItem key={provider} value={provider}>
                    {provider}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            <Input
              type="text"
              value={agentConfigForm.model}
              onChange={(e) =>
                setAgentConfigForm(prev => ({ ...prev, model: e.target.value }))
              }
              placeholder="模型名称"
              className="text-sm"
            />

            <div className="flex gap-2 pt-2">
              <Button
                size="sm"
                onClick={handleSaveAgentConfig}
                className="flex-1"
              >
                保存
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={() => setEditingAgent(null)}
              >
                取消
              </Button>
            </div>
          </div>
        ) : (
          <div className="space-y-1 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-500 dark:text-gray-400">提供商:</span>
              <span className="font-medium">
                {agentModelConfigs[agent]?.provider || '默认'}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500 dark:text-gray-400">模型:</span>
              <span className="font-medium">
                {agentModelConfigs[agent]?.model || '默认'}
              </span>
            </div>
          </div>
        )}
      </div>
    ))}
  </div>
</div>
```

---

### Task 3: 修复投资组合分析接口缺少 per-agent 配置的问题

**Files:**
- Modify: `backend/routers/analysis.py`

- [ ] **Step 1: 修改 run_portfolio_analysis 函数**

在 `run_portfolio_analysis` 函数中添加 `agent_model_configs` 参数：

```python
async def run_portfolio_analysis(
    task_id: str,
    tickers: List[str],
    user_settings: UserSettings,
    model_config: dict,
    agent_model_configs: dict,
    db: Session
) -> Dict:
    """
    投资组合分析任务
    """
    logger.info(f"开始投资组合分析任务: {task_id}, tickers: {tickers}")
    logger.debug(f"模型配置: {model_config}, Agent 模型配置: {agent_model_configs}")

    try:
        # 使用 orchestrator
        orchestrator = get_orchestrator(model_config, agent_model_configs)
        
        # 执行分析
        result = orchestrator.run_portfolio_analysis(
            tickers,
            user_settings=user_settings
        )
        
        logger.info(f"投资组合分析任务 {task_id} 完成")
        
        return result
        
    except Exception as e:
        logger.error(f"投资组合分析任务 {task_id} 失败: {e}")
        raise e
```

- [ ] **Step 2: 修改调用处传递参数**

在 `start_portfolio_analysis` 函数中修改调用：

```python
@router.post("/analysis/portfolio/start", response_model=AnalysisTaskResponse)
async def start_portfolio_analysis(
    request: PortfolioAnalysisRequest,
    task_service: AnalysisTaskService = Depends(get_analysis_task_service),
    settings_store: SettingsStore = Depends(get_settings_store),
    db: Session = Depends(get_db)
):
    """
    启动投资组合分析任务（异步）
    """
    user_settings = settings_store.load()
    llm_cfg = user_settings.llm_config
    agent_model_configs = user_settings.agent_model_configs or {}
    
    # 在这里使用获取到的配置
    logger.info(f"启动投资组合分析任务")
    
    # 创建任务
    task = task_service.create_task(
        tickers=request.tickers,
        analysis_type="portfolio",
        user_settings=user_settings
    )
    
    logger.debug(f"任务创建成功: {task}")
    
    # 启动后台任务
    background_tasks.add_task(
        run_portfolio_analysis,
        task.task_id,
        request.tickers,
        user_settings,
        llm_cfg,              # 通用配置
        agent_model_configs,   # Agent 级配置
        db
    )
    
    return AnalysisTaskResponse(
        task_id=task.task_id,
        status="pending"
    )
```

---

### Task 4: 运行前端构建检查

**Files:**
- Test: `frontend`

- [ ] **Step 1: 安装依赖**

```bash
cd frontend && npm install
```

- [ ] **Step 2: 运行类型检查**

```bash
npm run type-check
```

- [ ] **Step 3: 构建项目**

```bash
npm run build
```

- [ ] **Step 4: 运行开发服务器**

```bash
npm run dev
```

---

### Task 5: 测试功能

**Files:**
- Test: `frontend/src/app/settings/page.tsx`
- Test: `backend/routers/analysis.py`

- [ ] **Step 1: 访问设置页面**

```bash
open http://localhost:3000/settings
```

- [ ] **Step 2: 验证 Agent 配置 UI 功能**
  - 检查是否显示所有 7 个 Agent 的配置卡片
  - 测试编辑功能
  - 测试保存功能
  - 验证默认值显示

- [ ] **Step 3: 验证分析功能**
  - 访问 http://localhost:3000/analysis
  - 测试股票分析功能
  - 检查是否使用了 Agent 级配置

---

### Task 6: 提交代码

**Files:**
- Commit: All modified files

- [ ] **Step 1: 添加变更**

```bash
git add frontend/src/app/settings/page.tsx backend/routers/analysis.py
```

- [ ] **Step 2: 提交**

```bash
git commit -m "feat: 添加 Agent 模型配置 UI 和修复投资组合分析接口"
```

- [ ] **Step 3: 推送到远程**

```bash
git push
```

---

## Self-Review

**Spec Coverage:**
- ✅ 前端 Agent 配置 UI 实现
- ✅ Agent 配置获取和更新 API 调用
- ✅ 后端投资组合分析接口修复
- ✅ 验证步骤和提交指南

**Type Consistency:**
- ✅ 使用了正确的数据类型
- ✅ 状态管理和表单处理一致

**Placeholder Check:**
- ✅ 所有代码示例完整
- ✅ 没有 TODO 或 TBD 标记
- ✅ 包含完整的验证和测试步骤
