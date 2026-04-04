---
name: E2E Testing Design
description: Comprehensive end-to-end testing strategy for the finAssist investment AI assistant
type: design
---

# E2E Testing Design for finAssist

Date: 2026-04-04

## Overview

This document describes the comprehensive end-to-end testing strategy for the finAssist private investment AI assistant. The goal is to ensure stability for future changes by testing all critical user flows, API endpoints, and UI interactions.

## Technology Stack

### Backend Testing
- **Unit/Integration Tests:** pytest + httpx
- **Coverage:** pytest-cov
- **Mocking:** pytest monkeypatch + custom mock classes

### Frontend & E2E Testing
- **E2E Tests:** Playwright (TypeScript)
- **API Tests:** Playwright API testing
- **Browser Support:** Chromium, Firefox

## Test Structure

### Backend Test Structure
```
backend/
├── tests/
│   ├── __init__.py
│   ├── conftest.py              # pytest configuration & fixtures
│   ├── unit/
│   │   ├── test_storage.py      # Unit tests for storage layer
│   │   └── test_model_adapter.py
│   ├── integration/
│   │   ├── test_api_portfolio.py
│   │   ├── test_api_settings.py
│   │   ├── test_api_analysis.py
│   │   ├── test_api_agents.py
│   │   └── test_api_market.py
│   └── mocks/
│       ├── mock_finnhub.py
│       └── mock_llm.py
```

### Playwright Test Structure
```
frontend/
├── tests/
│   ├── e2e/
│   │   ├── portfolio.spec.ts    # Portfolio management flow
│   │   ├── analysis.spec.ts     # Stock analysis flow
│   │   ├── agents.spec.ts       # Agent chat flow
│   │   └── settings.spec.ts     # Settings configuration
│   ├── api/
│   │   ├── portfolio.spec.ts    # API tests via Playwright
│   │   ├── settings.spec.ts
│   │   ├── analysis.spec.ts
│   │   ├── agents.spec.ts
│   │   └── market.spec.ts
│   ├── support/
│   │   ├── fixtures.ts          # Test fixtures
│   │   ├── mocks/
│   │   │   ├── finnhub.ts
│   │   │   └── llm.ts
│   │   └── helpers.ts
│   └── playwright.config.ts
```

## Test Coverage Plan

### Main User Flows

#### 1. Portfolio Management
- View empty portfolio state
- Add a new stock position (AAPL, 100 shares, $150)
- Edit an existing position
- Delete a position
- View portfolio summary with totals

#### 2. Stock Analysis
- Search for a stock (AAPL)
- Trigger full analysis
- View analysis results from multiple agents
- Check that charts render correctly

#### 3. Agent Chat
- Navigate to Agents page
- Select an agent (News Agent)
- Send a message
- Verify response is received
- Test multiple agents

#### 4. Settings
- View current settings
- Update model configuration
- Update Finnhub API key
- Test investment style selection

### Backend API Test Coverage
- All CRUD operations for portfolio
- Settings GET/PUT
- Analysis endpoints (ticker + portfolio)
- Agent chat endpoints
- Market data endpoints
- Health checks (`/`, `/health`)

## Mocking Strategy

### Finnhub API Mock
- Mock quote endpoint: returns static price data for test tickers (AAPL, MSFT, GOOGL)
- Mock company profile endpoint
- Mock news endpoint
- Mock financials endpoint
- All mocks return consistent, deterministic data

### LLM Provider Mock
- Mock chat completions endpoint
- Returns pre-defined responses for each agent type
- Avoids real API costs and flakiness
- Allows testing error scenarios

### Implementation Approach
- Backend: Use pytest monkeypatch + custom mock classes
- Playwright: Use route mocking to intercept API calls
- Test data stored in JSON files for easy maintenance

## Success Criteria

1. **Reliability:** All tests pass consistently without flakiness
2. **Speed:** Complete test suite runs in < 5 minutes
3. **Maintainability:** Easy to add new tests as features are added
4. **Debuggability:** Clear failure messages and screenshots on failure
5. **Coverage:** Core functionality has comprehensive test coverage

## Implementation Steps

1. Set up pytest backend testing infrastructure
2. Create mock implementations for external APIs
3. Write backend unit and integration tests
4. Set up Playwright for frontend E2E testing
5. Write Playwright E2E tests for main user flows
6. Write Playwright API tests
7. Configure test scripts in package.json and requirements.txt
8. Document how to run tests
