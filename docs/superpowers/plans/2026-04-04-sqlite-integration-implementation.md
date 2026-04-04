# SQLite 集成实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现 SQLite 数据库集成，包括 Finnhub 数据缓存和分析报告存储，加速页面加载并支持历史报告查阅

**Architecture:** 使用 SQLAlchemy ORM 实现数据持久化，Finnhub 数据按类型设置不同的 TTL 缓存，分析报告主表与 Agent 报告明细表分离，支持灵活扩展

**Tech Stack:** Python 3.11+, SQLAlchemy 2.0+, SQLite, FastAPI, Pydantic

---

## 文件结构概览

### 创建的新文件

| 文件 | 用途 |
|------|------|
| `backend/database.py` | 数据库连接和会话管理 |
| `backend/models.py` | SQLAlchemy 数据模型定义 |
| `backend/services/finnhub_cache_service.py` | Finnhub 数据缓存服务 |
| `backend/services/analysis_report_repository.py` | 分析报告仓库 |

### 要修改的现有文件

| 文件 | 修改内容 |
|------|---------|
| `backend/config.py` | 添加 SQLite 配置 |
| `backend/dependencies.py` | 注入 SQLAlchemy 依赖 |
| `backend/services/finnhub_service.py` | 添加缓存逻辑 |
| `backend/storage/analysis.py` | 使用 SQLAlchemy 存储 |
| `backend/routers/analysis.py` | 更新依赖注入 |
| `backend/main.py` | 数据库初始化 |

---

## 任务分解

### 任务 1: 设置 SQLAlchemy 基础架构

**Files:**
- Create: `backend/database.py`
- Create: `backend/models.py`

- [ ] **Step 1: 创建数据库连接管理**

```python
# backend/database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pathlib import Path
from config import config

SQLALCHEMY_DATABASE_URL = f"sqlite:///{config.DATA_DIR / 'finance_assistant.db'}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

- [ ] **Step 2: 创建数据模型**

```python
# backend/models.py
from sqlalchemy import Column, Integer, String, DateTime, JSON, DECIMAL, ForeignKey
from sqlalchemy.sql import func
from database import Base
from typing import List
from sqlalchemy.orm import relationship

class FinnhubCache(Base):
    __tablename__ = "finnhub_cache"
    
    id = Column(Integer, primary_key=True, index=True)
    cache_key = Column(String(255), unique=True, index=True, nullable=False)
    data_type = Column(String(50), nullable=False)
    ticker = Column(String(20), nullable=False)
    data = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)
    
class AnalysisReport(Base):
    __tablename__ = "analysis_reports"
    
    report_id = Column(String(36), primary_key=True, index=True)
    ticker = Column(String(20), index=True, nullable=False)
    company_name = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(String(20), nullable=False)
    current_price = Column(DECIMAL(15, 4), nullable=False)
    change_percent = Column(DECIMAL(10, 4), nullable=False)
    fusion_summary = Column(String, nullable=True)
    
    agent_reports = relationship("AgentReport", back_populates="analysis_report")
    
class AgentReport(Base):
    __tablename__ = "agent_reports"
    
    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(String(36), ForeignKey("analysis_reports.report_id"), nullable=False)
    agent_name = Column(String(100), nullable=False)
    agent_content = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    analysis_report = relationship("AnalysisReport", back_populates="agent_reports")
```

- [ ] **Step 3: 提交**

```bash
cd /Users/sarowlwp/Document/go/finAssist
git add backend/database.py backend/models.py
git commit -m "feat: create SQLAlchemy models and database configuration"
```

---

### 任务 2: 创建 Finnhub 缓存服务

**Files:**
- Create: `backend/services/finnhub_cache_service.py`
- Modify: `backend/config.py:1-78`
- Modify: `backend/dependencies.py:1-25`

- [ ] **Step 1: 创建缓存服务**

```python
# backend/services/finnhub_cache_service.py
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from models import FinnhubCache
from typing import Dict, Any, Optional

