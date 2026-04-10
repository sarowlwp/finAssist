#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FastAPI 应用入口
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path

from config import config
from routers import portfolio, settings, analysis, agents, market

# 创建 FastAPI 应用
app = FastAPI(
    title="私人投资 AI 助理 API",
    description="基于 AgentScope 的多 Agent 投资助理系统",
    version="0.1.0"
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载路由
app.include_router(portfolio.router, prefix="/api", tags=["Portfolio"])
app.include_router(settings.router, prefix="/api", tags=["Settings"])
app.include_router(analysis.router, prefix="/api", tags=["Analysis"])
app.include_router(agents.router, prefix="/api", tags=["Agents"])
app.include_router(market.router, prefix="/api", tags=["Market"])


@app.on_event("startup")
async def startup_event():
    """应用启动时初始化"""
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)

    # 初始化数据库
    from database import Base, engine, SessionLocal
    from services.finnhub_cache_service import FinnhubCacheService

    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        cache_service = FinnhubCacheService(db)
        cache_service.delete_expired_cache()
    finally:
        db.close()

    # 从持久化存储中加载用户自定义 Agent
    from storage.settings import SettingsStore
    from agents.analysis_agent import load_custom_agents_from_settings
    settings_store = SettingsStore(config.DATA_DIR)
    load_custom_agents_from_settings(settings_store)

    print("✅ Backend started successfully on port 8001")


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时清理"""
    print("👋 Backend shutting down...")


@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "私人投资 AI 助理 API",
        "version": "0.1.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=False,            # 关闭热重载，避免处理请求时重启导致 ECONNRESET
        timeout_keep_alive=300,  # 保持连接超时 5 分钟
        limit_concurrency=100,
        limit_max_requests=1000
    )