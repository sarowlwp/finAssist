import { Page } from '@playwright/test';

export function mockFinnhubAPI(page: Page) {
  page.route('https://finnhub.io/api/v1/*', async (route) => {
    const url = route.request().url();

    if (url.includes('quote')) {
      await route.fulfill({
        status: 200,
        json: {
          c: 150.0,
          h: 155.0,
          l: 145.0,
          o: 148.0,
          pc: 149.0
        }
      });
    } else if (url.includes('company-profile')) {
      await route.fulfill({
        status: 200,
        json: {
          name: 'Apple Inc.',
          country: 'US',
          ipo: '1980-12-12',
          logo: 'https://example.com/aapl-logo.png',
          marketCapitalization: 2000000000000,
          ticker: 'AAPL'
        }
      });
    } else if (url.includes('news')) {
      await route.fulfill({
        status: 200,
        json: [
          {
            category: 'company',
            datetime: 1712246400,
            headline: 'Apple Reports Q1 2026 Earnings',
            id: 12345,
            image: 'https://example.com/news1.jpg',
            related: 'AAPL',
            source: 'Bloomberg',
            summary: 'Apple Inc. announced record quarterly earnings...',
            url: 'https://example.com/news1'
          }
        ]
      });
    } else {
      await route.fulfill({
        status: 404,
        json: { error: 'Not found' }
      });
    }
  });
}
