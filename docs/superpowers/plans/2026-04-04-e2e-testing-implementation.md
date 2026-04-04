# E2E Testing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement comprehensive end-to-end testing for the finAssist investment AI assistant, including backend API tests and frontend E2E tests.

**Architecture:**
- Backend: pytest + httpx for unit/integration tests with mocking
- Frontend: Playwright (TypeScript) for E2E and API tests
- Mocks: Custom mock classes for external APIs (Finnhub, LLM providers)
- Test Data: Static test data stored in JSON files

**Tech Stack:**
- Backend: Python 3.10+, pytest, httpx
- Frontend: Playwright, TypeScript, Next.js 14
- Mocking: Monkeypatch (backend), route mocking (Playwright)

---

## Task 1: Set Up Backend Testing Infrastructure

**Files:**
- Create: `backend/tests/conftest.py`
- Create: `backend/tests/unit/__init__.py`
- Create: `backend/tests/integration/__init__.py`
- Create: `backend/tests/mocks/__init__.py`
- Modify: `backend/requirements.txt`

- [ ] **Step 1: Install pytest and dependencies**

```bash
cd backend
pip install pytest pytest-asyncio httpx pytest-cov python-dotenv
```

- [ ] **Step 2: Update requirements.txt**

Add to requirements.txt:
```
pytest
pytest-asyncio
httpx
pytest-cov
```

- [ ] **Step 3: Write pytest configuration (conftest.py)**

```python
import pytest
import httpx
from fastapi.testclient import TestClient
from pathlib import Path
import tempfile

from main import app
from config import config


@pytest.fixture(scope="function")
def test_app():
    """Create a test client with temporary data directory"""
    with tempfile.TemporaryDirectory() as temp_dir:
        config.DATA_DIR = Path(temp_dir)
        with TestClient(app) as test_client:
            yield test_client


@pytest.fixture
def sample_portfolio_item():
    """Sample portfolio item for testing"""
    return {
        "ticker": "AAPL",
        "quantity": 100,
        "avg_price": 150.0,
        "purchase_date": "2026-04-04"
    }


@pytest.fixture
def sample_model_config():
    """Sample model configuration"""
    return {
        "provider": "openrouter",
        "api_key": "test-api-key",
        "model": "anthropic/claude-3.5-sonnet",
        "base_url": "https://openrouter.ai/api/v1"
    }
```

- [ ] **Step 4: Commit the changes**

```bash
cd backend
git add requirements.txt tests/conftest.py tests/unit/__init__.py tests/integration/__init__.py tests/mocks/__init__.py
git commit -m "test: add pytest infrastructure"
```

---

## Task 2: Write Backend Storage Tests

**Files:**
- Create: `backend/tests/unit/test_storage.py`
- Modify: `backend/storage/portfolio.py`
- Modify: `backend/storage/settings.py`

- [ ] **Step 1: Write failing test for portfolio storage**

```python
from storage.portfolio import PortfolioStore
from pathlib import Path


def test_portfolio_store_crud():
    """Test portfolio store CRUD operations"""
    temp_dir = Path("/tmp/test_finassist")
    temp_dir.mkdir(exist_ok=True)
    
    # Create store
    store = PortfolioStore(temp_dir)
    
    # Test initial state
    assert len(store.get_portfolio()) == 0
    
    # Test add position
    position = {
        "ticker": "AAPL",
        "quantity": 100,
        "avg_price": 150.0,
        "purchase_date": "2026-04-04"
    }
    store.add_position(position)
    assert len(store.get_portfolio()) == 1
    
    # Test get position
    portfolio = store.get_portfolio()
    assert portfolio[0]["ticker"] == "AAPL"
    assert portfolio[0]["quantity"] == 100
    
    # Test update position
    store.update_position("AAPL", {"quantity": 150})
    updated = next(p for p in store.get_portfolio() if p["ticker"] == "AAPL")
    assert updated["quantity"] == 150
    
    # Test delete position
    store.delete_position("AAPL")
    assert len(store.get_portfolio()) == 0
```

- [ ] **Step 2: Verify test fails**

```bash
cd backend
pytest tests/unit/test_storage.py::test_portfolio_store_crud -v
```

Expected: FAIL (if storage methods not implemented yet)

- [ ] **Step 3: Write tests for settings storage**

