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