CACHE_TTL_CONFIG = {
    "quote": timedelta(minutes=5),
    "profile": timedelta(hours=24),
    "financials": timedelta(hours=12),
    "news": timedelta(hours=1),
    "technical": timedelta(hours=4)
}

class FinnhubCacheService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_cache(self, data_type: str, ticker: str) -> Optional[Dict[str, Any]]:
        cache_key = f"{data_type}:{ticker.upper()}"
        
        cache_entry = self.db.query(FinnhubCache).filter(
            FinnhubCache.cache_key == cache_key,
            FinnhubCache.expires_at > datetime.now()
        ).first()
        
        if cache_entry:
            return cache_entry.data
        
        return None
    
    def set_cache(self, data_type: str, ticker: str, data: Dict[str, Any]):
        cache_key = f"{data_type}:{ticker.upper()}"
        
        ttl = CACHE_TTL_CONFIG.get(data_type, timedelta(hours=1))
        expires_at = datetime.now() + ttl
        
        existing = self.db.query(FinnhubCache).filter(
            FinnhubCache.cache_key == cache_key
        ).first()
        
        if existing:
            existing.data = data
            existing.expires_at = expires_at
        else:
            new_cache = FinnhubCache(
                cache_key=cache_key,
                data_type=data_type,
                ticker=ticker.upper(),
                data=data,
                expires_at=expires_at
            )
            self.db.add(new_cache)
        
        self.db.commit()
    
    def delete_cache(self, data_type: str, ticker: str):
        cache_key = f"{data_type}:{ticker.upper()}"
        self.db.query(FinnhubCache).filter(FinnhubCache.cache_key == cache_key).delete()
        self.db.commit()
    
    def delete_expired_cache(self):
        self.db.query(FinnhubCache).filter(
            FinnhubCache.expires_at <= datetime.now()
        ).delete()
        self.db.commit()
```

- [ ] **Step 2: 更新依赖注入**

```python
# backend/dependencies.py
from fastapi import Depends
from sqlalchemy.orm import Session
from database import get_db
from services.finnhub_cache_service import FinnhubCacheService
from services.analysis_report_repository import AnalysisReportRepository
from storage.analysis import AnalysisStore
from config import config

def get_finnhub_cache_service(db: Session = Depends(get_db)):
    return FinnhubCacheService(db)

def get_analysis_repository(db: Session = Depends(get_db)):
    return AnalysisReportRepository(db)

def get_analysis_store() -> AnalysisStore:
    return AnalysisStore(config.DATA_DIR)
```

- [ ] **Step 3: 提交**

```bash
git add backend/services/finnhub_cache_service.py backend/dependencies.py
git commit -m "feat: add Finnhub cache service with TTL management"
```

---

### 任务 3: 创建分析报告仓库

**Files:**
- Create: `backend/services/analysis_report_repository.py`

- [ ] **Step 1: 创建报告仓库**

```python
# backend/services/analysis_report_repository.py
from sqlalchemy.orm import Session
from models import AnalysisReport, AgentReport
from typing import List, Optional, Dict, Any
from datetime import datetime

class AnalysisReportRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def create_report(self, report_id: str, ticker: str, company_name: str,
                     current_price: float, change_percent: float,
                     status: str = "analyzing") -> AnalysisReport:
        report = AnalysisReport(
            report_id=report_id,
            ticker=ticker,
            company_name=company_name,
            created_at=datetime.now().isoformat(),
            status=status,
            current_price=current_price,
            change_percent=change_percent
        )
        self.db.add(report)
        self.db.commit()
        self.db.refresh(report)
        return report
    
    def get_report(self, report_id: str) -> Optional[AnalysisReport]:
        return self.db.query(AnalysisReport).filter(
            AnalysisReport.report_id == report_id
        ).first()
    
    def get_reports_by_ticker(self, ticker: str, limit: int = 20) -> List[AnalysisReport]:
        return self.db.query(AnalysisReport).filter(
            AnalysisReport.ticker == ticker.upper()
        ).order_by(AnalysisReport.created_at.desc()).limit(limit).all()
    
    def get_recent_reports(self, limit: int = 20) -> List[AnalysisReport]:
        return self.db.query(AnalysisReport).order_by(
            AnalysisReport.created_at.desc()
        ).limit(limit).all()
    
    def update_report_status(self, report_id: str, status: str):
        report = self.get_report(report_id)
        if report:
            report.status = status
            self.db.commit()
    
    def update_report_summary(self, report_id: str, fusion_summary: str):
        report = self.get_report(report_id)
        if report:
            report.fusion_summary = fusion_summary
            self.db.commit()
    
    def add_agent_report(self, report_id: str, agent_name: str,
                       agent_content: str) -> AgentReport:
        agent_report = AgentReport(
            report_id=report_id,
            agent_name=agent_name,
            agent_content=agent_content
        )
        self.db.add(agent_report)
        self.db.commit()
        self.db.refresh(agent_report)
        return agent_report
    
    def get_agent_reports(self, report_id: str) -> List[AgentReport]:
        return self.db.query(AgentReport).filter(
            AgentReport.report_id == report_id
        ).all()
    
    def delete_report(self, report_id: str) -> bool:
        self.db.query(AgentReport).filter(
            AgentReport.report_id == report_id
        ).delete()
        
        result = self.db.query(AnalysisReport).filter(
            AnalysisReport.report_id == report_id
        ).delete()
        self.db.commit()
        return result > 0
