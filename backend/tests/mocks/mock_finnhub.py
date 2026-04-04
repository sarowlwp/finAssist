class MockFinnhubService:
    """Mock Finnhub service for testing"""

    def __init__(self, api_key=None):
        pass

    def get_quote(self, ticker: str):
        """Mock get quote"""
        return {
            "success": True,
            "current_price": 150.0,  # Current price
            "high": 155.0,  # High
            "low": 145.0,  # Low
            "open": 148.0,  # Open
            "previous_close": 149.0  # Previous close
        }

    def get_company_profile(self, ticker: str):
        """Mock company profile"""
        return {
            "success": True,
            "name": "Apple Inc.",
            "country": "US",
            "ipo": "1980-12-12",
            "logo": "https://example.com/aapl-logo.png",
            "marketCapitalization": 2000000000000,
            "ticker": "AAPL"
        }

    def get_news(self, ticker: str):
        """Mock news"""
        return {
            "success": True,
            "data": [
                {
                    "category": "company",
                    "datetime": 1712246400,
                    "headline": "Apple Reports Q1 2026 Earnings",
                    "id": 12345,
                    "image": "https://example.com/news1.jpg",
                    "related": "AAPL",
                    "source": "Bloomberg",
                    "summary": "Apple Inc. announced record quarterly earnings...",
                    "url": "https://example.com/news1"
                }
            ]
        }

    def get_financials(self, ticker: str):
        """Mock financials"""
        return {
            "success": True,
            "data": {
                "totalRevenue": 394328000000,
                "netIncome": 96995000000,
                "grossProfit": 170782000000,
                "totalAssets": 455183000000
            }
        }
