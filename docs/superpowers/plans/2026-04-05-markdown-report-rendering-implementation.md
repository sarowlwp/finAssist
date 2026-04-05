# Markdown 报告渲染系统实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现功能强大的 Markdown 渲染系统，改进金融分析报告的阅读体验，支持完整的 Markdown 语法、代码高亮、表格渲染和目录导航。

**Architecture:** 使用 react-markdown 作为核心渲染引擎，remark-gfm 提供 GFM 支持，react-syntax-highlighter 实现代码高亮。采用 Tailwind CSS 和 shadcn/ui 组件构建响应式界面，支持夜间模式。

**Tech Stack:** React 18 + TypeScript, react-markdown, remark-gfm, react-syntax-highlighter, Tailwind CSS, shadcn/ui, Playwright E2E 测试。

---

## 文件结构

**创建/修改的文件：**
1. `frontend/src/components/MarkdownRenderer.tsx` - 新组件，Markdown 渲染器
2. `frontend/src/components/analysis/AgentReportCard.tsx` - 修改，使用新渲染器
3. `frontend/src/app/analysis/[ticker]/page.tsx` - 修改，集成新渲染系统
4. `frontend/package.json` - 新增依赖

**测试文件：**
- `frontend/e2e/analysis.spec.ts` - 更新测试用例

---

## 阶段1：基础渲染

### 任务1：安装依赖

**Files:**
- Modify: `frontend/package.json`

- [ ] **步骤1：添加依赖到 package.json**

在 `dependencies` 部分添加：
```json
"react-markdown": "^9.0.1",
"remark-gfm": "^4.0.0",
"react-syntax-highlighter": "^15.5.0"
```

- [ ] **步骤2：安装依赖**

Run:
```bash
cd frontend && npm install
```

- [ ] **步骤3：验证安装**

Run:
```bash
cd frontend && npm list react-markdown remark-gfm react-syntax-highlighter
```

Expected: 显示已安装的依赖版本

- [ ] **步骤4：提交**

Run:
```bash
cd frontend && git add package.json package-lock.json && git commit -m "feat: 安装 Markdown 渲染依赖"
```

### 任务2：创建 MarkdownRenderer 组件

**Files:**
- Create: `frontend/src/components/MarkdownRenderer.tsx`

- [ ] **步骤1：创建组件文件**

```typescript
'use client'

import React from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { vscDarkPlus, vs } from 'react-syntax-highlighter/dist/esm/styles/prism'

interface MarkdownRendererProps {
  content: string
  className?: string
  darkMode?: boolean
}

const MarkdownRenderer: React.FC<MarkdownRendererProps> = ({
  content,
  className = '',
  darkMode = false
}) => {
  return (
    <div className={`markdown-renderer ${className}`}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          code({ node, inline, className, children, ...props }) {
            const match = /language-(\w+)/.exec(className || '')
            const language = match ? match[1] : ''

            if (!inline && match) {
              return (
                <div className="my-4 rounded-lg overflow-hidden bg-gray-50 dark:bg-gray-800">
                  <div className="px-4 py-2 bg-gray-100 dark:bg-gray-700 text-xs font-medium text-gray-600 dark:text-gray-300">
                    {language}
                  </div>
                  <SyntaxHighlighter
                    style={darkMode ? vscDarkPlus : vs}
                    language={language}
                    PreTag="div"
                    customStyle={{
                      margin: 0,
                      borderRadius: 0,
                      padding: '1rem'
                    }}
                    {...props}
                  >
                    {String(children).replace(/\n$/, '')}
                  </SyntaxHighlighter>
                </div>
              )
            }

            return (
              <code
                className={`inline-code px-1.5 py-0.5 rounded text-sm bg-gray-100 dark:bg-gray-800 ${className}`}
                {...props}
              >
                {children}
              </code>
            )
          },
          table({ children }) {
            return (
              <div className="my-4 overflow-x-auto">
                <table className="w-full text-sm text-left border-collapse">
                  {children}
                </table>
              </div>
            )
          },
          thead({ children }) {
            return (
              <thead className="bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-white font-semibold">
                {children}
              </thead>
            )
          },
          tbody({ children }) {
            return <tbody className="divide-y divide-gray-200 dark:divide-gray-700">{children}</tbody>
          },
          tr({ children }) {
            return <tr className="hover:bg-gray-50 dark:hover:bg-gray-800">{children}</tr>
          },
          th({ children }) {
            return <th className="px-4 py-2 border">{children}</th>
          },
          td({ children }) {
            return <td className="px-4 py-2 border">{children}</td>
          },
          a({ children, href, ...props }) {
            return (
              <a
                href={href}
                target={href?.startsWith('http') ? '_blank' : '_self'}
                rel={href?.startsWith('http') ? 'noopener noreferrer' : ''}
                className="text-blue-600 dark:text-blue-400 hover:underline"
                {...props}
              >
                {children}
                {href?.startsWith('http') && (
                  <span className="ml-1 text-xs opacity-70">↗</span>
                )}
              </a>
            )
          },
          h1({ children }) {
            return <h1 className="text-3xl font-bold mb-6 text-gray-900 dark:text-white">{children}</h1>
          },
          h2({ children }) {
            return <h2 className="text-2xl font-semibold mt-8 mb-4 text-gray-900 dark:text-white">{children}</h2>
          },
          h3({ children }) {
            return <h3 className="text-xl font-semibold mt-6 mb-3 text-gray-900 dark:text-white">{children}</h3>
          },
          h4({ children }) {
            return <h4 className="text-lg font-medium mt-4 mb-2 text-gray-900 dark:text-white">{children}</h4>
          },
          p({ children }) {
            return <p className="mb-4 text-gray-700 dark:text-gray-300 leading-relaxed">{children}</p>
          },
          ul({ children }) {
            return <ul className="mb-4 pl-6 list-disc text-gray-700 dark:text-gray-300">{children}</ul>
          },
          ol({ children }) {
            return <ol className="mb-4 pl-6 list-decimal text-gray-700 dark:text-gray-300">{children}</ol>
          },
          li({ children }) {
            return <li className="mb-1 leading-relaxed">{children}</li>
          },
          blockquote({ children }) {
            return (
              <blockquote className="my-4 p-4 border-l-4 border-blue-500 bg-blue-50 dark:bg-blue-900/20 text-gray-700 dark:text-gray-300">
                {children}
              </blockquote>
            )
          },
          hr() {
            return <hr className="my-8 border-gray-200 dark:border-gray-700" />
          }
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  )
}

export default MarkdownRenderer
```

