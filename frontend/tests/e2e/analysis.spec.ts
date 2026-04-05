import { test, expect } from '@playwright/test';
import { mockFinnhubAPI, mockLLMAPI } from '../support/mocks';

test.describe('Analysis Page', () => {
  test.beforeEach(async ({ page }) => {
    mockFinnhubAPI(page);
    mockLLMAPI(page);
    await page.goto('/analysis/AAPL');
  });

  test('should display analysis options page', async ({ page }) => {
    // 验证分析选项页面是否正确显示
    await expect(page.locator('h1:has-text("AAPL 分析")')).toBeVisible();
    await expect(page.locator('h3:has-text("分析选项")')).toBeVisible();
    await expect(page.locator('div:has-text("实时分析")').first()).toBeVisible();
    await expect(page.locator('div:has-text("异步分析")').first()).toBeVisible();
  });

  test('should show both analysis buttons', async ({ page }) => {
    // 验证分析按钮是否可见
    const realTimeButton = page.locator('button', { hasText: '实时分析' });
    await expect(realTimeButton).toBeVisible();

    const asyncButton = page.locator('button', { hasText: '异步分析' });
    await expect(asyncButton).toBeVisible();
  });
});
