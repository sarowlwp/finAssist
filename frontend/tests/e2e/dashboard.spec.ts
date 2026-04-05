import { test, expect } from '@playwright/test';
import { mockFinnhubAPI, mockLLMAPI } from '../support/mocks';

test.describe('Dashboard Page', () => {
  test.beforeEach(async ({ page }) => {
    mockFinnhubAPI(page);
    mockLLMAPI(page);
    await page.goto('/');
  });

  test('should display dashboard page elements', async ({ page }) => {
    await expect(page.getByRole('heading', { name: '投资仪表盘' })).toBeVisible();
    await expect(page.getByRole('heading', { name: '持仓分布' })).toBeVisible();
    await expect(page.getByRole('heading', { name: '持仓列表' })).toBeVisible();
  });

  test('should display portfolio holdings with "查看数据" button', async ({ page }) => {
    // 等待表格数据加载
    await expect(page.getByText('AAPL')).toBeVisible();
    await expect(page.getByText('GOOGL')).toBeVisible();
    await expect(page.getByText('TSLA')).toBeVisible();

    // 检查"查看数据"按钮是否存在
    await expect(page.getByRole('button', { name: '查看数据' }).first()).toBeVisible();
  });

  test('should have "今日分析" button', async ({ page }) => {
    await expect(page.getByRole('button', { name: '今日分析' })).toBeVisible();
  });
});
