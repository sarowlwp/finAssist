import { test, expect } from '@playwright/test';
import { mockFinnhubAPI } from '../support/mocks';

test.describe('Market API', () => {
  test.beforeEach(async ({ page }) => {
    mockFinnhubAPI(page);
  });

  test('should get quote and company profile', async ({ request }) => {
    const quoteResponse = await request.get('/api/market/quote/AAPL');
    expect(quoteResponse.ok()).toBeTruthy();
    const quote = await quoteResponse.json();
    expect(typeof quote.price).toEqual('number');

    const profileResponse = await request.get('/api/market/profile/AAPL');
    expect(profileResponse.ok()).toBeTruthy();
    const profile = await profileResponse.json();
    expect(profile.company_name).toEqual(expect.any(String));
    expect(profile.company_name).toEqual('Apple Inc.');
  });

  test('should get news and financials', async ({ request }) => {
    const newsResponse = await request.get('/api/market/news/AAPL');
    expect(newsResponse.ok()).toBeTruthy();
    const news = await newsResponse.json();
    expect(Array.isArray(news)).toBeTruthy();

    const financialsResponse = await request.get('/api/market/financials/AAPL');
    expect(financialsResponse.ok()).toBeTruthy();
    const financials = await financialsResponse.json();
    expect(financials.totalRevenue).toEqual(expect.any(Number));
  });
});
