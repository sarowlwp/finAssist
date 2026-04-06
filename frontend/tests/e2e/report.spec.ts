import { test, expect } from '@playwright/test';
import { mockFinnhubAPI, mockLLMAPI } from '../support/mocks';

test.describe('Report Detail Page', () => {
  test.beforeEach(async ({ page }) => {
    mockFinnhubAPI(page);
    mockLLMAPI(page);
    // 先导航到历史页面，然后点击一个报告
    await page.goto('/history');
  });

  test('should navigate to report detail page and show basic structure', async ({ page }) => {
    // 点击第一个报告
    const reportCards = page.locator('[role="article"]');
    if (await reportCards.count() > 0) {
      await reportCards.first().click();

      // 等待 URL 变更
      await page.waitForURL('**/report/*');

      // 检查基本页面结构
      await expect(page.locator('h1:has-text("分析报告详情")')).toBeVisible();
      await expect(page.locator('button:has-text("返回历史列表")')).toBeVisible();
    }
  });

  test('should display Fusion Agent summary at top', async ({ page }) => {
    // 点击第一个报告
    const reportCards = page.locator('[role="article"]');
    if (await reportCards.count() > 0) {
      await reportCards.first().click();

      // 等待 URL 变更
      await page.waitForURL('**/report/*');

      // 检查 Fusion Agent 摘要是否在顶部
      await expect(page.locator('h3:has-text("Fusion Agent 融合总结")')).toBeVisible();
    }
  });

  test('should display all agent reports in tabs', async ({ page }) => {
    // 点击第一个报告
    const reportCards = page.locator('[role="article"]');
    if (await reportCards.count() > 0) {
      await reportCards.first().click();

      // 等待 URL 变更
      await page.waitForURL('**/report/*');

      // 检查是否有 tabs
      const tabs = page.locator('button:has-text("📰 News Agent"), button:has-text("📋 SEC Agent"), button:has-text("📊 Fundamentals Agent"), button:has-text("📈 Technical Agent"), button:has-text("🔧 Custom Skill Agent")');

      // 等待 tabs 加载
      await page.waitForTimeout(1000);

      // 检查 tabs 数量
      const visibleTabs = await tabs.filter({ visible: true }).count();
      expect(visibleTabs).toBeGreaterThanOrEqual(5);
    }
  });

  test('should allow switching between agent reports', async ({ page }) => {
    // 点击第一个报告
    const reportCards = page.locator('[role="article"]');
    if (await reportCards.count() > 0) {
      await reportCards.first().click();

      // 等待 URL 变更
      await page.waitForURL('**/report/*');

      // 点击第一个 tab
      const newsTab = page.locator('button:has-text("📰 News Agent")');
      if (await newsTab.isVisible()) {
        await newsTab.click();

        // 等待内容加载
        await page.waitForTimeout(500);

        // 检查是否有内容
        const content = page.locator('.prose');
        await expect(content).toBeVisible();
      }
    }
  });
});