- [ ] **步骤2：运行类型检查**

Run:
```bash
cd frontend && npx tsc
```

Expected: 无类型错误

- [ ] **步骤3：提交**

Run:
```bash
cd frontend && git add src/components/MarkdownRenderer.tsx && git commit -m "feat: 创建 MarkdownRenderer 组件"
```

---

## 阶段2：集成到分析页面

### 任务3：更新 AgentReportCard 组件

**Files:**
- Modify: `frontend/src/components/analysis/AgentReportCard.tsx` (需先确认文件是否存在)

- [ ] **步骤1：检查并创建组件**

Run:
```bash
ls -la /Users/sarowlwp/Document/go/finAssist/frontend/src/components/analysis
```

如果文件不存在，先创建：

```typescript
'use client'

import React from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import MarkdownRenderer from '@/components/MarkdownRenderer'

interface AgentReportCardProps {
  title: string
  emoji: string
  content: string
  defaultCollapsed?: boolean
}

const AgentReportCard: React.FC<AgentReportCardProps> = ({
  title,
  emoji,
  content,
  defaultCollapsed = false
}) => {
  const [collapsed, setCollapsed] = React.useState(defaultCollapsed)

  return (
    <Card className="mb-4">
      <CardHeader
        className="cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors py-3 px-4"
        onClick={() => setCollapsed(!collapsed)}
      >
        <div className="flex justify-between items-center">
          <CardTitle className="flex items-center gap-2 text-base">
            <span>{emoji}</span>
            {title}
          </CardTitle>
          <span className="text-gray-400 text-sm">
            {collapsed ? '▼' : '▲'}
          </span>
        </div>
      </CardHeader>
      {!collapsed && (
        <CardContent className="pt-0 px-4 pb-4">
          <MarkdownRenderer content={content} />
        </CardContent>
      )}
    </Card>
  )
}

export default AgentReportCard
```

- [ ] **步骤2：提交**

Run:
```bash
cd frontend && git add src/components/analysis/AgentReportCard.tsx && git commit -m "feat: 创建 AgentReportCard 组件"
```

### 任务4：更新分析页面

**Files:**
- Modify: `frontend/src/app/analysis/[ticker]/page.tsx`

- [ ] **步骤1：替换渲染逻辑**

找到当前的 `renderMarkdown` 函数和使用该函数的地方，替换为 `MarkdownRenderer` 组件。

修改后的页面需要：
1. 导入 MarkdownRenderer 和 AgentReportCard
2. 替换 renderMarkdown 调用
3. 为每个 Agent 报告使用 AgentReportCard 组件

- [ ] **步骤2：验证构建**

Run:
```bash
cd frontend && npm run build
```

Expected: 构建成功

- [ ] **步骤3：运行开发服务器**

Run:
```bash
cd frontend && npm run dev
```

然后访问 http://localhost:3000/analysis/AAPL 测试

- [ ] **步骤4：提交**

Run:
```bash
cd frontend && git add src/app/analysis/[ticker]/page.tsx && git commit -m "feat: 集成 Markdown 渲染系统到分析页面"
```

---

## 阶段3：优化和测试

### 任务5：添加目录导航

**Files:**
- Modify: `frontend/src/app/analysis/[ticker]/page.tsx`
- Create: `frontend/src/components/TableOfContents.tsx`

