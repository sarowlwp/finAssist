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

    // Use more reliable selectors for headings in cards
    await expect(page.getByText('投资风格')).toBeVisible();
    await expect(page.getByText('通用模型配置')).toBeVisible();
    await expect(page.getByText('Agent 模型配置')).toBeVisible();
    await expect(page.getByText('API Key 配置状态')).toBeVisible();
  });

  test('should update investment style', async ({ page }) => {
    await page.waitForSelector('text=加载中...', { state: 'hidden', timeout: 10000 });

    // Select conservative style
    await page.getByText('投资风格').waitFor();

    const investmentStyleSelect = page.locator('select').first();
    await investmentStyleSelect.selectOption({ label: '保守型' });
    await page.getByText('保存投资风格').click();

    // Verify success message
    await expect(page.getByText('投资风格已保存')).toBeVisible();
  });

  test('should update model configuration', async ({ page }) => {
    await page.waitForSelector('text=加载中...', { state: 'hidden', timeout: 10000 });
    await page.getByText('通用模型配置').waitFor();

    // Update model configuration
    const providerSelect = page.locator('select').nth(1);
    await providerSelect.selectOption({ label: 'OpenAI' });

    const modelInput = page.getByPlaceholder('例如: gpt-4, gpt-3.5-turbo');
    await modelInput.fill('gpt-4-turbo');

    await page.getByText('保存模型配置').click();

    // Verify success message
    await expect(page.getByText('模型配置已保存')).toBeVisible();
  });

  test('should display and edit agent model configurations', async ({ page }) => {
    await page.waitForSelector('text=加载中...', { state: 'hidden', timeout: 10000 });
    await page.getByText('Agent 模型配置').waitFor();

    // Check all agent cards are visible
    const agentNames = ['supervisor', 'fusion', 'news', 'sec', 'fundamentals', 'technical', 'custom_skill'];
    for (const agent of agentNames) {
      await expect(page.getByText(`${agent} Agent`)).toBeVisible();
    }

    // Test editing supervisor agent configuration
    const supervisorCard = page.locator('div').filter({ hasText: 'supervisor Agent' }).first();
    await supervisorCard.getByText('编辑').click();

    // Check edit mode UI
    await expect(supervisorCard.getByText('保存')).toBeVisible();
    await expect(supervisorCard.getByText('取消')).toBeVisible();

    // Update configuration
    const agentProviderSelect = supervisorCard.locator('select');
    await agentProviderSelect.selectOption({ label: 'OpenAI' });

    const agentModelInput = supervisorCard.getByPlaceholder('模型名称');
    await agentModelInput.fill('gpt-4o');

    // Save configuration
    await supervisorCard.getByText('保存').click();

    // Verify success message
    await expect(page.getByText('supervisor Agent 配置已保存')).toBeVisible();
  });

  test('should display API key status badges', async ({ page }) => {
    await page.waitForSelector('text=加载中...', { state: 'hidden', timeout: 10000 });
    await page.getByText('API Key 配置状态').waitFor();

    // Check all provider badges are visible
    await expect(page.getByText('OpenRouter')).toBeVisible();
    await expect(page.getByText('OpenAI')).toBeVisible();
    await expect(page.getByText('Grok')).toBeVisible();
    await expect(page.getByText('Gemini')).toBeVisible();
    await expect(page.getByText('DashScope')).toBeVisible();

    // Check configured status for some providers
    await expect(page.getByText('已配置')).toBeVisible();
    await expect(page.getByText('未配置')).toBeVisible();
  });
});
