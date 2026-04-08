# E2E 测试要求

## 概述

本项目采用 Playwright 作为 E2E（端到端）测试框架，确保应用在各种场景下的功能正确性、用户体验一致性和系统稳定性。

## 测试文件结构

```
frontend/
├── tests/
│   ├── e2e/                 # E2E 测试文件
│   │   ├── analysis.spec.ts  # 分析页面测试
│   │   ├── agents.spec.ts    # Agent 管理页面测试
│   │   ├── history.spec.ts   # 历史页面测试
│   │   ├── portfolio.spec.ts # 持仓管理页面测试
│   │   ├── settings.spec.ts  # 设置页面测试
│   │   └── full-test-suite.spec.ts # 完整功能测试套件
│   └── support/
│       ├── mocks/            # API 模拟响应
│       ├── fixtures.ts       # 测试装置
│       └── helpers.ts        # 辅助函数
```

## 测试执行

### 运行所有测试

```bash
cd frontend
npx playwright test --project=chromium
```

### 运行特定测试文件

```bash
cd frontend
npx playwright test tests/e2e/full-test-suite.spec.ts --project=chromium
```

### 查看测试报告

```bash
cd frontend
npx playwright show-report
```

## 测试要求

### 1. 覆盖范围要求

#### 页面覆盖
- [ ] 首页仪表盘
- [ ] 持仓管理
- [ ] 分析页面（异步/实时模式）
- [ ] 历史页面（任务状态/报告查看）
- [ ] Agent 管理
- [ ] 设置页面

#### 核心功能覆盖
- [ ] 异步任务管理
- [ ] 实时分析功能
- [ ] 投资组合管理
- [ ] 报告历史查询
- [ ] Agent 交互
- [ ] 主题切换（白天/夜间模式）
- [ ] 导航功能

### 2. 测试规范

#### 命名规范
- 测试文件使用 `.spec.ts` 扩展名
- 测试描述使用中文
- 测试分组使用 `test.describe`
- 每个测试包含明确的目的说明

#### 代码规范
```typescript
// 示例：正确的测试结构
test.describe('页面功能描述', () => {
  test.beforeEach(async ({ page }) => {
    // 页面初始化和数据准备
  });

  test('测试功能描述', async ({ page }) => {
    // 测试逻辑
  });
});
```

#### 断言规范
- 使用 `expect` 进行断言
- 优先使用 `getByRole` 定位元素
- 避免使用硬编码的选择器（如 `.class-name`）
- 确保断言可见性而非存在性

### 3. 测试稳定性

#### 避免超时
- 确保测试执行时间合理（单测试 < 10 秒）
- 关键操作添加适当等待
- 避免不必要的 `page.waitForTimeout()`

#### 避免不稳定测试
- 确保测试数据隔离
- 使用 `test.beforeEach` 和 `test.afterEach` 管理状态
- 避免测试依赖外部资源

### 4. 测试报告

#### 生成报告
```bash
cd frontend
npx playwright test --reporter=html
```

#### 报告查看
报告位于 `playwright-report/` 目录中，包含：
- 测试执行时间
- 失败截图
- 错误信息
- 网络请求日志

## 测试维护

### 1. 测试更新
- 页面结构改变时同步更新对应测试
- 功能增强时补充新的测试
- 删除功能时移除对应的测试

### 2. 定期执行
- 提交代码前运行受影响的测试
- 每日执行完整测试套件
- 部署前执行所有 E2E 测试

### 3. 问题定位

#### 失败测试分析
1. 检查 `test-results/` 目录下的截图和日志
2. 分析网络请求和响应
3. 检查控制台错误信息
4. 定位到具体测试步骤

#### 常见问题
- **超时**：增加等待时间或优化测试逻辑
- **元素定位**：使用更稳定的选择器
- **数据依赖**：确保测试数据的一致性

## 示例测试

```typescript
import { test, expect } from '@playwright/test';
import { mockFinnhubAPI, mockLLMAPI } from '../support/mocks';

test.describe('异步分析任务管理', () => {
  test.beforeEach(async ({ page }) => {
    mockFinnhubAPI(page);
    mockLLMAPI(page);
    await page.goto('/analysis/AAPL');
  });

  test('显示分析选项页面', async ({ page }) => {
    await expect(page.getByRole('heading', { name: 'AAPL 分析' })).toBeVisible();
    await expect(page.getByRole('button', { name: '实时分析' })).toBeVisible();
    await expect(page.getByRole('button', { name: '异步分析' })).toBeVisible();
  });
});
```

## CI/CD 集成

### GitHub Actions 工作流程

```yaml
name: E2E Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '18'
      - run: cd frontend && npm ci
      - run: cd frontend && npx playwright install --with-deps chromium
      - run: cd frontend && npx playwright test --project=chromium
      - uses: actions/upload-artifact@v4
        if: always()
        with:
          name: test-results
          path: frontend/test-results/
```

## 最佳实践

1. **独立测试**：每个测试应该相互独立，避免共享状态
2. **可重复性**：相同的测试在相同条件下应产生相同的结果
3. **稳定性**：测试应该稳定且可靠，避免波动
4. **速度**：保持测试执行快速，便于开发循环
5. **清晰度**：测试代码应易于理解和维护
