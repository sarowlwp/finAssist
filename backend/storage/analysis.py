"""
分析报告存储模块
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from pathlib import Path
import json
from datetime import datetime
from services.analysis_report_repository import AnalysisReportRepository
from models import AnalysisReport as DBReport
from models import AgentReport as DBAgentReport
from utils.json_to_markdown import json_to_markdown


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
        from dependencies import get_db
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
                content = agent.agent_content
                # 转换内容为 Markdown
                markdown_content = json_to_markdown(content)

                if agent.agent_name == "news_agent":
                    agent_reports["news_report"] = markdown_content
                elif agent.agent_name == "sec_agent":
                    agent_reports["sec_report"] = markdown_content
                elif agent.agent_name == "fundamentals_agent":
                    agent_reports["fundamentals_report"] = markdown_content
                elif agent.agent_name == "technical_agent":
                    agent_reports["technical_report"] = markdown_content
                elif agent.agent_name == "custom_skill_agent":
                    agent_reports["custom_skill_report"] = markdown_content

            # 转换 fusion summary
            fusion_summary = json_to_markdown(db_report.fusion_summary or "")

            reports.append(AnalysisReport(
                report_id=db_report.report_id,
                ticker=db_report.ticker,
                company_name=db_report.company_name,
                created_at=db_report.created_at.isoformat(),
                status=db_report.status,
                current_price=float(db_report.current_price),
                change_percent=float(db_report.change_percent),
                fusion_summary=fusion_summary,
                **agent_reports
            ))

        return reports

    def load_by_ticker(self, ticker: str) -> List[AnalysisReport]:
        all_reports = self.load_all()
        return [report for report in all_reports if report.ticker.upper() == ticker.upper()]

    def load_by_id(self, report_id: str) -> Optional[AnalysisReport]:
        from dependencies import get_db
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
                content = agent.agent_content
                # 转换内容为 Markdown
                markdown_content = json_to_markdown(content)

                if agent.agent_name == "news_agent":
                    agent_reports["news_report"] = markdown_content
                elif agent.agent_name == "sec_agent":
                    agent_reports["sec_report"] = markdown_content
                elif agent.agent_name == "fundamentals_agent":
                    agent_reports["fundamentals_report"] = markdown_content
                elif agent.agent_name == "technical_agent":
                    agent_reports["technical_report"] = markdown_content
                elif agent.agent_name == "custom_skill_agent":
                    agent_reports["custom_skill_report"] = markdown_content

            # 转换 fusion summary
            fusion_summary = json_to_markdown(db_report.fusion_summary or "")

            return AnalysisReport(
                report_id=db_report.report_id,
                ticker=db_report.ticker,
                company_name=db_report.company_name,
                created_at=db_report.created_at.isoformat(),
                status=db_report.status,
                current_price=float(db_report.current_price),
                change_percent=float(db_report.change_percent),
                fusion_summary=fusion_summary,
                **agent_reports
            )

        return None

    def save_report(self, report: AnalysisReport) -> AnalysisReport:
        from dependencies import get_db
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
        from dependencies import get_db
        db = next(get_db())
        repo = AnalysisReportRepository(db)
        return repo.delete_report(report_id)

    def delete_reports_by_ticker(self, ticker: str) -> int:
        reports = self.load_by_ticker(ticker)
        count = 0
        from dependencies import get_db
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
