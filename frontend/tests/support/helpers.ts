export function generateRandomTicker() {
  const tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA'];
  return tickers[Math.floor(Math.random() * tickers.length)];
}

export function formatCurrency(value: number) {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
  }).format(value);
}

export function waitForApiResponse(page: any, urlPattern: string) {
  return page.waitForResponse((response: any) =>
    response.url().includes(urlPattern) && response.status() === 200
  );
}