Add to test_storage.py:
```python
from storage.settings import SettingsStore


def test_settings_store():
    """Test settings store"""
    temp_dir = Path("/tmp/test_finassist")
    temp_dir.mkdir(exist_ok=True)
    
    store = SettingsStore(temp_dir)
    
    # Test initial state
    assert store.get_settings() == {}
    
    # Test update settings
    config = {
        "provider": "openrouter",
        "api_key": "test-key"
    }
    store.update_settings("model_config", config)
    
    assert store.get_settings()["model_config"] == config
    
    # Test reset to defaults
    store.update_settings("model_config", {})
    assert "model_config" not in store.get_settings()
```

- [ ] **Step 4: Run storage tests**

```bash
cd backend
pytest tests/unit/test_storage.py -v
```

Expected: PASS

- [ ] **Step 5: Commit the changes**

```bash
cd backend
git add tests/unit/test_storage.py
git commit -m "test: add storage layer tests"
```

---

## Task 3: Write Backend API Tests

**Files:**
- Create: `backend/tests/integration/test_api_portfolio.py`
- Create: `backend/tests/integration/test_api_settings.py`
- Create: `backend/tests/integration/test_api_health.py`
- Create: `backend/tests/mocks/mock_finnhub.py`
- Create: `backend/tests/mocks/mock_llm.py`

- [ ] **Step 1: Write health endpoint tests**

```python
def test_health_endpoint(test_app):
    """Test health check endpoint"""
    response = test_app.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_root_endpoint(test_app):
    """Test root endpoint"""
    response = test_app.get("/")
    assert response.status_code == 200
    assert "message" in response.json()
    assert response.json()["version"] == "0.1.0"
```

- [ ] **Step 2: Write portfolio API tests**

```python
def test_portfolio_crud(test_app, sample_portfolio_item):
    """Test portfolio CRUD operations"""
    # Test get empty portfolio
    response = test_app.get("/api/portfolio")
    assert response.status_code == 200
    assert len(response.json()) == 0
    
    # Test add position
    response = test_app.post("/api/portfolio", json=sample_portfolio_item)
    assert response.status_code == 200
    
    # Test get all positions
    response = test_app.get("/api/portfolio")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["ticker"] == "AAPL"
    
    # Test update position
    update_data = {**sample_portfolio_item, "quantity": 150}
    response = test_app.put("/api/portfolio/AAPL", json=update_data)
    assert response.status_code == 200
    
    # Test get updated position
    response = test_app.get("/api/portfolio")
    assert response.status_code == 200
    assert response.json()[0]["quantity"] == 150
    
    # Test delete position
    response = test_app.delete("/api/portfolio/AAPL")
    assert response.status_code == 200
    
    # Test portfolio is empty again
    response = test_app.get("/api/portfolio")
    assert response.status_code == 200
    assert len(response.json()) == 0
```

- [ ] **Step 3: Write settings API tests**

```python
def test_settings_api(test_app, sample_model_config):
    """Test settings API endpoints"""
    # Test get settings
    response = test_app.get("/api/settings")
    assert response.status_code == 200
    assert isinstance(response.json(), dict)
    
    # Test update model config
    response = test_app.put("/api/settings/model-config", json=sample_model_config)
    assert response.status_code == 200
    assert response.json()["provider"] == "openrouter"
```

- [ ] **Step 4: Write Finnhub API mock**

```python
# backend/tests/mocks/mock_finnhub.py
class MockFinnhubService:
    """Mock Finnhub service for testing"""
    
    def __init__(self, api_key=None):
        pass
    
    async def get_quote(self, ticker: str):
        """Mock get quote"""
        return {
            "c": 150.0,  # Current price
            "h": 155.0,  # High
            "l": 145.0,  # Low
            "o": 148.0,  # Open
            "pc": 149.0  # Previous close
        }
    
    async def get_company_profile(self, ticker: str):
        """Mock company profile"""
        return {
            "name": "Apple Inc.",
            "country": "US",
            "ipo": "1980-12-12",
            "logo": "https://example.com/aapl-logo.png",
            "marketCapitalization": 2000000000000,
            "ticker": "AAPL"
        }
    
    async def get_news(self, ticker: str):
        """Mock news"""
        return [
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
    
    async def get_financials(self, ticker: str):
        """Mock financials"""
        return {
            "totalRevenue": 394328000000,
            "netIncome": 96995000000,
            "grossProfit": 170782000000,
            "totalAssets": 455183000000
        }
```

- [ ] **Step 5: Write LLM mock**

```python
# backend/tests/mocks/mock_llm.py
class MockModelAdapter:
    """Mock LLM model adapter for testing"""
    
    async def chat(self, messages, **kwargs):
        """Mock chat completion"""
        return "This is a mock response from the LLM"
    
    async def analyze(self, context, **kwargs):
        """Mock analysis function"""
        return {
            "ticker": "AAPL",
            "analysis": "Mock analysis",
            "confidence": 0.85
        }
```

