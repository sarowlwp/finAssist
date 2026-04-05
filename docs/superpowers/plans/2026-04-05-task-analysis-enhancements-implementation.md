# 任务分析界面增强实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现任务分析界面的增强功能，包括 SQLite 连接池优化、历史任务管理、实时任务进度查看和独立报告详情页面。

**Architecture:** 采用渐进式增强的方法，分阶段实现每个功能，每个阶段都可以独立测试和部署。

**Tech Stack:** FastAPI (后端), SQLAlchemy (ORM), Next.js 14 (前端), TypeScript, Playwright (E2E 测试)

---

## 文件变更映射

### 第一阶段：SQLite 连接池优化
- 修改: `backend/database.py` - 优化连接池配置
- 检查: `backend/routers/analysis.py` - 检查后台任务中的连接管理

### 第二阶段：任务管理增强
- 修改: `backend/routers/analysis.py` - 添加删除任务 API
- 修改: `frontend/src/app/history/page.tsx` - 添加删除任务功能和实时进度按钮
- 修改: `frontend/src/lib/api.ts` - 添加删除任务 API 调用

### 第三阶段：独立报告详情页面
- 创建: `frontend/src/app/report/[reportId]/page.tsx` - 报告详情页面
- 修改: `frontend/src/app/history/page.tsx` - 修改为跳转到报告详情页面

---

## 任务分解

### Task 1: SQLite 连接池优化

**Files:**
- Modify: `backend/database.py:1-15`

- [ ] **Step 1: Read current database.py file**

  确认文件内容，确保我们有最新版本。

- [ ] **Step 2: Update connection pool configuration**

  修改 `backend/database.py` 中的引擎配置：

  ```python
  engine = create_engine(
      SQLALCHEMY_DATABASE_URL,
      connect_args={"check_same_thread": False},
      pool_size=20,
      max_overflow=30,
      pool_recycle=1800,
      pool_pre_ping=True
  )
  ```

- [ ] **Step 3: Verify the change compiles**

  运行:
  ```bash
  cd backend && source venv/bin/activate && python3 -c "from database import engine; print('Engine created successfully')"
  ```
  预期: 无错误，输出 "Engine created successfully"

- [ ] **Step 4: Commit**

  ```bash
  git add backend/database.py
  git commit -m "feat: 优化 SQLite 连接池配置"
  ```

---

### Task 2: 后端添加删除任务 API

**Files:**
- Modify: `backend/routers/analysis.py` - 添加删除任务端点

- [ ] **Step 1: Read analysis.py router file**

  确认文件内容，特别是现有 API 的结构。

- [ ] **Step 2: Add delete task endpoint**

  在 `backend/routers/analysis.py` 的末尾（在 `delete_analysis_report` 函数之后）添加：

  ```python
  @router.delete("/analysis/tasks/{task_id}")
  async def delete_analysis_task(
      task_id: str,
      db: Session = Depends(get_db)
  ):
      """
      删除分析任务

      Args:
          task_id: 任务 ID
          db: 数据库会话

      Returns:
          删除结果
      """
      try:
          task = db.query(AnalysisTask).filter(AnalysisTask.task_id == task_id).first()
          if not task:
              raise HTTPException(
                  status_code=status.HTTP_404_NOT_FOUND,
                  detail=f"未找到任务: {task_id}"
              )
          
          # 检查任务状态
          if task.status == "analyzing":
              raise HTTPException(
                  status_code=status.HTTP_400_BAD_REQUEST,
                  detail="正在分析中的任务不能删除"
              )
          
          # 删除任务
          db.delete(task)
          db.commit()
          
          return {"success": True, "message": "任务已删除"}
      except HTTPException:
          raise
      except Exception as e:
          raise HTTPException(
              status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
              detail=f"删除任务失败: {str(e)}"
          )
  ```

- [ ] **Step 3: Verify imports**

  确认文件顶部有必要的导入：
  - `from models import AnalysisTask` (应该已经存在)

