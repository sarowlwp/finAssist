import { test, expect } from '@playwright/test';
import { mockLLMAPI } from '../support/mocks';

test.describe('Settings Page', () => {
  test.beforeEach(async ({ page }) => {
    mockLLMAPI(page);
    await page.goto('/settings');
  });

  test('should display settings page elements', async ({ page }) => {
    // Wait for loading to finish first
    await page.waitForSelector('text=加载中...', { state: 'hidden', timeout: 10000 });

    // Check card titles using more precise locators
    await expect(page.getByRole('heading', { name: '投资风格' })).toBeVisible();
    await expect(page.getByRole('heading', { name: '通用模型配置' })).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Agent 模型配置' })).toBeVisible();
    await expect(page.getByRole('heading', { name: 'API Key 配置状态' })).toBeVisible();
  });

  test('should update investment style', async ({ page }) => {
    await page.waitForSelector('text=加载中...', { state: 'hidden', timeout: 10000 });

    // Find the investment style card specifically
    const investmentStyleCard = page.locator('div').filter({ has: page.getByRole('heading', { name: '投资风格' }) }).first();

    // Find select within this card
    const investmentStyleSelect = investmentStyleCard.locator('select').first();
    await investmentStyleSelect.selectOption({ label: '保守型' });

    // Click save button within this card
    await investmentStyleCard.getByRole('button', { name: '保存投资风格' }).click();

    // Verify success message
    await expect(page.getByText('投资风格已保存')).toBeVisible();
  });

  test('should display model configuration fields', async ({ page }) => {
    await page.waitForSelector('text=加载中...', { state: 'hidden', timeout: 10000 });

    // Find model config card
    const modelConfigCard = page.locator('div').filter({ has: page.getByRole('heading', { name: '通用模型配置' }) }).first();

    // Verify that all necessary fields are present
    await expect(modelConfigCard.locator('select').first()).toBeVisible();
    await expect(modelConfigCard.getByPlaceholder('例如: gpt-4, gpt-3.5-turbo')).toBeVisible();
    await expect(modelConfigCard.getByRole('button', { name: '保存模型配置' })).toBeVisible();
  });

  test('should display agent model configuration cards', async ({ page }) => {
    await page.waitForSelector('text=加载中...', { state: 'hidden', timeout: 10000 });
    await page.getByRole('heading', { name: 'Agent 模型配置' }).waitFor();

    // Check all agent cards are visible
    const agentNames = ['supervisor', 'fusion', 'news', 'sec', 'fundamentals', 'technical', 'custom_skill'];
    for (const agent of agentNames) {
      await expect(page.getByText(`${agent} Agent`)).toBeVisible();
    }

    // Check that each card has an edit button
    const editButtons = page.getByRole('button', { name: '编辑' });
    const editButtonsCount = await editButtons.count();
    await expect(editButtonsCount).toBeGreaterThanOrEqual(agentNames.length);
  });

  test('should display API key status section', async ({ page }) => {
    await page.waitForSelector('text=加载中...', { state: 'hidden', timeout: 10000 });
    await page.getByRole('heading', { name: 'API Key 配置状态' }).waitFor();

    // Check that API key status section is visible
    const apiKeyCard = page.locator('div').filter({ has: page.getByRole('heading', { name: 'API Key 配置状态' }) }).first();
    await expect(apiKeyCard).toBeVisible();
  });
});
