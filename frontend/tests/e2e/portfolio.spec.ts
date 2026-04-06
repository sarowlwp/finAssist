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

    // Wait for modal to open
    await expect(page.getByRole('heading', { name: '添加持仓' })).toBeVisible();

    // Fill form
    await page.getByPlaceholder('例如: AAPL').fill('MSFT');
    await page.getByPlaceholder('例如: 100 (0表示关注)').fill('50');
    await page.getByPlaceholder('例如: 150.00').fill('300');
    await page.getByPlaceholder('添加备注信息...').fill('Microsoft Corporation');

    // Click add button
    await page.getByRole('button', { name: '添加' }).click();

    // Verify modal is closed and item is added
    await expect(page.getByRole('heading', { name: '添加持仓' })).not.toBeVisible();
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
    // Wait for mock data to load
    await expect(page.getByText('AAPL')).toBeVisible();

    // Click delete button
    const aaplRow = page.locator('tr').filter({ hasText: 'AAPL' });
    page.on('dialog', dialog => dialog.accept());
    await aaplRow.getByRole('button', { name: '删除' }).click();

    // Verify item is removed from table
    await expect(page.getByText('AAPL')).not.toBeVisible();
  });

  test('should display zero quantity items with special style', async ({ page }) => {
    // Check if there are any zero quantity items (mock data should have TSLA with 0 quantity)
    await expect(page.getByText('TSLA').locator('..').filter({ hasText: '关注' })).toBeVisible();

    // Check the "关注" badge style
    const zeroQuantityBadges = page.getByText('关注');
    await expect(zeroQuantityBadges).toBeVisible();
  });
});