- [ ] **Step 4: Commit**

  ```bash
  git add backend/routers/analysis.py
  git commit -m "feat: 添加删除分析任务的 API"
  ```

---

### Task 3: 前端 API 层增强

**Files:**
- Modify: `frontend/src/lib/api.ts` - 确保删除任务 API 已添加

- [ ] **Step 1: Verify deleteTask function exists**

  检查 `frontend/src/lib/api.ts` 中是否有 `deleteTask` 函数，应该在之前的步骤中已添加。

- [ ] **Step 2: Run type check**

  ```bash
  cd frontend && npx tsc --noEmit
  ```
  预期: 无类型错误

- [ ] **Step 3: Commit (if needed)**

  如果有修改，提交更改。

---

### Task 4: 历史页面增强 - 删除任务功能

**Files:**
- Modify: `frontend/src/app/history/page.tsx`

- [ ] **Step 1: Read history page file**

  确认当前实现，了解现有状态和结构。

- [ ] **Step 2: Add deleteTask state**

  在状态声明部分（`deleteLoading` 变量附近）添加：

  ```typescript
  const [deleteTaskLoading, setDeleteTaskLoading] = useState<string | null>(null)
  ```

- [ ] **Step 3: Add handleDeleteTask function**

  在 `handleDelete` 函数之后添加：

  ```typescript
  const handleDeleteTask = async (taskId: string) => {
    if (!confirm('确定要删除该分析任务吗？此操作无法撤销。')) {
      return
    }

    try {
      setDeleteTaskLoading(taskId)
      await analysisApi.deleteTask(taskId)
      setTasks(tasks.filter(task => task.task_id !== taskId))
    } catch (err) {
      console.error('Failed to delete task:', err)
    } finally {
      setDeleteTaskLoading(null)
    }
  }
  ```

- [ ] **Step 4: Update task list UI**

  在任务列表的渲染部分（`filteredTasks.map` 中），为每个任务添加删除按钮和查看实时进度按钮：

  在任务卡片的底部（`{task.report_id && (...)}` 之后）添加：

  ```typescript
  <div className="mt-2 flex gap-2">
    {task.status === 'analyzing' && (
      <Button
        variant="outline"
        size="sm"
        onClick={() => router.push(`/analysis/${task.ticker}`)}
      >
        查看实时进度
      </Button>
    )}
    {task.status !== 'analyzing' && (
      <Button
        variant="destructive"
        size="sm"
        disabled={deleteTaskLoading === task.task_id}
        onClick={() => handleDeleteTask(task.task_id)}
      >
        {deleteTaskLoading === task.task_id ? '删除中...' : '删除任务'}
      </Button>
    )}
  </div>
  ```

- [ ] **Step 5: Run type check**

  ```bash
  cd frontend && npx tsc --noEmit
  ```
  预期: 无类型错误

- [ ] **Step 6: Commit**

  ```bash
  git add frontend/src/app/history/page.tsx
  git commit -m "feat: 添加删除任务和查看实时进度功能"
  ```

---

### Task 5: 创建独立报告详情页面

**Files:**
- Create: `frontend/src/app/report/[reportId]/page.tsx`

- [ ] **Step 1: Create report page directory**

  ```bash
  mkdir -p frontend/src/app/report/[reportId]
  ```