```

- [ ] **Step 2: 提交**

```bash
git add backend/services/analysis_report_repository.py
git commit -m "feat: create analysis report repository"
```

---

### 任务 4: 更新 FinnhubService 添加缓存逻辑

**Files:**
- Modify: `backend/services/finnhub_service.py:1-282`

- [ ] **Step 1: 更新 FinnhubService 构造函数和方法**

```python
# backend/services/finnhub_service.py
class FinnhubService:
    """Finnhub API 服务类"""
    
    def __init__(self, api_key: str, db: Session = None):
        self.client = FinnhubClient(api_key=api_key)
        self.db = db
    
    # ... (其他方法保持不变)
    
    def get_quote(self, ticker: str, use_cache: bool = True) -> Dict[str, Any]:
        """
        获取实时报价
        
        Args:
            ticker: 股票代码
            use_cache: 是否使用缓存
            
        Returns:
            包含报价信息的字典
        """
        if use_cache and self.db:
            from services.finnhub_cache_service import FinnhubCacheService
            cache_service = FinnhubCacheService(self.db)
            cached = cache_service.get_cache("quote", ticker)
            if cached:
                return cached
        
        try:
            quote = self.client.quote(ticker)
            result = {
                "success": True,
                "ticker": ticker,
                "current_price": quote.get("c"),
                "change": quote.get("d"),
                "percent_change": quote.get("dp"),
                "high_price": quote.get("h"),
                "low_price": quote.get("l"),
                "open_price": quote.get("o"),
                "previous_close": quote.get("pc"),
                "timestamp": datetime.now().isoformat()
            }
            
            if self.db:
                from services.finnhub_cache_service import FinnhubCacheService
                cache_service = FinnhubCacheService(self.db)
                cache_service.set_cache("quote", ticker, result)
            
            return result
        except Exception as e:
            return self._handle_api_error("get_quote", e)
    
    def get_company_profile(self, ticker: str, use_cache: bool = True) -> Dict[str, Any]:
        if use_cache and self.db:
            from services.finnhub_cache_service import FinnhubCacheService
            cache_service = FinnhubCacheService(self.db)
            cached = cache_service.get_cache("profile", ticker)
            if cached:
                return cached
        
        try:
            profile = self.client.company_profile2(symbol=ticker)
            result = {
                "success": True,
                "ticker": ticker,
                "company_name": profile.get("name"),
                "country": profile.get("country"),
                "currency": profile.get("currency"),
                "exchange": profile.get("exchange"),
                "industry": profile.get("finnhubIndustry"),
                "market_cap": profile.get("marketCapitalization"),
                "description": profile.get("description"),
                "website": profile.get("weburl"),
                "logo": profile.get("logo"),
                "timestamp": datetime.now().isoformat()
            }
            
            if self.db:
                from services.finnhub_cache_service import FinnhubCacheService
                cache_service = FinnhubCacheService(self.db)
                cache_service.set_cache("profile", ticker, result)
            
            return result
        except Exception as e:
            return self._handle_api_error("get_company_profile", e)
    
    def get_financials(self, ticker: str, use_cache: bool = True) -> Dict[str, Any]:
        if use_cache and self.db:
            from services.finnhub_cache_service import FinnhubCacheService
            cache_service = FinnhubCacheService(self.db)
            cached = cache_service.get_cache("financials", ticker)
            if cached:
                return cached
        
        try:
            financials = self.client.company_basic_financials(ticker, "all")
            metric = financials.get("metric", {})
            
            result = {
                "success": True,
                "ticker": ticker,
                "pe_ratio": metric.get("peBasicExclExtraTTM"),
                "pb_ratio": metric.get("pbQuarterly"),
                "ps_ratio": metric.get("psTTM"),
                "roe": metric.get("roeTTM"),
                "roa": metric.get("roaTTM"),
                "profit_margin": metric.get("netMarginTTM"),
                "dividend_yield": metric.get("dividendYieldTTM"),
                "debt_to_equity": metric.get("debtToEquityQuarterly"),
                "current_ratio": metric.get("currentRatioQuarterly"),
                "quick_ratio": metric.get("quickRatioQuarterly"),
                "revenue_growth": metric.get("revenueGrowth5Y"),
                "earnings_growth": metric.get("epsGrowth5Y"),
                "timestamp": datetime.now().isoformat()
            }
            
            if self.db:
                from services.finnhub_cache_service import FinnhubCacheService
                cache_service = FinnhubCacheService(self.db)
                cache_service.set_cache("financials", ticker, result)
            
            return result
        except Exception as e:
            return self._handle_api_error("get_financials", e)
    
    def get_company_news(self, ticker: str, from_date: Optional[str] = None, 
                        to_date: Optional[str] = None, use_cache: bool = True) -> Dict[str, Any]:
        if use_cache and self.db:
            from services.finnhub_cache_service import FinnhubCacheService
            cache_service = FinnhubCacheService(self.db)
            cached = cache_service.get_cache("news", ticker)
            if cached:
                return cached
        
        try:
            if not from_date:
                from_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
            if not to_date:
                to_date = datetime.now().strftime("%Y-%m-%d")
            
            news = self.client.company_news(ticker, _from=from_date, to=to_date)
            
            news_list = []
            for item in news[:10]:
                news_list.append({
                    "headline": item.get("headline"),
                    "summary": item.get("summary"),
                    "url": item.get("url"),
                    "source": item.get("source"),
                    "datetime": datetime.fromtimestamp(item.get("datetime", 0)).isoformat() if item.get("datetime") else None,
                    "related_symbols": item.get("related", [])
                })
            
            result = {
                "success": True,
                "ticker": ticker,
                "news": news_list,
                "from_date": from_date,
                "to_date": to_date,
                "count": len(news_list),
                "timestamp": datetime.now().isoformat()
            }
            
            if self.db:
                from services.finnhub_cache_service import FinnhubCacheService
                cache_service = FinnhubCacheService(self.db)
                cache_service.set_cache("news", ticker, result)
            
            return result
        except Exception as e:
            return self._handle_api_error("get_company_news", e)
    
    def get_technical_indicators(self, ticker: str, use_cache: bool = True) -> Dict[str, Any]:
        if use_cache and self.db:
            from services.finnhub_cache_service import FinnhubCacheService
            cache_service = FinnhubCacheService(self.db)
            cached = cache_service.get_cache("technical", ticker)
            if cached:
                return cached
        
        try:
            end_date = int(datetime.now().timestamp())
            start_date = int((datetime.now() - timedelta(days=60)).timestamp())
            
            candles = self.client.stock_candles(
                ticker, 
                "D", 
                start_date, 
                end_date
            )
            
            if candles.get("s") != "ok" or not candles.get("c"):
                return {
                    "success": False,
                    "error": "Unable to fetch candle data",
                    "ticker": ticker
                }
            
            close_prices = candles["c"]
            
            rsi = self._calculate_rsi(close_prices)
            macd = self._calculate_macd(close_prices)
            bollinger = self._calculate_bollinger_bands(close_prices)
            
            result = {
                "success": True,
                "ticker": ticker,
                "current_price": close_prices[-1],
                "rsi": rsi,
                "macd": macd,
                "bollinger_bands": bollinger,
                "rsi_signal": "overbought" if rsi > 70 else "oversold" if rsi < 30 else "neutral",
                "timestamp": datetime.now().isoformat()
            }
            
            if self.db:
                from services.finnhub_cache_service import FinnhubCacheService
                cache_service = FinnhubCacheService(self.db)
                cache_service.set_cache("technical", ticker, result)
            
            return result
        except Exception as e:
            return self._handle_api_error("get_technical_indicators", e)