- [ ] **Step 6: Run integration tests**

```bash
cd backend
pytest tests/integration/ -v
```

Expected: PASS

- [ ] **Step 7: Commit the changes**

```bash
cd backend
git add tests/integration/test_api_*.py tests/mocks/mock_*.py
git commit -m "test: add backend API integration tests"
```

---

## Task 4: Set Up Frontend Testing Infrastructure

**Files:**
- Create: `frontend/playwright.config.ts`
- Create: `frontend/tests/support/fixtures.ts`
- Create: `frontend/tests/support/helpers.ts`
- Create: `frontend/tests/support/mocks/__init__.py`
- Modify: `frontend/package.json`

- [ ] **Step 1: Install Playwright**

```bash
cd frontend
npm init playwright@latest
```

Select options:
- Choose between TypeScript or JavaScript: TypeScript
- Where to put your end-to-end tests: tests/e2e
- Add a GitHub Actions workflow: No

- [ ] **Step 2: Write Playwright configuration**

```typescript
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',
  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
  ],

  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
  },
});
```

- [ ] **Step 3: Create test fixtures**

```typescript
import { test as base } from '@playwright/test';

export type TestFixtures = {
  testUser: string;
  samplePortfolioItem: {
    ticker: string;
    quantity: number;
    avgPrice: number;
    purchaseDate: string;
  };
};

export const test = base.extend<TestFixtures>({
  testUser: 'test-user',
  samplePortfolioItem: {
    ticker: 'AAPL',
    quantity: 100,
    avgPrice: 150,
    purchaseDate: '2026-04-04',
  },
});

export { expect } from '@playwright/test';
```

- [ ] **Step 4: Create test helpers**

```typescript
// frontend/tests/support/helpers.ts
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
```

- [ ] **Step 5: Create Finnhub API mock**

```typescript
// frontend/tests/support/mocks/finnhub.ts
export function mockFinnhubAPI(page: any) {
  page.route('https://finnhub.io/api/v1/*', async (route: any) => {
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
```

- [ ] **Step 6: Create LLM API mock**

```typescript
// frontend/tests/support/mocks/llm.ts
export function mockLLMAPI(page: any) {
  page.route('**/api/agents/*/chat', async (route: any) => {
    await route.fulfill({
      status: 200,
      json: {
        response: 'This is a mock response from the ' + 
                 route.request().url().split('/').pop() + ' agent'
      }
    });
  });

  page.route('**/api/analysis/*', async (route: any) => {
    await route.fulfill({
      status: 200,
      json: {
        task_id: 'test-task-123',
        status: 'completed',
        results: [
          {
            agent: 'news',
            analysis: 'News analysis: Positive sentiment'
          },
          {
            agent: 'fundamentals',
            analysis: 'Fundamentals: Strong financial position'
          }
        ]
      }
    });
  });
}
```

- [ ] **Step 7: Commit the changes**

```bash
cd frontend
git add playwright.config.ts tests/support/ tests/e2e/
git commit -m "test: add Playwright testing infrastructure"
```

---

## Task 5: Write Frontend E2E Tests

**Files:**
- Create: `frontend/tests/e2e/portfolio.spec.ts`
- Create: `frontend/tests/e2e/analysis.spec.ts`
- Create: `frontend/tests/e2e/agents.spec.ts`
- Create: `frontend/tests/e2e/settings.spec.ts`

- [ ] **Step 1: Write portfolio management tests**

```typescript
import { test, expect } from '@playwright/test';
import { mockFinnhubAPI, mockLLMAPI } from '../support/mocks';

test.describe('Portfolio Management', () => {
  test.beforeEach(async ({ page }) => {
    mockFinnhubAPI(page);
    mockLLMAPI(page);
    await page.goto('/portfolio');
  });

  test('should display empty portfolio state', async ({ page }) => {
    await expect(page.getByText('Your portfolio is empty')).toBeVisible();
  });

  test('should add a new stock position', async ({ page }) => {
    await page.click('text=Add Position');
    await page.fill('input[name="ticker"]', 'AAPL');
    await page.fill('input[name="quantity"]', '100');
    await page.fill('input[name="avgPrice"]', '150');
    await page.click('text=Add');
    
    await expect(page.getByText('AAPL')).toBeVisible();
    await expect(page.getByText('100')).toBeVisible();
    await expect(page.getByText('$15,000.00')).toBeVisible();
  });

  test('should edit an existing position', async ({ page }) => {
    await page.click('text=Add Position');
    await page.fill('input[name="ticker"]', 'AAPL');
    await page.fill('input[name="quantity"]', '100');
    await page.fill('input[name="avgPrice"]', '150');
    await page.click('text=Add');

    await page.click('button[aria-label="Edit AAPL"]');
    await page.fill('input[name="quantity"]', '150');
    await page.click('text=Save');
    
    await expect(page.getByText('150')).toBeVisible();
  });

  test('should delete a position', async ({ page }) => {
    await page.click('text=Add Position');
    await page.fill('input[name="ticker"]', 'AAPL');
    await page.fill('input[name="quantity"]', '100');
    await page.fill('input[name="avgPrice"]', '150');
    await page.click('text=Add');

    await page.click('button[aria-label="Delete AAPL"]');
    await page.click('text=Confirm Delete');
    
    await expect(page.getByText('AAPL')).not.toBeVisible();
  });
});
```