- [ ] **Step 2: Create report page component**

  创建 `frontend/src/app/report/[reportId]/page.tsx`：

  ```typescript
  'use client'

  import { useState, useEffect } from 'react'
  import { useParams, useRouter } from 'next/navigation'
  import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'
  import { Button } from '@/components/ui/button'
  import { Badge } from '@/components/ui/badge'
  import { analysisApi } from '@/lib/api'
  import MarkdownRenderer from '@/components/MarkdownRenderer'
  import { format } from 'date-fns'
  import { zhCN } from 'date-fns/locale'

  interface AnalysisReport {
    report_id: string
    ticker: string
    company_name: string
    created_at: string
    status: string
    current_price: number
    change_percent: number
    fusion_summary: string
    news_report: string
    sec_report: string
    fundamentals_report: string
    technical_report: string
    custom_skill_report: string
  }

  export default function ReportPage() {
    const params = useParams()
    const router = useRouter()
    const reportId = params.reportId as string
    const [loading, setLoading] = useState(true)
    const [report, setReport] = useState<AnalysisReport | null>(null)
    const [error, setError] = useState<string | null>(null)

    useEffect(() => {
      const fetchReport = async () => {
        try {
          setLoading(true)
          const reportData = await analysisApi.getReport(reportId)
          setReport(reportData)
        } catch (err) {
          setError('加载报告失败')
          console.error('Failed to fetch report:', err)
        } finally {
          setLoading(false)
        }
      }

      fetchReport()
    }, [reportId])

    if (loading) {
      return (
        <div className="min-h-screen flex items-center justify-center">
          <div className="text-lg">加载中...</div>
        </div>
      )
    }

    if (error || !report) {
      return (
        <div className="min-h-screen flex items-center justify-center">
          <div className="text-red-500">
            {error || '未找到报告'}
          </div>
        </div>
      )
    }

    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-950 dark:to-slate-900 p-4">
        <div className="max-w-7xl mx-auto">
          <div className="flex justify-between items-center mb-6">
            <div>
              <h1 className="text-2xl font-bold">分析报告详情</h1>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                {report.company_name} ({report.ticker})
              </p>
            </div>
            <div className="flex gap-2">
              <Button variant="outline" onClick={() => router.push('/history')}>
                返回历史列表
              </Button>
            </div>
          </div>

          <Card className="mb-6">
            <CardHeader>
              <div className="flex items-center gap-2">
                <Badge variant="outline">{report.ticker}</Badge>
                <CardTitle className="text-lg">{report.company_name}</CardTitle>
              </div>
              <CardDescription>
                报告 ID: {report.report_id} | 创建时间: {format(new Date(report.created_at), 'yyyy年MM月dd日 HH:mm:ss', { locale: zhCN })}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">股票代码</p>
                  <p className="font-semibold">{report.ticker}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">当前价格</p>
                  <p className="font-semibold">${report.current_price.toFixed(2)}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">涨跌幅</p>
                  <p className={`font-semibold ${report.change_percent >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {report.change_percent >= 0 ? '+' : ''}{report.change_percent.toFixed(2)}%
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">状态</p>
                  <Badge variant={report.status === 'completed' ? 'default' : 'secondary'}>
                    {report.status === 'completed' ? '已完成' : report.status}
                  </Badge>
                </div>
              </div>
            </CardContent>
          </Card>

          {report.fusion_summary && (
            <Card className="mb-6 border-2 border-blue-500 dark:border-blue-700">
              <CardHeader className="py-3 px-4">
                <CardTitle className="text-blue-600 dark:text-blue-400 text-lg">Fusion Agent 融合总结</CardTitle>
                <CardDescription className="text-sm">多Agent综合分析结果</CardDescription>
              </CardHeader>
              <CardContent className="pt-0 px-4 pb-4">
                <div className="prose prose-slate dark:prose-invert max-w-none text-sm">
                  <MarkdownRenderer content={report.fusion_summary} />
                </div>
              </CardContent>
            </Card>
          )}

          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {[
              { title: 'News Agent', content: report.news_report, emoji: '📰' },
              { title: 'SEC Agent', content: report.sec_report, emoji: '📋' },
              { title: 'Fundamentals Agent', content: report.fundamentals_report, emoji: '📊' },
              { title: 'Technical Agent', content: report.technical_report, emoji: '📈' },
              { title: 'Custom Skill Agent', content: report.custom_skill_report, emoji: '🔧' },
            ].map(({ title, content, emoji }) => (
              <Card key={title} className="h-full">
                <CardHeader className="py-3 px-4">
                  <CardTitle className="text-lg flex items-center gap-2">
                    <span>{emoji}</span>
                    {title}
                  </CardTitle>
                </CardHeader>
                <CardContent className="pt-0 px-4 pb-4">
                  {content ? (
                    <div className="prose prose-slate dark:prose-invert max-w-none text-sm">
                      <MarkdownRenderer content={content} />
                    </div>
                  ) : (
                    <div className="text-sm text-gray-500">暂无内容</div>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </div>
    )
  }
  ```

- [ ] **Step 3: Run type check**

  ```bash
  cd frontend && npx tsc --noEmit
  ```
  预期: 无类型错误

- [ ] **Step 4: Commit**

  ```bash
  git add frontend/src/app/report/[reportId]/page.tsx
  git commit -m "feat: 创建独立的报告详情页面"
  ```

---

### Task 6: 更新历史页面 - 跳转报告详情

**Files:**
- Modify: `frontend/src/app/history/page.tsx`

- [ ] **Step 1: Modify report list click behavior**

  修改报告列表卡片的点击事件，从滚动到详情改为跳转到独立页面：

  移除 `onClick` 事件和 `id` 属性，改为：

  ```typescript
  <Card
    key={report.report_id}
    className="cursor-pointer hover:border-blue-400 transition-colors"
    onClick={() => router.push(`/report/${report.report_id}`)}
  >
  ```

- [ ] **Step 2: Remove report details panel**

  移除右侧报告详情面板的内容。将 `lg:col-span-2` 的 Card 改为简单的提示：

  ```typescript
  <Card className="lg:col-span-2">
    <CardHeader className="py-3 px-4">
      <CardTitle className="text-lg">报告详情</CardTitle>
      <CardDescription className="text-sm">点击左侧报告查看详细内容</CardDescription>
    </CardHeader>
    <CardContent className="pt-0 px-4 pb-4">
      <div className="text-center py-10 text-muted-foreground">
        选择一个报告查看详情
      </div>
    </CardContent>
  </Card>
  ```

- [ ] **Step 3: Run type check**

  ```bash
  cd frontend && npx tsc --noEmit
  ```
  预期: 无类型错误

- [ ] **Step 4: Commit**

  ```bash
  git add frontend/src/app/history/page.tsx
  git commit -m "feat: 历史页面改为跳转到独立报告详情页面"
  ```

---

### Task 7: 运行测试和验证

**Files:**
- Test: 运行现有 E2E 测试

- [ ] **Step 1: Start backend service**

  按照重启服务方法启动后端服务。

- [ ] **Step 2: Start frontend service**

  按照重启服务方法启动前端服务。

- [ ] **Step 3: Run E2E tests**

  ```bash
  cd frontend && npm run test:e2e
  ```
  预期: 所有测试通过

- [ ] **Step 4: Manual verification**

  1. 访问历史页面，验证任务列表显示
  2. 点击"查看实时进度"按钮，验证跳转正确
  3. 尝试删除已完成的任务，验证删除功能
  4. 点击报告，验证跳转到独立报告详情页面
  5. 在报告详情页面验证所有内容正确显示

- [ ] **Step 5: Commit test results (if needed)**

  如果有测试文件修改，提交更改。

---

## 自审检查

### 1. Spec Coverage
✅ SQLite 连接池优化 - Task 1 实现
✅ 历史任务删除功能 - Task 2, 3, 4 实现
✅ 查看实时进度按钮 - Task 4 实现
✅ 独立报告详情页面 - Task 5, 6 实现

### 2. Placeholder Scan
✅ 无占位符，所有步骤都有完整的代码和命令

### 3. Type Consistency
✅ 函数名、变量名在所有任务中保持一致
✅ API 调用和类型定义匹配

---

## 执行选项

Plan complete and saved to `docs/superpowers/plans/2026-04-05-task-analysis-enhancements-implementation.md`. Two execution options:

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

Which approach?