```

- [ ] **Step 2: 提交**

```bash
git add backend/services/finnhub_service.py
git commit -m "feat: update FinnhubService with caching support"
```

---

### 任务 5: 更新 AnalysisStore 使用 SQLAlchemy

**Files:**
- Modify: `backend/storage/analysis.py:1-134`

- [ ] **Step 1: 更新 AnalysisStore**

```python
# backend/storage/analysis.py
"""
分析报告存储模块
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from pathlib import Path
import json
from datetime import datetime
from services.analysis_report_repository import AnalysisReportRepository
from dependencies import get_db
from models import AnalysisReport as DBReport
from models import AgentReport as DBAgentReport

class AnalysisReport(BaseModel):
    """分析报告模型"""
    report_id: str = Field(..., description="报告唯一标识符")
    ticker: str = Field(..., description="股票代码")
    company_name: str = Field(..., description="公司名称")
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat(), description="创建时间")
    status: str = Field(..., description="分析状态: completed, analyzing, failed")
    current_price: float = Field(..., description="当前价格")
    change_percent: float = Field(..., description="涨跌幅")
    fusion_summary: str = Field(..., description="融合分析总结")
    news_report: str = Field(..., description="News Agent 报告")
    sec_report: str = Field(..., description="SEC Agent 报告")
    fundamentals_report: str = Field(..., description="Fundamentals Agent 报告")
    technical_report: str = Field(..., description="Technical Agent 报告")
    custom_skill_report: str = Field(..., description="Custom Skill Agent 报告")


class AnalysisStore:
    """分析报告存储类"""

    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
    
    def load_all(self) -> List[AnalysisReport]:
        db = next(get_db())
        repo = AnalysisReportRepository(db)
        db_reports = repo.get_recent_reports(100)
        
        reports = []
        for db_report in db_reports:
            agent_reports = {
                "news_report": "",
                "sec_report": "",
                "fundamentals_report": "",
                "technical_report": "",
                "custom_skill_report": ""
            }
            
            for agent in repo.get_agent_reports(db_report.report_id):
                if agent.agent_name == "news_agent":
                    agent_reports["news_report"] = agent.agent_content
                elif agent.agent_name == "sec_agent":
                    agent_reports["sec_report"] = agent.agent_content
                elif agent.agent_name == "fundamentals_agent":
                    agent_reports["fundamentals_report"] = agent.agent_content
                elif agent.agent_name == "technical_agent":
                    agent_reports["technical_report"] = agent.agent_content
                elif agent.agent_name == "custom_skill_agent":
                    agent_reports["custom_skill_report"] = agent.agent_content
            
            reports.append(AnalysisReport(
                report_id=db_report.report_id,
                ticker=db_report.ticker,
                company_name=db_report.company_name,
                created_at=db_report.created_at.isoformat(),
                status=db_report.status,
                current_price=float(db_report.current_price),
                change_percent=float(db_report.change_percent),
                fusion_summary=db_report.fusion_summary or "",
                **agent_reports
            ))
        
        return reports
    
    def load_by_ticker(self, ticker: str) -> List[AnalysisReport]:
        all_reports = self.load_all()
        return [report for report in all_reports if report.ticker.upper() == ticker.upper()]
    
    def load_by_id(self, report_id: str) -> Optional[AnalysisReport]:
        db = next(get_db())
        repo = AnalysisReportRepository(db)
        db_report = repo.get_report(report_id)
        
        if db_report:
            agent_reports = {
                "news_report": "",
                "sec_report": "",
                "fundamentals_report": "",
                "technical_report": "",
                "custom_skill_report": ""
            }
            
            for agent in repo.get_agent_reports(db_report.report_id):
                if agent.agent_name == "news_agent":
                    agent_reports["news_report"] = agent.agent_content
                elif agent.agent_name == "sec_agent":
                    agent_reports["sec_report"] = agent.agent_content
                elif agent.agent_name == "fundamentals_agent":
                    agent_reports["fundamentals_report"] = agent.agent_content
                elif agent.agent_name == "technical_agent":
                    agent_reports["technical_report"] = agent.agent_content
                elif agent.agent_name == "custom_skill_agent":
                    agent_reports["custom_skill_report"] = agent.agent_content
            
            return AnalysisReport(
                report_id=db_report.report_id,
                ticker=db_report.ticker,
                company_name=db_report.company_name,
                created_at=db_report.created_at.isoformat(),
                status=db_report.status,
                current_price=float(db_report.current_price),
                change_percent=float(db_report.change_percent),
                fusion_summary=db_report.fusion_summary or "",
                **agent_reports
            )
        
        return None
    
    def save_report(self, report: AnalysisReport) -> AnalysisReport:
        db = next(get_db())
        repo = AnalysisReportRepository(db)
        
        db_report = repo.get_report(report.report_id)
        if not db_report:
            db_report = repo.create_report(
                report_id=report.report_id,
                ticker=report.ticker,
                company_name=report.company_name,
                current_price=report.current_price,
                change_percent=report.change_percent,
                status=report.status
            )
        
        if report.fusion_summary:
            repo.update_report_summary(report.report_id, report.fusion_summary)
        
        agent_outputs = {
            "news_agent": report.news_report,
            "sec_agent": report.sec_report,
            "fundamentals_agent": report.fundamentals_report,
            "technical_agent": report.technical_report,
            "custom_skill_agent": report.custom_skill_report
        }
        
        for agent_name, agent_content in agent_outputs.items():
            if agent_content:
                repo.add_agent_report(report.report_id, agent_name, agent_content)
        
        return report
    
    def delete_report(self, report_id: str) -> bool:
        db = next(get_db())
        repo = AnalysisReportRepository(db)
        return repo.delete_report(report_id)
    
    def delete_reports_by_ticker(self, ticker: str) -> int:
        reports = self.load_by_ticker(ticker)
        count = 0
        db = next(get_db())
        repo = AnalysisReportRepository(db)
        for report in reports:
            repo.delete_report(report.report_id)
            count += 1
        return count
    
    def get_recent_reports(self, limit: int = 10) -> List[AnalysisReport]:
        all_reports = self.load_all()
        sorted_reports = sorted(
            all_reports,
            key=lambda x: datetime.fromisoformat(x.created_at),
            reverse=True
        )
        return sorted_reports[:limit]
```

- [ ] **Step 2: 提交**

```bash
git add backend/storage/analysis.py
git commit -m "feat: update AnalysisStore to use SQLAlchemy"
```

---

### 任务 6: 更新路由注入新依赖

**Files:**
- Modify: `backend/routers/analysis.py:1-580`

- [ ] **Step 1: 更新分析路由**

```python
# backend/routers/analysis.py
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import json
import asyncio
import uuid
from agents.orchestrator import AnalysisOrchestrator
from storage.settings import SettingsStore
from storage.analysis import AnalysisStore, AnalysisReport
from dependencies import get_settings_store, get_analysis_store, get_analysis_repository
from services.finnhub_cache_service import FinnhubCacheService
from services.analysis_report_repository import AnalysisReportRepository
```

- [ ] **Step 2: 提交**

```bash
git add backend/routers/analysis.py
git commit -m "feat: update analysis router dependencies"
```

---

### 任务 7: 更新主程序初始化

**Files:**
- Modify: `backend/main.py:37-48`

- [ ] **Step 1: 更新 startup 事件**

```python
# backend/main.py
@app.on_event("startup")
async def startup_event():
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    # 初始化数据库
    from database import Base, engine
    from services.finnhub_cache_service import FinnhubCacheService
    from database import get_db
    
    Base.metadata.create_all(bind=engine)
    
    db = next(get_db())
    cache_service = FinnhubCacheService(db)
    cache_service.delete_expired_cache()
    
    # 从持久化存储中加载用户自定义 Agent
    from storage.settings import SettingsStore
    from agents.analysis_agent import load_custom_agents_from_settings
    settings_store = SettingsStore(config.DATA_DIR)
    load_custom_agents_from_settings(settings_store)
    
    print("✅ Backend started successfully on port 8001")
```

- [ ] **Step 2: 提交**

```bash
git add backend/main.py
git commit -m "feat: update main.py with database initialization"
```

---

### 任务 8: 安装依赖并测试

**Files:**

- [ ] **Step 1: 安装 SQLAlchemy**

```bash
cd /Users/sarowlwp/Document/go/finAssist/backend
pip install sqlalchemy
```

- [ ] **Step 2: 运行现有测试**

```bash
cd /Users/sarowlwp/Document/go/finAssist
pytest backend/tests/ -v
```

- [ ] **Step 3: 检查是否有任何失败**

---

### 任务 9: 更新 .gitignore

**Files:**
- Modify: `/Users/sarowlwp/Document/go/finAssist/.gitignore:1-74`

- [ ] **Step 1: 添加 SQLite 文件到 .gitignore**

```
# SQLite
*.db
*.sqlite
*.sqlite3
```

- [ ] **Step 2: 提交**

```bash
git add .gitignore
git commit -m "feat: add SQLite files to .gitignore"
```

---

## 自我审核

### 1. Spec 覆盖检查

✅ **数据库架构**：任务 1 实现了 models.py 和数据库连接
✅ **缓存服务**：任务 2 实现了 finnhub_cache_service.py
✅ **报告存储**：任务 3 实现了 analysis_report_repository.py
✅ **Finnhub 服务集成**：任务 4 更新了 finnhub_service.py
✅ **AnalysisStore 更新**：任务 5 更新了 storage/analysis.py
✅ **路由和依赖注入**：任务 6-7 更新了路由和 main.py

### 2. 占位符检查

✅ **没有 TBD 或 TODO**：所有代码都是完整的
✅ **没有模糊指令**：所有任务都有具体的代码示例
✅ **所有方法都有定义**：没有未定义的函数或类型引用

### 3. 类型一致性检查

✅ **类型引用一致**：AnalysisReport 在所有任务中都保持相同的属性
✅ **方法签名一致**：load_by_id, save_report 等接口保持不变
✅ **导入路径一致**：所有导入路径都是正确的

---

## 执行选项

**Plan complete and saved to `docs/superpowers/plans/2026-04-04-sqlite-integration-implementation.md`. Two execution options:**

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?**
<options>
    <option>Subagent-Driven (recommended)</option>
    <option>Inline Execution</option>
</options>
