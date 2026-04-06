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

  test('should add a new portfolio item', async ({ page }) => {
    // Click add button
    await page.getByRole('button', { name: '+ 添加持仓' }).click();

    // Wait for modal to open by checking for the title
    await expect(page.locator('text=添加持仓').first()).toBeVisible();

    // Fill form - use CSS selectors that are more reliable in modal
    await page.locator('input[placeholder="例如: AAPL"]').fill('MSFT');
    await page.locator('input[placeholder="例如: 100 (0表示关注)"]').fill('50');
    await page.locator('input[placeholder="例如: 150.00"]').fill('300');

    // Click add button using more direct selector - find all "添加" buttons and pick the one not on the main page
    const addButtons = page.locator('button', { hasText: '添加' });
    const count = await addButtons.count();
    for (let i = 0; i < count; i++) {
      const btn = addButtons.nth(i);
      const text = await btn.textContent();
      if (text === '添加') {
        await btn.click();
        break;
      }
    }

    // Verify modal is closed
    await page.waitForSelector('text=添加持仓', { state: 'hidden' });
  });

  test('should edit an existing portfolio item', async ({ page }) => {
    // Wait for mock data to load
    await expect(page.getByText('AAPL')).toBeVisible();

    // Find and edit quantity of AAPL
    const aaplRow = page.locator('tr').filter({ hasText: 'AAPL' });
    const quantityCell = aaplRow.locator('td').nth(1).locator('button');
    await quantityCell.click();

    // Enter new quantity
    const input = page.locator('input[type="number"]');
    await input.fill('150');
    await input.press('Enter');

    // Wait for edit to complete
    await expect(input).not.toBeVisible();
  });

  test('should search and filter portfolio items', async ({ page }) => {
    // Wait for mock data to load
    await expect(page.getByText('AAPL')).toBeVisible();
    await expect(page.getByText('GOOGL')).toBeVisible();

    // Search for AAPL
    await page.getByPlaceholder('搜索股票代码或备注...').fill('AAPL');
    await expect(page.getByText('AAPL')).toBeVisible();
    await expect(page.getByText('GOOGL')).not.toBeVisible();
  });

  test('should delete a portfolio item', async ({ page }) => {
    // First add a test item so we can delete it
    await page.getByRole('button', { name: '+ 添加持仓' }).click();
    await page.waitForSelector('input[placeholder="例如: AAPL"]');
    await page.locator('input[placeholder="例如: AAPL"]').fill('TEST');
    await page.locator('input[placeholder="例如: 100 (0表示关注)"]').fill('10');
    await page.locator('input[placeholder="例如: 150.00"]').fill('100');
    await page.locator('button:has-text("添加")').filter({ hasNotText: '+ 添加' }).click();
    await page.waitForSelector('[role="dialog"]', { state: 'hidden' });

    // Wait for item to be added
    await expect(page.getByText('TEST')).toBeVisible();

    // Click delete button
    const testRow = page.locator('tr').filter({ hasText: 'TEST' });
    page.on('dialog', dialog => dialog.accept());
    await testRow.getByRole('button', { name: '删除' }).click();

    // Verify item is removed from table
    await expect(page.getByText('TEST')).not.toBeVisible();
  });

  test('should display zero quantity items with special style', async ({ page }) => {
    // First add a zero quantity item to test with
    await page.getByRole('button', { name: '+ 添加持仓' }).click();

    // Wait for modal to open and fill form
    await page.waitForSelector('input[placeholder="例如: AAPL"]');
    await page.locator('input[placeholder="例如: AAPL"]').fill('ZERO');
    await page.locator('input[placeholder="例如: 100 (0表示关注)"]').fill('0');
    await page.locator('input[placeholder="例如: 150.00"]').fill('50');
    await page.locator('button:has-text("添加")').filter({ hasNotText: '+ 添加' }).click();
    await page.waitForSelector('[role="dialog"]', { state: 'hidden' });

    // Wait for item to be added and check for "关注" badge
    await expect(page.getByText('ZERO')).toBeVisible();

    // Check the "关注" badge style
    const zeroRow = page.locator('tr').filter({ hasText: 'ZERO' });
    await expect(zeroRow.getByText('关注')).toBeVisible();

    // Clean up
    page.on('dialog', dialog => dialog.accept());
    await zeroRow.getByRole('button', { name: '删除' }).click();
  });
});