- [ ] **步骤1：创建目录组件**

```typescript
'use client'

import React from 'react'
import { ScrollArea } from '@/components/ui/scroll-area'

interface TableOfContentsProps {
  headings: Array<{ id: string; text: string; level: number }>
  onHeadingClick: (id: string) => void
}

const TableOfContents: React.FC<TableOfContentsProps> = ({ headings, onHeadingClick }) => {
  if (headings.length === 0) {
    return null
  }

  return (
    <div className="sticky top-6 hidden lg:block">
      <div className="bg-white dark:bg-gray-800 rounded-lg p-4 shadow-sm border border-gray-200 dark:border-gray-700">
        <h3 className="text-sm font-semibold mb-3 text-gray-900 dark:text-white">目录</h3>
        <ScrollArea className="h-[calc(100vh-12rem)]">
          <nav className="text-sm">
            {headings.map((heading) => (
              <a
                key={heading.id}
                href={`#${heading.id}`}
                onClick={(e) => {
                  e.preventDefault()
                  onHeadingClick(heading.id)
                }}
                className="block py-1.5 px-2 rounded hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-600 dark:text-gray-300 transition-colors"
                style={{ marginLeft: `${(heading.level - 2) * 16}px` }}
              >
                {heading.text}
              </a>
            ))}
          </nav>
        </ScrollArea>
      </div>
    </div>
  )
}

export default TableOfContents
```

- [ ] **步骤2：在分析页面中使用**

修改 `frontend/src/app/analysis/[ticker]/page.tsx`，添加目录功能。

- [ ] **步骤3：提交**

Run:
```bash
cd frontend && git add src/components/TableOfContents.tsx src/app/analysis/[ticker]/page.tsx && git commit -m "feat: 添加目录导航功能"
```

### 任务6：E2E 测试

**Files:**
- Modify: `frontend/e2e/analysis.spec.ts`

- [ ] **步骤1：更新测试用例**

Run:
```bash
cd frontend && git status
```

如果有测试文件，更新以使用新的定位器：

```typescript
import { test, expect } from '@playwright/test'

test('分析页面 Markdown 渲染测试', async ({ page }) => {
  await page.goto('/analysis/AAPL')
  await page.waitForLoadState('networkidle')

  // 验证 Markdown 内容渲染
  const fusionSummary = page.locator('[data-testid="fusion-summary"]')
  await expect(fusionSummary).toBeVisible()

  // 验证 Agent 报告卡片
  const agentReports = page.locator('[data-testid="agent-report"]')
  await expect(agentReports).toHaveCount(5)

  // 验证 Markdown 元素
  const headings = page.locator('h1, h2, h3, h4, h5, h6')
  await expect(headings).not.toBeEmpty()

  // 验证链接渲染
  const links = page.locator('a')
  await expect(links).not.toBeEmpty()
})
```

- [ ] **步骤2：运行测试**

Run:
```bash
cd frontend && npx playwright install
npm run test:e2e
```

- [ ] **步骤3：修复失败的测试**

根据测试结果修复问题。

- [ ] **步骤4：提交**

Run:
```bash
cd frontend && git add frontend/e2e/analysis.spec.ts && git commit -m "test: 更新分析页面测试用例"
```

---

## 阶段4：最终优化

### 任务7：优化和修复

**Files:**
- Modify: 可能涉及多个文件

- [ ] **步骤1：优化夜间模式**

确保 Markdown 渲染器在夜间模式下显示正确。

- [ ] **步骤2：优化响应式设计**

确保在移动设备上的布局正确。

- [ ] **步骤3：性能优化**

添加代码分割或懒加载。

- [ ] **步骤4：提交**

Run:
```bash
cd frontend && git add src/components/MarkdownRenderer.tsx src/app/analysis/[ticker]/page.tsx && git commit -m "perf: 优化 Markdown 渲染器性能和响应式"
```

### 任务8：构建和部署验证

- [ ] **步骤1：构建项目**

Run:
```bash
cd frontend && npm run build
```

Expected: 构建成功

- [ ] **步骤2：启动开发服务器**

Run:
```bash
cd frontend && npm run dev
```

然后访问 http://localhost:3000/analysis/AAPL 验证所有功能正常。

- [ ] **步骤3：检查是否有未提交的文件**

Run:
```bash
cd frontend && git status
```

- [ ] **步骤4：最终提交**

如果有其他修改，提交：

Run:
```bash
cd frontend && git add . && git commit -m "feat: 完成 Markdown 报告渲染系统实现"
```

---

## 执行选项

**Plan complete and saved to `docs/superpowers/plans/2026-04-05-markdown-report-rendering-implementation.md`.**

**执行选项：**
1. **Subagent-Driven (推荐)** - 我将调度 subagent 来逐个执行任务，快速迭代
2. **Inline Execution** - 在当前会话中执行任务，批量处理

您希望使用哪种方式？
