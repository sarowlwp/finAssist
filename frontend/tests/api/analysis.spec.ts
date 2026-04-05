import { test, expect } from '@playwright/test';
import { mockFinnhubAPI, mockLLMAPI } from '../support/mocks';

test.describe('Analysis API', () => {
  test.beforeEach(async ({ page }) => {
    mockFinnhubAPI(page);
    mockLLMAPI(page);
  });

  test('should start async analysis and get task status', async ({ request }) => {
    // 启动异步分析任务
    const analyzeResponse = await request.post('/api/analysis/ticker/start', {
      data: { ticker: 'AAPL' }
    });
    expect(analyzeResponse.ok()).toBeTruthy();
    const result = await analyzeResponse.json();
    expect(result.success).toBeTruthy();
    expect(result.task_id).toBeDefined();
    expect(result.ticker).toBe('AAPL');

    // 获取任务列表
    const tasksResponse = await request.get('/api/analysis/tasks');
    expect(tasksResponse.ok()).toBeTruthy();
    const tasks = await tasksResponse.json();
    expect(Array.isArray(tasks)).toBeTruthy();
    expect(tasks.length).toBeGreaterThan(0);
  });
});