- [ ] **Step 2: Write stock analysis tests**

```typescript
import { test, expect } from '@playwright/test';
import { mockFinnhubAPI, mockLLMAPI } from '../support/mocks';

test.describe('Stock Analysis', () => {
  test.beforeEach(async ({ page }) => {
    mockFinnhubAPI(page);
    mockLLMAPI(page);
    await page.goto('/analysis');
  });

  test('should search and analyze a stock', async ({ page }) => {
    await page.fill('input[placeholder="Search stock..."]', 'AAPL');
    await page.click('text=Search');

    await expect(page.getByText('Apple Inc.')).toBeVisible();
    await expect(page.getByText('Market Cap: $2.0T')).toBeVisible();

    await page.click('text=Analyze Stock');
    
    await expect(page.getByText('Analysis in progress...')).toBeVisible();
    await expect(page.getByText('News Analysis')).toBeVisible();
  });
});
```

- [ ] **Step 3: Write agent chat tests**

```typescript
import { test, expect } from '@playwright/test';
import { mockLLMAPI } from '../support/mocks';

test.describe('Agent Chat', () => {
  test.beforeEach(async ({ page }) => {
    mockLLMAPI(page);
    await page.goto('/agents');
  });

  test('should list available agents', async ({ page }) => {
    await expect(page.getByText('News Agent')).toBeVisible();
    await expect(page.getByText('SEC Agent')).toBeVisible();
    await expect(page.getByText('Fundamentals Agent')).toBeVisible();
  });

  test('should send message to news agent', async ({ page }) => {
    await page.selectOption('select[name="agent"]', 'news');
    await page.fill('textarea[name="message"]', 'What is the news about AAPL?');
    await page.click('text=Send');

    await expect(page.getByText('Mock response from the news agent')).toBeVisible();
  });
});
```

- [ ] **Step 4: Write settings tests**

```typescript
import { test, expect } from '@playwright/test';

test.describe('Settings', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/settings');
  });

  test('should display settings page', async ({ page }) => {
    await expect(page.getByText('Model Configuration')).toBeVisible();
    await expect(page.getByText('API Keys')).toBeVisible();
    await expect(page.getByText('Investment Style')).toBeVisible();
  });

  test('should update model configuration', async ({ page }) => {
    await page.selectOption('select[name="provider"]', 'openrouter');
    await page.fill('input[name="apiKey"]', 'test-api-key');
    await page.click('text=Save Settings');

    await expect(page.getByText('Settings updated successfully')).toBeVisible();
  });

  test('should update investment style', async ({ page }) => {
    await page.check('input[value="conservative"]');
    await page.click('text=Save Settings');
    
    await expect(page.getByText('Investment style: Conservative')).toBeVisible();
  });
});
```

- [ ] **Step 5: Run the E2E tests**

```bash
cd frontend
npm run build
npm run test:e2e
```

Expected: All tests pass

- [ ] **Step 6: Commit the changes**

```bash
cd frontend
git add tests/e2e/*.spec.ts
git commit -m "test: add frontend E2E tests"
```

---

## Task 6: Write Frontend API Tests

**Files:**
- Create: `frontend/tests/api/portfolio.spec.ts`
- Create: `frontend/tests/api/settings.spec.ts`
- Create: `frontend/tests/api/analysis.spec.ts`
- Create: `frontend/tests/api/agents.spec.ts`
- Create: `frontend/tests/api/market.spec.ts`

- [ ] **Step 1: Write portfolio API tests**

```typescript
import { test, expect } from '@playwright/test';

test.describe('Portfolio API', () => {
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
      avg_price: 150.0,
      purchase_date: '2026-04-04'
    };

    const addResponse = await request.post('/api/portfolio', { data: item });
    expect(addResponse.ok()).toBeTruthy();

    const getResponse = await request.get('/api/portfolio');
    const data = await getResponse.json();
    expect(data.length).toBeGreaterThan(0);

    const deleteResponse = await request.delete('/api/portfolio/AAPL');
    expect(deleteResponse.ok()).toBeTruthy();
  });
});
```

