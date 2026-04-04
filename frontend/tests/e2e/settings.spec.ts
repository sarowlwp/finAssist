import { test, expect } from '@playwright/test';
import { mockLLMAPI } from '../support/mocks';

test.describe('Settings Page', () => {
  test.beforeEach(async ({ page }) => {
    mockLLMAPI(page);
    await page.goto('/settings');
  });

  test('should display settings page elements', async ({ page }) => {
    await expect(page.getByRole('heading', { name: '投资风格' })).toBeVisible();
    await expect(page.getByRole('heading', { name: '模型配置' })).toBeVisible();
    await expect(page.getByRole('heading', { name: 'API Key 配置状态' })).toBeVisible();
  });

  test('should update investment style', async ({ page }) => {
    // Select conservative style
    const investmentStyleSelect = page.locator('select').first();
    await investmentStyleSelect.selectOption({ label: '保守型' });
    await page.getByRole('button', { name: '保存投资风格' }).click();

    // Verify success message
    await expect(page.getByText('投资风格已保存')).toBeVisible();
  });

  test('should update model configuration', async ({ page }) => {
    // Update model configuration
    const providerSelect = page.locator('select').nth(1);
    await providerSelect.selectOption({ label: 'OpenAI' });

    const modelInput = page.getByPlaceholder('例如: gpt-4, gpt-3.5-turbo');
    await modelInput.fill('gpt-4-turbo');

    await page.getByRole('button', { name: '保存模型配置' }).click();

    // Verify success message
    await expect(page.getByText('模型配置已保存')).toBeVisible();
  });

  test('should display API key status badges', async ({ page }) => {
    // Check API key status section
    await expect(page.getByRole('heading', { name: 'API Key 配置状态' })).toBeVisible();

    // Check all provider badges are visible (using more specific selectors)
    await expect(page.locator('.bg-slate-50').filter({ hasText: 'OpenRouter' })).toBeVisible();
    await expect(page.locator('.bg-slate-50').filter({ hasText: 'OpenAI' })).toBeVisible();
    await expect(page.locator('.bg-slate-50').filter({ hasText: 'Grok' })).toBeVisible();
    await expect(page.locator('.bg-slate-50').filter({ hasText: 'Gemini' })).toBeVisible();
    await expect(page.locator('.bg-slate-50').filter({ hasText: 'DashScope' })).toBeVisible();

    // Check configured status for some providers
    await expect(page.getByText('已配置').first()).toBeVisible();
    await expect(page.getByText('未配置').first()).toBeVisible();
  });
});