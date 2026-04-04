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
