import { test, expect } from '@playwright/test';
import { mockFinnhubAPI, mockLLMAPI } from '../support/mocks';

test.describe('Analysis Page', () => {
  test.beforeEach(async ({ page }) => {
    mockFinnhubAPI(page);
    mockLLMAPI(page);
    await page.goto('/analysis/AAPL');
  });

  test('should display analysis page elements', async ({ page }) => {
    await expect(page.getByRole('heading', { name: 'AAPL 分析报告' })).toBeVisible();
    await expect(page.getByText('当前价格')).toBeVisible();
    await expect(page.getByText('涨跌幅')).toBeVisible();
  });

  test('should show agent reports and fusion summary', async ({ page }) => {
    await expect(page.getByRole('heading', { name: 'Fusion Agent 融合总结' })).toBeVisible();
    await expect(page.getByRole('heading', { name: 'News Agent 报告' })).toBeVisible();
    await expect(page.getByRole('heading', { name: 'SEC Agent 报告' })).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Fundamentals Agent 报告' })).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Technical Agent 报告' })).toBeVisible();
  });

  test('should display current price and change percentage', async ({ page }) => {
    // Check price display
    const priceElement = page.getByText(/\$\d+\.\d{2}/);
    await expect(priceElement).toBeVisible();

    // Check change percentage with proper sign
    const changeElement = page.getByText(/[+-]?\d+\.\d{2}%/);
    await expect(changeElement).toBeVisible();
  });

  test('should handle reanalysis functionality', async ({ page }) => {
    // Click reanalyze button
    await page.getByRole('button', { name: '重新分析' }).click();

    // Wait for analysis to start
    await expect(page.getByText('分析中...')).toBeVisible();

    // Wait for cancel button to appear
    await expect(page.getByRole('button', { name: '取消' })).toBeVisible();

    // Click cancel button
    await page.getByRole('button', { name: '取消' }).click();
  });

  test('should toggle agent report cards', async ({ page }) => {
    // Click on News Agent report card to collapse/expand
    await page.getByRole('heading', { name: 'News Agent 报告' }).first().click();

    // Verify content is still accessible
    await expect(page.getByText('News Agent 报告')).toBeVisible();
  });
});