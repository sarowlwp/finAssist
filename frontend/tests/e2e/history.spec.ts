import { test, expect } from '@playwright/test';
import { mockFinnhubAPI, mockLLMAPI } from '../support/mocks';

test.describe('History Page', () => {
  test.beforeEach(async ({ page }) => {
    mockFinnhubAPI(page);
    mockLLMAPI(page);
    await page.goto('/history');
  });

  test('should display history page elements', async ({ page }) => {
    // Check main elements
    await expect(page.locator('h1:has-text("分析报告历史")')).toBeVisible();
    await expect(page.getByPlaceholder('搜索股票代码...')).toBeVisible();
    await expect(page.locator('button:has-text("刷新数据")')).toBeVisible();
    await expect(page.locator('h3:has-text("报告列表")')).toBeVisible();
    await expect(page.locator('h3:has-text("报告详情")')).toBeVisible();
  });

  test('should display toggle button for tasks and reports', async ({ page }) => {
    // Check toggle button exists (either text works)
    const toggleButton = page.locator('button').filter({ hasText: /显示(报告|任务)/ });
    await expect(toggleButton).toBeVisible();
  });

  test('should handle search functionality', async ({ page }) => {
    const searchInput = page.getByPlaceholder('搜索股票代码...');
    await searchInput.fill('AAPL');
    await searchInput.press('Enter');

    // Wait for search to apply
    await page.waitForTimeout(500);
  });

  test('should display refresh button functionality', async ({ page }) => {
    const refreshButton = page.locator('button:has-text("刷新数据")');
    await expect(refreshButton).toBeVisible();

    // Click refresh button
    await refreshButton.click();
    await page.waitForTimeout(500);
  });
});
