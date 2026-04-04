"""
依赖注入模块
使用 FastAPI Depends 管理全局依赖
"""
from typing import Optional
from storage.portfolio import PortfolioStore
from storage.settings import SettingsStore
from storage.analysis import AnalysisStore
from services.finnhub_service import FinnhubService
from services.model_adapter import ModelAdapter
from config import config
from pathlib import Path

# 全局单例实例
_portfolio_store: Optional[PortfolioStore] = None
_settings_store: Optional[SettingsStore] = None
_analysis_store: Optional[AnalysisStore] = None
_finnhub_service: Optional[FinnhubService] = None
_model_adapter: Optional[ModelAdapter] = None
_last_data_dir: Optional[Path] = None

def get_portfolio_store() -> PortfolioStore:
    """获取 PortfolioStore 实例"""
    global _portfolio_store, _last_data_dir
    if _portfolio_store is None or _last_data_dir != config.DATA_DIR:
        _portfolio_store = PortfolioStore(config.DATA_DIR)
        _last_data_dir = config.DATA_DIR
    return _portfolio_store

def get_settings_store() -> SettingsStore:
    """获取 SettingsStore 实例"""
    global _settings_store, _last_data_dir
    if _settings_store is None or _last_data_dir != config.DATA_DIR:
        _settings_store = SettingsStore(config.DATA_DIR)
        _last_data_dir = config.DATA_DIR
    return _settings_store

def get_analysis_store() -> AnalysisStore:
    """获取 AnalysisStore 实例"""
    global _analysis_store, _last_data_dir
    if _analysis_store is None or _last_data_dir != config.DATA_DIR:
        _analysis_store = AnalysisStore(config.DATA_DIR)
        _last_data_dir = config.DATA_DIR
    return _analysis_store

def get_finnhub_service() -> Optional[FinnhubService]:
    """获取 FinnhubService 单例"""
    global _finnhub_service
    if _finnhub_service is None and config.FINNHUB_API_KEY:
        _finnhub_service = FinnhubService(config.FINNHUB_API_KEY)
    return _finnhub_service

def get_model_adapter() -> ModelAdapter:
    """获取 ModelAdapter 单例"""
    global _model_adapter
    if _model_adapter is None:
        _model_adapter = ModelAdapter()
    return _model_adapter
