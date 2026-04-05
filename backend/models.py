from sqlalchemy import Column, Integer, String, DateTime, JSON, DECIMAL, ForeignKey
from sqlalchemy.sql import func
from database import Base
from sqlalchemy.orm import relationship


class FinnhubCache(Base):
    """
    Finnhub API 数据缓存模型

    用于存储 Finnhub API 返回的数据，避免重复请求。
    """
    __tablename__ = "finnhub_cache"

    id = Column(Integer, primary_key=True, index=True)
    cache_key = Column(String(255), unique=True, index=True, nullable=False)
    data_type = Column(String(50), nullable=False)
    ticker = Column(String(20), nullable=False)
    data = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)


class AnalysisReport(Base):
    """
    分析报告主模型

    存储完整分析报告的元数据和汇总信息。
    """
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
    """
    Agent 报告子模型

    存储各个分析 Agent 生成的详细报告。
    """
    __tablename__ = "agent_reports"

    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(String(36), ForeignKey("analysis_reports.report_id"), nullable=False)
    agent_name = Column(String(100), nullable=False)
    agent_content = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    analysis_report = relationship("AnalysisReport", back_populates="agent_reports")


class PortfolioHolding(Base):
    """
    持仓数据模型

    存储用户的股票持仓信息，包括成本价、数量、备注等。
    """
    __tablename__ = "portfolio_holdings"

    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String(20), index=True, unique=True, nullable=False)
    quantity = Column(Integer, nullable=False)
    cost_price = Column(DECIMAL(15, 4), nullable=False)
    note = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class AnalysisTask(Base):
    """
    分析任务模型

    存储分析任务的状态和元数据，支持异步任务管理。
    """
    __tablename__ = "analysis_tasks"

    task_id = Column(String(36), primary_key=True, index=True)
    ticker = Column(String(20), index=True, nullable=False)
    company_name = Column(String(255), nullable=False)
    status = Column(String(20), nullable=False, default="pending")  # pending, analyzing, completed, failed
    progress = Column(Integer, nullable=False, default=0)
    progress_message = Column(String(255), nullable=True)
    progress_stage = Column(String(50), nullable=True)
    report_id = Column(String(36), nullable=True)
    error_message = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
