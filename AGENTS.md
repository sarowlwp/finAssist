# finAssist - Investment AI Assistant

Full-stack investment analysis system using AgentScope multi-agent framework.

## Architecture

- **Backend**: FastAPI (port 8001) + AgentScope multi-agent system
- **Frontend**: Next.js 14 (port 3000) + Tailwind CSS
- **Database**: SQLite (auto-initializes on startup)
- **External APIs**: Finnhub for financial data

## Startup Commands

**Backend** (from `backend/`):
```bash
# Activate venv first
source venv/bin/activate  # macOS/Linux
python main.py
```

**Frontend** (from `frontend/`):
```bash
npm run dev
```

## Development Workflow

The backend has **hot reload disabled** (`reload=False` in main.py) to prevent ECONNRESET errors during development. Always restart both services after code changes.

**Restart services properly**:
```bash
# Stop backend
pkill -f "uvicorn" || true
rm -f backend/uvicorn.pid

# Stop frontend  
pkill -f "next" || true
rm -f frontend/next.pid

# Restart from respective directories
cd backend: python main.py
cd frontend: npm run dev
```

## Database Management

SQLite database auto-initializes on first run at `backend/data/finance_assistant.db`.

Manual database operations (from `backend/`):
```bash
python scripts/db/init_db.py init    # Full init with sample data
python scripts/db/init_db.py reset   # Delete all data and reinit
python scripts/db/init_db.py sample  # Add sample holdings only
```

Database tables: `portfolio_holdings`, `analysis_reports`, `agent_reports`, `analysis_tasks`, `finnhub_cache`

## Testing

E2E tests use Playwright:
```bash
npm run test:e2e    # All E2E tests
npm run test:api    # API-specific tests
```

## Key Project Files

- `backend/main.py` - FastAPI entry point (port 8001, reload disabled)
- `backend/agents/` - AgentScope multi-agent system (7 agents)
- `backend/routers/` - API endpoints
- `backend/scripts/db/init_db.py` - Database management
- `frontend/src/lib/api.ts` - API client
- `frontend/src/app/` - Next.js page routes

## Agent System

7 specialized agents: Supervisor, News, SEC, Fundamentals, Technical, Custom Skill, Fusion Agent.

## Important Constraints

- Backend requires Python 3.10+ with virtual environment
- Frontend requires Node.js 18+ 
- Finnhub API key required (configure via env var or settings page)
- Do NOT enable hot reload on backend (causes ECONNRESET errors)
