import { test, expect } from '@playwright/test';
import { mockFinnhubAPI, mockLLMAPI } from '../support/mocks';

test.describe('Analysis API', () => {
  test.beforeEach(async ({ page }) => {
    mockFinnhubAPI(page);
    mockLLMAPI(page);
  });

  test('should analyze ticker and get task status', async ({ request }) => {
    const analyzeResponse = await request.post('/api/analysis/AAPL');
    expect(analyzeResponse.ok()).toBeTruthy();
    const result = await analyzeResponse.json();
    expect(result.task_id).toBeDefined();
    expect(result.status).toBeDefined();
  });
});
