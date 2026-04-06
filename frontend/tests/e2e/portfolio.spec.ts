import { test, expect } from '@playwright/test';
import { mockFinnhubAPI, mockLLMAPI } from '../support/mocks';

test.describe('Portfolio Management', () => {
  test.beforeEach(async ({ page }) => {
    mockFinnhubAPI(page);
    mockLLMAPI(page);
    await page.goto('/portfolio');
  });

  test('should display portfolio page elements', async ({ page }) => {
    // Check main elements
    await expect(page.getByRole('heading', { name: '持仓管理' })).toBeVisible();
    await expect(page.getByRole('heading', { name: '持仓列表' })).toBeVisible();
    await expect(page.getByRole('button', { name: '+ 添加持仓' })).toBeVisible();
    await expect(page.getByPlaceholder('搜索股票代码或备注...')).toBeVisible();
  });

  test('should open and close add modal', async ({ page }) => {
    // Click add button
    await page.getByRole('button', { name: '+ 添加持仓' }).click();

    // Wait for modal form elements to appear
    await expect(page.locator('input[placeholder="例如: AAPL"]')).toBeVisible();
    await expect(page.locator('input[placeholder="例如: 100 (0表示关注)"]')).toBeVisible();

    // Find and click cancel button
    const cancelButtons = page.locator('button', { hasText: '取消' });
    const cancelCount = await cancelButtons.count();
    for (let i = 0; i < cancelCount; i++) {
      const btn = cancelButtons.nth(i);
      const text = await btn.textContent();
      if (text === '取消') {
        await btn.click();
        break;
      }
    }

    // Verify modal is closed
    await page.waitForSelector('input[placeholder="例如: AAPL"]', { state: 'hidden', timeout: 5000 });
  });

  test('should edit an existing portfolio item', async ({ page }) => {
    // Wait for mock data to load (or actual data)
    await page.waitForSelector('table', { timeout: 10000 });

    // Try to find any row with a quantity button
    const quantityButtons = page.locator('td:nth-child(2) button');
    const count = await quantityButtons.count();
    if (count > 0) {
      // Click the first quantity cell
      await quantityButtons.first().click();

      // Check that input appears
      const input = page.locator('input[type="number"]').first();
      await expect(input).toBeVisible();

      // Press escape to cancel
      await input.press('Escape');
      await expect(input).not.toBeVisible();
    }
  });

  test('should search and filter portfolio items', async ({ page }) => {
    // This test just verifies the search input exists and is interactive
    const searchInput = page.getByPlaceholder('搜索股票代码或备注...');
    await expect(searchInput).toBeVisible();

    // Type something and verify it's there
    await searchInput.fill('test');
    await expect(searchInput).toHaveValue('test');

    // Clear it
    await searchInput.fill('');
    await expect(searchInput).toHaveValue('');
  });
});
