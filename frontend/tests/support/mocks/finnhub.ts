import { Page } from '@playwright/test';

export function mockFinnhubAPI(page: Page) {
  // Mock Finnhub external API
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

  // Mock local portfolio API endpoints
  page.route('http://localhost:8001/api/portfolio', async (route) => {
    if (route.request().method() === 'GET') {
      await route.fulfill({
        status: 200,
        json: [
          {
            ticker: 'AAPL',
            quantity: 100,
            cost_price: 150.0,
            note: '长期持有',
            created_at: '2026-04-04T10:00:00',
            updated_at: '2026-04-04T10:00:00',
            current_price: 155.0,
            market_value: 15500.0,
            total_cost: 15000.0,
            profit_loss: 500.0,
            profit_loss_percent: 3.33,
            data_status: {
              last_updated: '2026-04-04T10:00:00',
              is_stale: false
            }
          },
          {
            ticker: 'GOOGL',
            quantity: 50,
            cost_price: 120.0,
            note: '科技股',
            created_at: '2026-04-04T10:00:00',
            updated_at: '2026-04-04T10:00:00',
            current_price: 130.0,
            market_value: 6500.0,
            total_cost: 6000.0,
            profit_loss: 500.0,
            profit_loss_percent: 8.33,
            data_status: {
              last_updated: '2026-04-04T10:00:00',
              is_stale: false
            }
          },
          {
            ticker: 'TSLA',
            quantity: 30,
            cost_price: 200.0,
            note: '新能源',
            created_at: '2026-04-04T10:00:00',
            updated_at: '2026-04-04T10:00:00',
            current_price: 210.0,
            market_value: 6300.0,
            total_cost: 6000.0,
            profit_loss: 300.0,
            profit_loss_percent: 5.0,
            data_status: {
              last_updated: '2026-04-04T10:00:00',
              is_stale: false
            }
          }
        ]
      });
    } else if (route.request().method() === 'POST') {
      await route.fulfill({
        status: 201,
        json: {
          ticker: 'MSFT',
          quantity: 50,
          cost_price: 300.0,
          note: '',
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString()
        }
      });
    } else {
      await route.continue();
    }
  });

  // Mock portfolio update endpoints
  page.route('http://localhost:8001/api/portfolio/*', async (route) => {
    const method = route.request().method();
    if (method === 'DELETE') {
      await route.fulfill({
        status: 204
      });
    } else if (method === 'PUT') {
      const requestData = await route.request().postDataJSON();
      await route.fulfill({
        status: 200,
        json: {
          ticker: 'AAPL',
          quantity: requestData.quantity || 150,
          cost_price: requestData.cost_price || 150.0,
          note: requestData.note || '长期持有',
          created_at: '2026-04-04T10:00:00',
          updated_at: new Date().toISOString()
        }
      });
    } else {
      await route.continue();
    }
  });

  // Mock portfolio fundamentals endpoints
  page.route('http://localhost:8001/api/portfolio/*/fundamentals', async (route) => {
    const pathParts = route.request().url().split('/');
    const ticker = pathParts[pathParts.length - 2];

    if (route.request().method() === 'GET' || route.request().method() === 'POST') {
      await route.fulfill({
        status: 200,
        json: {
          success: true,
          ticker: ticker,
          company_profile: {
            success: true,
            ticker: ticker,
            company_name: `${ticker} Inc.`,
            country: 'US',
            currency: 'USD',
            exchange: 'NASDAQ',
            industry: 'Technology',
            market_cap: 2000000000000,
            description: `${ticker} is a technology company.`,
            website: `https://${ticker.toLowerCase()}.com`,
            logo: `https://example.com/${ticker.toLowerCase()}.png`,
            timestamp: new Date().toISOString()
          },
          financials: {
            success: true,
            ticker: ticker,
            pe_ratio: 25.5,
            pb_ratio: 4.2,
            ps_ratio: 6.8,
            roe: 0.15,
            roa: 0.10,
            profit_margin: 0.20,
            dividend_yield: 0.02,
            debt_to_equity: 0.5,
            current_ratio: 1.5,
            quick_ratio: 1.2,
            revenue_growth: 0.10,
            earnings_growth: 0.12,
            timestamp: new Date().toISOString()
          },
          technical_indicators: {
            success: true,
            ticker: ticker,
            current_price: 150.0,
            rsi: 55.0,
            macd: {
              macd: 0.5,
              signal: 0.3,
              histogram: 0.2
            },
            bollinger_bands: {
              upper: 160.0,
              middle: 150.0,
              lower: 140.0
            },
            rsi_signal: 'neutral',
            timestamp: new Date().toISOString()
          }
        }
      });
    } else {
      await route.continue();
    }
  });

  // Mock local market API endpoints
  page.route('http://localhost:8001/api/market/quote/*', async (route) => {
    await route.fulfill({
      status: 200,
      json: {
        price: 150.00,
        change_percent: 0.67
      }
    });
  });

  page.route('http://localhost:8001/api/market/profile/*', async (route) => {
    await route.fulfill({
      status: 200,
      json: {
        company_name: 'Apple Inc.'
      }
    });
  });
}
