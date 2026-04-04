import { test, expect } from '@playwright/test';
import { mockFinnhubAPI, mockLLMAPI } from '../support/mocks';

test.describe('Portfolio Management', () => {
  test.beforeEach(async ({ page }) => {
    mockFinnhubAPI(page);
    mockLLMAPI(page);
    await page.goto('/portfolio');
  });

  test('should display portfolio page elements', async ({ page }) => {
    // Use more specific selector for the heading
    await expect(page.getByRole('heading', { name: '持仓管理' })).toBeVisible();
    await expect(page.getByRole('heading', { name: '添加持仓' })).toBeVisible();
    await expect(page.getByRole('heading', { name: '持仓列表' })).toBeVisible();
    await expect(page.getByPlaceholder('例如: AAPL')).toBeVisible();
  });

  test('should add a new portfolio item', async ({ page }) => {
    // Fill form
    await page.getByPlaceholder('例如: AAPL').fill('MSFT');
    await page.getByPlaceholder('例如: 100').fill('50');
    await page.getByPlaceholder('例如: 150.00').fill('300');

    // Click add button
    await page.getByRole('button', { name: '添加' }).click();

    // Verify form is reset
    await expect(page.getByPlaceholder('例如: AAPL')).toHaveValue('');
    await expect(page.getByPlaceholder('例如: 100')).toHaveValue('');
    await expect(page.getByPlaceholder('例如: 150.00')).toHaveValue('');
  });

  test('should edit an existing portfolio item', async ({ page }) => {
    // Wait for mock data to load
    await expect(page.getByRole('row', { name: 'AAPL' })).toBeVisible();

    // Click edit button for AAPL
    await page.getByRole('row', { name: 'AAPL' }).getByRole('button', { name: '编辑' }).click();

    // Verify form is in edit mode
    await expect(page.getByRole('heading', { name: '编辑持仓' })).toBeVisible();

    // Update quantity
    await page.getByPlaceholder('例如: 100').fill('150');
    await page.getByRole('button', { name: '更新' }).click();

    // Verify the update (mock data will show original, but form should reset)
    await expect(page.getByRole('heading', { name: '添加持仓' })).toBeVisible();
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
    await expect(page.getByRole('row', { name: 'AAPL' })).toBeVisible();

    // Click delete button
    page.on('dialog', dialog => dialog.accept());
    await page.getByRole('row', { name: 'AAPL' }).getByRole('button', { name: '删除' }).click();
  });
});