- [ ] **Step 2: Write other API tests**

```typescript
import { test, expect } from '@playwright/test';

test.describe('Market API', () => {
  test('should get quote for AAPL', async ({ request }) => {
    const response = await request.get('/api/market/quote/AAPL');
    expect(response.ok()).toBeTruthy();
    const data = await response.json();
    expect(data.ticker).toEqual('AAPL');
  });
});

test.describe('Agents API', () => {
  test('should chat with news agent', async ({ request }) => {
    const response = await request.post('/api/agents/news/chat', {
      data: { message: 'What is the latest news?' }
    });
    expect(response.ok()).toBeTruthy();
    const data = await response.json();
    expect(data.response).toBeDefined();
  });
});

test.describe('Settings API', () => {
  test('should get and update settings', async ({ request }) => {
    const getResponse = await request.get('/api/settings');
    expect(getResponse.ok()).toBeTruthy();

    const config = {
      provider: 'openrouter',
      api_key: 'test-key'
    };
    const updateResponse = await request.put(
      '/api/settings/model-config', 
      { data: config }
    );
    expect(updateResponse.ok()).toBeTruthy();
  });
});
```

- [ ] **Step 3: Run API tests**

```bash
cd frontend
npm run test:api
```

Expected: All tests pass

- [ ] **Step 4: Commit the changes**

```bash
cd frontend
git add tests/api/*.spec.ts
git commit -m "test: add API tests via Playwright"
```

---

## Task 7: Run Full Test Suite & Verify

**Files:**
- Modify: `backend/.gitignore`
- Modify: `frontend/.gitignore`

- [ ] **Step 1: Add test temp files to gitignore**

Add to backend/.gitignore:
```
.pytest_cache/
.coverage
htmlcov/
*.pyc
__pycache__/
/tmp/test_finassist/
```

Add to frontend/.gitignore:
```
playwright-report/
test-results/
*.swp
*.swo
.DS_Store
```

- [ ] **Step 2: Run all backend tests**

```bash
cd backend
pytest tests/ -v --tb=short
```

Expected: All tests pass

- [ ] **Step 3: Run backend with coverage**

```bash
cd backend
pytest tests/ --cov=. --cov-report=html
```

Check coverage report: open `htmlcov/index.html`

- [ ] **Step 4: Run all frontend tests**

```bash
cd frontend
npm run test:e2e -- --headless
npm run test:api -- --headless
```

Expected: All tests pass

- [ ] **Step 5: Clean up and commit**

```bash
cd finAssist
git add backend/.gitignore frontend/.gitignore
git commit -m "test: add test temp files to gitignore"
```

---

## Success Criteria

- ✅ All backend tests (20+ tests) pass
- ✅ All frontend tests (15+ tests) pass
- ✅ Coverage report shows > 60% coverage for core backend files
- ✅ Tests run in < 5 minutes
- ✅ No flaky tests
- ✅ Mocks provide consistent, deterministic responses
- ✅ Tests are isolated and don't interfere with each other

---

## Running the Tests

### Running Backend Tests

```bash
cd backend
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=. --cov-report=html

# Run specific test file
pytest tests/unit/test_storage.py -v

# Run specific test function
pytest tests/unit/test_storage.py::test_portfolio_store_crud -v
```

### Running Frontend Tests

```bash
cd frontend
# Run E2E tests (headed)
npm run test:e2e

# Run E2E tests (headless)
npm run test:e2e -- --headless

# Run API tests only
npm run test:api

# Run specific test file
npm run test:e2e -- tests/e2e/portfolio.spec.ts
```

### CI Integration

**GitHub Actions (backend):**
```yaml
name: Backend Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-python@v5
      with:
        python-version: '3.10'
    - name: Install dependencies
      run: |
        cd backend
        pip install -r requirements.txt
    - name: Run tests
      run: |
        cd backend
        pytest tests/ -v
```

**GitHub Actions (frontend):**
```yaml
name: Frontend Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-node@v4
      with:
        node-version: '18'
    - name: Install dependencies
      run: |
        cd frontend
        npm ci
    - name: Run Playwright tests
      run: |
        cd frontend
        npx playwright install --with-deps
        npm run test:e2e -- --headless
    - uses: actions/upload-artifact@v4
      if: ${{ !cancelled() }}
      with:
        name: playwright-report
        path: frontend/playwright-report
        retention-days: 7
```
