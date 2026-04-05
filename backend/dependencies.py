from pathlib import Path
from typing import Optional

from fastapi import Depends
from sqlalchemy.orm import Session

from config import config
from database import get_db
from services.analysis_report_repository import AnalysisReportRepository
from services.finnhub_cache_service import FinnhubCacheService
from services.finnhub_service import FinnhubService
from services.model_adapter import ModelAdapter
from storage.analysis import AnalysisStore
from storage.portfolio import PortfolioStore
from storage.settings import SettingsStore

# 全局单例实例
_settings_store: Optional[SettingsStore] = None
_analysis_store: Optional[AnalysisStore] = None
_finnhub_service: Optional[FinnhubService] = None
_model_adapter: Optional[ModelAdapter] = None
_settings_data_dir: Optional[Path] = None
_analysis_data_dir: Optional[Path] = None

def get_finnhub_cache_service(db: Session = Depends(get_db)) -> FinnhubCacheService:
    return FinnhubCacheService(db)

def get_analysis_repository(db: Session = Depends(get_db)) -> AnalysisReportRepository:
    return AnalysisReportRepository(db)

def get_analysis_store() -> AnalysisStore:
    """获取 AnalysisStore 实例"""
    global _analysis_store, _analysis_data_dir
    if _analysis_store is None or _analysis_data_dir != config.DATA_DIR:
        _analysis_store = AnalysisStore(config.DATA_DIR)
        _analysis_data_dir = config.DATA_DIR
    return _analysis_store

def get_portfolio_store(db: Session = Depends(get_db)) -> PortfolioStore:
    """获取 PortfolioStore 实例（使用数据库）"""
    return PortfolioStore(db, data_dir=config.DATA_DIR)

def get_settings_store() -> SettingsStore:
    """获取 SettingsStore 实例"""
    global _settings_store, _settings_data_dir
    if _settings_store is None or _settings_data_dir != config.DATA_DIR:
        _settings_store = SettingsStore(config.DATA_DIR)
        _settings_data_dir = config.DATA_DIR
    return _settings_store

def get_finnhub_service(db: Session = Depends(get_db)) -> Optional[FinnhubService]:
    """获取 FinnhubService 单例"""
    global _finnhub_service
    if _finnhub_service is None and config.FINNHUB_API_KEY:
        _finnhub_service = FinnhubService(config.FINNHUB_API_KEY, db)
    return _finnhub_service

def get_model_adapter() -> ModelAdapter:
    """获取 ModelAdapter 单例"""
    global _model_adapter
    if _model_adapter is None:
        _model_adapter = ModelAdapter()
    return _model_adapter
