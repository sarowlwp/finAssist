import { test, expect } from '@playwright/test';
import { mockLLMAPI } from '../support/mocks';

test.describe('Agents Page', () => {
  test.beforeEach(async ({ page }) => {
    mockLLMAPI(page);
    await page.goto('/agents');
  });

  test('should display agents list and chat interface', async ({ page }) => {
    await expect(page.getByRole('heading', { name: 'Agent 调试' })).toBeVisible();
    await expect(page.getByPlaceholder('输入消息...')).toBeVisible();
    await expect(page.getByRole('button', { name: '发送' })).toBeVisible();
  });

  test('should send message to supervisor agent', async ({ page }) => {
    // Wait for initial agents to load
    await expect(page.getByRole('heading', { name: 'supervisor 聊天' })).toBeVisible();

    // Send a message
    await page.getByPlaceholder('输入消息...').fill('分析一下苹果公司的股票');
    await page.getByRole('button', { name: '发送' }).click();

    // Verify mock response
    await expect(page.getByText('This is a mock response from the supervisor agent')).toBeVisible();
  });

  test('should manage skills with manual and GitHub installation', async ({ page }) => {
    // Check manual creation form
    await expect(page.getByText('✏️ 手动创建')).toBeVisible();
    await expect(page.getByText('🔗 从 GitHub 安装')).toBeVisible();

    // Verify manual creation form inputs
    await expect(page.getByPlaceholder('技能名称（必填）')).toBeVisible();
    await expect(page.getByPlaceholder('技能描述（必填）')).toBeVisible();
    await expect(page.getByPlaceholder('提示词注入')).toBeVisible();

    // Verify GitHub installation form
    await page.getByText('🔗 从 GitHub 安装').click();
    await expect(page.getByPlaceholder('GitHub 仓库链接')).toBeVisible();
  });

  test('should save agent model configuration', async ({ page }) => {
    // Change provider and model
    const providerSelect = page.locator('select').first();
    await providerSelect.selectOption({ label: 'OpenAI' });

    const modelInput = page.getByPlaceholder('gpt-4');
    await modelInput.fill('gpt-3.5-turbo');

    // Save configuration
    await page.getByRole('button', { name: '保存配置' }).click();
  });

  test('should handle custom agents management', async ({ page }) => {
    // Check new agent button
    await expect(page.getByRole('button', { name: '+ 新增 Agent' })).toBeVisible();

    // Open create agent modal
    await page.getByRole('button', { name: '+ 新增 Agent' }).click();
    await expect(page.getByText('创建自定义 Agent')).toBeVisible();

    // Fill in form (but don't submit)
    await page.getByPlaceholder('英文标识，如 esg、sentiment').fill('test_agent');
    await page.getByPlaceholder('如 ESG Agent、情绪分析 Agent').fill('测试 Agent');
    await page.getByPlaceholder('定义 Agent 的角色、能力和输出格式').fill('这是一个测试 Agent');

    // Close modal
    await page.getByRole('button', { name: '取消' }).click();
  });
});