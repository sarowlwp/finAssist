import { test as base } from '@playwright/test';

export type TestFixtures = {
  testUser: string;
  samplePortfolioItem: {
    ticker: string;
    quantity: number;
    costPrice: number;
    note?: string;
  };
};

export const test = base.extend<TestFixtures>({
  testUser: 'test-user',
  samplePortfolioItem: {
    ticker: 'AAPL',
    quantity: 100,
    costPrice: 150,
    note: 'Test position',
  },
});

export { expect } from '@playwright/test';
