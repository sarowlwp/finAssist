import { test, expect } from '@playwright/test';
import { mockLLMAPI } from '../support/mocks';

test.describe('Portfolio API', () => {
  test.beforeEach(async ({ page }) => {
    mockLLMAPI(page);
  });

  test('should get empty portfolio', async ({ request }) => {
    const response = await request.get('/api/portfolio');
    expect(response.ok()).toBeTruthy();
    const data = await response.json();
    expect(data).toEqual([]);
  });

  test('should add and delete portfolio item', async ({ request }) => {
    const item = {
      ticker: 'AAPL',
      quantity: 100,
      cost_price: 150.0,
      note: 'Test note'
    };

    // Add
    const addResponse = await request.post('/api/portfolio', { data: item });
    expect(addResponse.ok()).toBeTruthy();
    const addedItem = await addResponse.json();
    expect(addedItem.ticker).toEqual(item.ticker);
    expect(addedItem.quantity).toEqual(item.quantity);

    // Get all and verify
    const getAllResponse = await request.get('/api/portfolio');
    const allItems = await getAllResponse.json();
    expect(allItems.length).toBeGreaterThan(0);

    // Delete
    const deleteResponse = await request.delete(`/api/portfolio/${item.ticker}`);
    expect(deleteResponse.ok()).toBeTruthy();
    expect(deleteResponse.status()).toEqual(204);
  });
});
