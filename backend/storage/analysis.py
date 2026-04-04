"""
分析报告存储模块
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from pathlib import Path
import json
from datetime import datetime


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
        self.analysis_file = data_dir / "analysis_reports.json"
        self._ensure_file_exists()

    def _ensure_file_exists(self) -> None:
        """确保数据文件存在"""
        if not self.analysis_file.exists():
            self._write_file([])

    def _write_file(self, data: List[Dict[str, Any]]) -> None:
        """写入文件"""
        self.analysis_file.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

    def _read_file(self) -> List[Dict[str, Any]]:
        """读取文件"""
        try:
            content = self.analysis_file.read_text(encoding="utf-8")
            return json.loads(content) if content else []
        except Exception as e:
            print(f"Error reading analysis file: {e}")
            return []

    def load_all(self) -> List[AnalysisReport]:
        """加载所有分析报告"""
        data = self._read_file()
        return [AnalysisReport(**report) for report in data]

    def load_by_ticker(self, ticker: str) -> List[AnalysisReport]:
        """根据股票代码加载分析报告"""
        all_reports = self.load_all()
        return [report for report in all_reports if report.ticker.upper() == ticker.upper()]

    def load_by_id(self, report_id: str) -> Optional[AnalysisReport]:
        """根据报告ID加载分析报告"""
        all_reports = self.load_all()
        return next((report for report in all_reports if report.report_id == report_id), None)

    def save_report(self, report: AnalysisReport) -> AnalysisReport:
        """保存分析报告"""
        all_reports = self.load_all()

        # 检查是否已存在相同ID的报告
        existing_index = next(
            (i for i, existing in enumerate(all_reports) if existing.report_id == report.report_id),
            None
        )

        if existing_index is not None:
            # 更新现有报告
            all_reports[existing_index] = report
        else:
            # 添加新报告
            all_reports.append(report)

        # 按创建时间降序排序
        sorted_reports = sorted(
            all_reports,
            key=lambda x: datetime.fromisoformat(x.created_at),
            reverse=True
        )

        # 限制存储报告数量（保留最近20条）
        if len(sorted_reports) > 20:
            sorted_reports = sorted_reports[:20]

        self._write_file([report.model_dump() for report in sorted_reports])
        return report

    def delete_report(self, report_id: str) -> bool:
        """删除分析报告"""
        all_reports = self.load_all()
        original_length = len(all_reports)
        filtered_reports = [report for report in all_reports if report.report_id != report_id]

        if len(filtered_reports) < original_length:
            self._write_file([report.model_dump() for report in filtered_reports])
            return True
        return False

    def delete_reports_by_ticker(self, ticker: str) -> int:
        """删除指定股票代码的所有分析报告"""
        all_reports = self.load_all()
        original_length = len(all_reports)
        filtered_reports = [report for report in all_reports if report.ticker.upper() != ticker.upper()]

        if len(filtered_reports) < original_length:
            self._write_file([report.model_dump() for report in filtered_reports])
            return original_length - len(filtered_reports)
        return 0

    def get_recent_reports(self, limit: int = 10) -> List[AnalysisReport]:
        """获取最近的分析报告"""
        all_reports = self.load_all()
        sorted_reports = sorted(
            all_reports,
            key=lambda x: datetime.fromisoformat(x.created_at),
            reverse=True
        )
        return sorted_reports[:limit]
