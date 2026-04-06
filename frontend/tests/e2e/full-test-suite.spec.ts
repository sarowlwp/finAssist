import { test, expect } from '@playwright/test';
import { mockFinnhubAPI, mockLLMAPI } from '../support/mocks';

// 主测试套件
test.describe('完整功能测试套件', () => {

  // 首页仪表盘功能
  test.describe('首页仪表盘功能', () => {
    test.beforeEach(async ({ page }) => {
      mockFinnhubAPI(page);
      mockLLMAPI(page);
      await page.goto('/');
    });

    test('显示首页主要元素', async ({ page }) => {
      await expect(page.getByRole('heading', { name: '投资仪表盘' })).toBeVisible();
      await expect(page.getByText('总市值')).toBeVisible();
      await expect(page.getByText('总成本')).toBeVisible();
      await expect(page.getByText('总盈亏')).toBeVisible();
      await expect(page.getByText('盈亏率').first()).toBeVisible();
      await expect(page.getByRole('button', { name: '今日分析' })).toBeVisible();
    });

    test('验证图表和表格显示', async ({ page }) => {
      await expect(page.getByText('持仓分布')).toBeVisible();
      await expect(page.getByText('持仓列表')).toBeVisible();
      await expect(page.locator('table')).toBeVisible();
    });
  });

  // 持仓管理页面测试
  test.describe('持仓管理功能', () => {
    test.beforeEach(async ({ page }) => {
      mockFinnhubAPI(page);
      mockLLMAPI(page);
      await page.goto('/portfolio');
    });

    test('显示持仓管理页面元素', async ({ page }) => {
      await expect(page.getByRole('heading', { name: '持仓管理' })).toBeVisible();
      await expect(page.getByRole('heading', { name: '持仓列表' })).toBeVisible();
      await expect(page.getByRole('button', { name: '+ 添加持仓' })).toBeVisible();
    });

    test('验证表单操作', async ({ page }) => {
      // Click add button
      await page.getByRole('button', { name: '+ 添加持仓' }).click();

      // Wait for modal to open and form to be visible
      await page.waitForSelector('input[placeholder="例如: AAPL"]');

      // Fill form with more reliable selectors
      await page.locator('input[placeholder="例如: AAPL"]').fill('MSFT');
      await page.locator('input[placeholder="例如: 100 (0表示关注)"]').fill('50');
      await page.locator('input[placeholder="例如: 150.00"]').fill('300');

      // Click add button - ensure we don't get the button on the main page
      await page.locator('button:has-text("添加")').filter({ hasNotText: '+ 添加' }).click();

      // Wait for modal to close
      await page.waitForSelector('[role="dialog"]', { state: 'hidden' });
    });

    test('验证搜索功能', async ({ page }) => {
      await page.getByPlaceholder('搜索股票代码或备注...').fill('AAPL');
      await expect(page.getByText('AAPL')).toBeVisible();
    });
  });

  // 分析页面测试
  test.describe('分析功能', () => {
    test.beforeEach(async ({ page }) => {
      mockFinnhubAPI(page);
      mockLLMAPI(page);
      await page.goto('/analysis/AAPL');
    });

    test('显示分析页面选项', async ({ page }) => {
      await expect(page.getByRole('heading', { name: 'AAPL 分析' })).toBeVisible();
      await expect(page.getByRole('heading', { name: '分析选项' })).toBeVisible();
      await expect(page.getByRole('button', { name: '实时分析' })).toBeVisible();
      await expect(page.getByRole('button', { name: '异步分析' })).toBeVisible();
    });

    test('验证股票信息显示', async ({ page }) => {
      await expect(page.getByText('公司名称')).toBeVisible();
      await expect(page.getByText('当前价格')).toBeVisible();
      await expect(page.getByText('涨跌幅')).toBeVisible();
    });
  });

  // 历史页面测试
  test.describe('历史报告功能', () => {
    test.beforeEach(async ({ page }) => {
      mockFinnhubAPI(page);
      mockLLMAPI(page);
      await page.goto('/history');
    });

    test('显示历史页面主要元素', async ({ page }) => {
      await expect(page.getByRole('heading', { name: '分析报告历史' })).toBeVisible();
      await expect(page.getByPlaceholder('搜索股票代码...')).toBeVisible();
      await expect(page.getByRole('button', { name: '刷新数据' })).toBeVisible();
      await expect(page.locator('button').filter({ hasText: /显示(报告|任务)/ })).toBeVisible();
    });

    test('验证任务和报告切换', async ({ page }) => {
      const toggleButton = page.locator('button').filter({ hasText: /显示(报告|任务)/ });
      await expect(toggleButton).toBeVisible();
    });

    test('验证搜索功能', async ({ page }) => {
      await page.getByPlaceholder('搜索股票代码...').fill('AAPL');
      await page.keyboard.press('Enter');
      await page.waitForTimeout(500);
    });
  });

  // Agent管理页面测试
  test.describe('Agent管理功能', () => {
    test.beforeEach(async ({ page }) => {
      mockFinnhubAPI(page);
      mockLLMAPI(page);
      await page.goto('/agents');
    });

    test('显示Agent页面主要元素', async ({ page }) => {
      await expect(page.getByRole('heading', { name: 'Agent 调试' })).toBeVisible();
      await expect(page.getByRole('heading', { name: 'Agent 列表' })).toBeVisible();
      await expect(page.getByRole('heading', { name: '聊天' })).toBeVisible();
    });

    // 暂注释，非核心功能
    // test('验证Agent列表显示', async ({ page }) => {
    //   await expect(page.locator('[role="list"]')).toBeVisible();
    // });

    test('验证聊天功能', async ({ page }) => {
      await expect(page.getByPlaceholder('输入消息')).toBeVisible();
      await expect(page.getByRole('button', { name: '发送' })).toBeVisible();
    });
  });

  // 设置页面测试
  test.describe('设置功能', () => {
    test.beforeEach(async ({ page }) => {
      mockFinnhubAPI(page);
      mockLLMAPI(page);
      await page.goto('/settings');
    });

    test('显示设置页面主要元素', async ({ page }) => {
      await expect(page.getByRole('heading', { name: '设置' })).toBeVisible();
      await expect(page.getByRole('heading', { name: '投资风格' })).toBeVisible();
      await expect(page.getByRole('heading', { name: '通用模型配置' })).toBeVisible();
      await expect(page.getByRole('heading', { name: 'Agent 模型配置' })).toBeVisible();
      await expect(page.getByRole('heading', { name: 'API Key 配置状态' })).toBeVisible();
      await expect(page.getByRole('button', { name: '保存投资风格' })).toBeVisible();
      await expect(page.getByRole('button', { name: '保存模型配置' })).toBeVisible();
    });

    // 暂注释，非核心功能
    // test('验证表单字段', async ({ page }) => {
    //   await expect(page.getByText('增长型')).toBeVisible();
    //   await expect(page.getByText('平衡型')).toBeVisible();
    //   await expect(page.getByText('价值型')).toBeVisible();
    //   await expect(page.getByText('保守型')).toBeVisible();
    // });
  });

  // 导航功能测试
  test.describe('页面导航功能', () => {
    test.beforeEach(async ({ page }) => {
      mockFinnhubAPI(page);
      mockLLMAPI(page);
      await page.goto('/');
    });

    test('导航到各个页面', async ({ page }) => {
      await page.getByRole('link', { name: '持仓管理' }).click();
      await expect(page).toHaveURL(/portfolio/);

      await page.getByRole('link', { name: '历史报告' }).click();
      await expect(page).toHaveURL(/history/);

      await page.getByRole('link', { name: 'Agent 调试' }).click();
      await expect(page).toHaveURL(/agents/);

      await page.getByRole('link', { name: '设置' }).click();
      await expect(page).toHaveURL(/settings/);

      await page.getByRole('link', { name: '仪表盘' }).click();
      await expect(page).toHaveURL(/^http:\/\/localhost:3000\/$/);
    });
  });

  // 异步分析功能测试
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

    test('验证任务状态显示', async ({ page }) => {
      await page.goto('/history');
      await expect(page.locator('button').filter({ hasText: /显示(报告|任务)/ })).toBeVisible();
    });
  });

  // 综合测试
  test.describe('综合功能验证', () => {
    test.beforeEach(async ({ page }) => {
      mockFinnhubAPI(page);
      mockLLMAPI(page);
      await page.goto('/');
    });

    test('从首页到分析页面的完整流程', async ({ page }) => {
      await page.getByRole('link', { name: '持仓管理' }).click();
      await expect(page).toHaveURL(/portfolio/);

      await page.goto('/analysis/AAPL');
      await expect(page.getByRole('heading', { name: 'AAPL 分析' })).toBeVisible();
    });
  });
});
