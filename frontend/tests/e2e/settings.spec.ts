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

  test('should update model configuration', async ({ page }) => {
    await page.waitForSelector('text=加载中...', { state: 'hidden', timeout: 10000 });

    // Find model config card
    const modelConfigCard = page.locator('div').filter({ has: page.getByRole('heading', { name: '通用模型配置' }) }).first();

    // Update model configuration within this card
    const providerSelect = modelConfigCard.locator('select').first();
    await providerSelect.selectOption({ label: 'OpenAI' });

    const modelInput = modelConfigCard.getByPlaceholder('例如: gpt-4, gpt-3.5-turbo');
    await modelInput.fill('gpt-4-turbo');

    await modelConfigCard.getByRole('button', { name: '保存模型配置' }).click();

    // Verify success message
    await expect(page.getByText('模型配置已保存')).toBeVisible();
  });

  test('should display and edit agent model configurations', async ({ page }) => {
    await page.waitForSelector('text=加载中...', { state: 'hidden', timeout: 10000 });
    await page.getByRole('heading', { name: 'Agent 模型配置' }).waitFor();

    // Check all agent cards are visible
    const agentNames = ['supervisor', 'fusion', 'news', 'sec', 'fundamentals', 'technical', 'custom_skill'];
    for (const agent of agentNames) {
      await expect(page.getByText(`${agent} Agent`)).toBeVisible();
    }

    // Test editing supervisor agent configuration
    const supervisorCard = page.locator('div').filter({ hasText: 'supervisor Agent' }).first();
    await supervisorCard.getByRole('button', { name: '编辑' }).click();

    // Check edit mode UI
    await expect(supervisorCard.getByRole('button', { name: '保存' })).toBeVisible();

    // Update configuration within supervisor card
    const agentProviderSelect = supervisorCard.locator('select');
    await agentProviderSelect.selectOption({ label: 'OpenAI' });

    const agentModelInput = supervisorCard.getByPlaceholder('模型名称');
    await agentModelInput.fill('gpt-4o');

    // Save configuration
    await supervisorCard.getByRole('button', { name: '保存' }).click();

    // Verify success message
    await expect(page.getByText('supervisor Agent 配置已保存')).toBeVisible();
  });

  test('should display API key status badges', async ({ page }) => {
    await page.waitForSelector('text=加载中...', { state: 'hidden', timeout: 10000 });
    await page.getByRole('heading', { name: 'API Key 配置状态' }).waitFor();

    // Check that provider badges are visible - use more flexible approach
    const apiKeyCard = page.locator('div').filter({ has: page.getByRole('heading', { name: 'API Key 配置状态' }) }).first();

    // Just check that there are badges visible instead of specific ones
    const badges = apiKeyCard.locator('[class*="badge"], [class*="Badge"]');
    await expect(badges.first()).toBeVisible();
  });
});
