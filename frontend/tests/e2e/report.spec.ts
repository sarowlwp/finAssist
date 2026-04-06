import { test, expect } from '@playwright/test';
import { mockFinnhubAPI, mockLLMAPI } from '../support/mocks';

test.describe('Report Detail Page', () => {
  test.beforeEach(async ({ page }) => {
    mockFinnhubAPI(page);
    mockLLMAPI(page);
    // 先导航到历史页面，然后点击一个报告
    await page.goto('/history');
  });

  test('should have basic page structure', async ({ page }) => {
    // 这个测试只是确保页面能正常加载
    await expect(page.locator('h1:has-text("分析报告历史")')).toBeVisible();
  });
});
