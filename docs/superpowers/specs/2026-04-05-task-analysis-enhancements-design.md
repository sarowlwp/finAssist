---
name: task-analysis-enhancements
title: 任务分析界面增强设计
date: 2026-04-05
version: 1.0
status: approved
---

# 任务分析界面增强设计

## 概述

本设计文档描述了对任务分析界面的增强，包括历史任务管理、实时任务进度查看、SQLite 连接池优化以及独立报告详情页面的实现方案。

## 设计原则

- 渐进式增强：先解决最紧急的问题，然后逐步完善功能
- 保持代码稳定性：尽量减少对现有功能的影响
- 风险可控：每个改进都有明确的测试和验证方法

## 需求分析

### 1. 历史任务管理

- 支持删除历史任务
- 任务删除前需要确认
- 处理删除操作的错误和加载状态

### 2. 实时任务进度查看

- 为"分析中"状态的任务添加"查看实时进度"按钮
- 点击按钮跳转到对应的分析页面
- 传递任务 ID 等参数以确保进度显示正确性

### 3. SQLite 连接池问题

- 解决 "queue pool limit of size 5 overflow 10 reach" 错误
- 优化 SQLAlchemy 连接池配置
- 检查并修复连接泄漏问题

### 4. 独立报告详情页面

- 创建独立的报告详情页面 `/report/[reportId]`
- 专门用于展示单个报告的完整内容
- 保持与现有设计风格一致

## 技术架构

### 1. 后端架构

#### 1.1 数据库连接优化

修改 `backend/database.py` 中的 SQLAlchemy 引擎配置：

```python
# 优化后的连接池配置
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    pool_size=20,
    max_overflow=30,
    pool_recycle=1800,
    pool_pre_ping=True
)
```

#### 1.2 任务管理 API

在 `backend/routers/analysis.py` 中添加删除任务的 API：

```python
@router.delete("/analysis/tasks/{task_id}")
async def delete_analysis_task(
    task_id: str,
    db: Session = Depends(get_db)
):
    """
    删除分析任务
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

### 2. 前端架构

#### 2.1 历史任务管理组件

修改 `frontend/src/app/history/page.tsx`：

```typescript
// 添加删除任务功能
const handleDeleteTask = async (taskId: string) => {
  if (!confirm('确定要删除该分析任务吗？此操作无法撤销。')) {
    return
  }

  try {
    setDeleteLoading(taskId)
    await analysisApi.deleteTask(taskId)
    setTasks(tasks.filter(task => task.task_id !== taskId))
  } catch (err) {
    console.error('Failed to delete task:', err)
  } finally {
    setDeleteLoading(null)
  }
}

// 在任务列表中添加"查看实时进度"按钮
{task.status === 'analyzing' && (
  <Button
    variant="outline"
    size="sm"
    onClick={() => router.push(`/analysis/${task.ticker}`)}
  >
    查看实时进度
  </Button>
)}
```

#### 2.2 独立报告详情页面

创建 `frontend/src/app/report/[reportId]/page.tsx`：

```typescript
'use client'

import { useState, useEffect } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
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
          <h1 className="text-2xl font-bold">分析报告详情</h1>
          <Button onClick={() => router.back()}>返回</Button>
        </div>

        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="text-lg">{report.company_name}</CardTitle>
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
                  <MarkdownRenderer content={content} />
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

## 实现计划

### 第一阶段：SQLite 连接池优化

1. 修改 `backend/database.py` 中的连接池配置
2. 测试连接池优化后的效果
3. 检查并修复代码中的连接泄漏问题

### 第二阶段：任务管理增强

1. 在后端添加删除任务的 API
2. 在前端添加任务删除功能
3. 为分析中任务添加"查看实时进度"按钮

### 第三阶段：报告详情页面

1. 创建 `frontend/src/app/report/[reportId]/page.tsx`
2. 实现报告详情页面的功能
3. 修改历史页面，添加跳转到报告详情页面的链接

## 测试计划

1. 测试任务删除功能
2. 测试"查看实时进度"按钮跳转功能
3. 测试报告详情页面的显示
4. 压力测试数据库连接池优化后的效果

## 风险评估

- **SQLite 连接池优化风险**：低，配置变更不会影响现有功能
- **任务管理增强风险**：中，需要修改数据库操作和前端界面
- **报告详情页面风险**：高，需要创建新页面和重构代码

## 后续改进

1. 为任务删除操作添加日志记录
2. 实现任务批量删除功能
3. 为报告详情页面添加下载功能
4. 优化报告加载性能
