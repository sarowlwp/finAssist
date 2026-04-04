"""
分析服务路由
"""
import json
import asyncio
import uuid
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from agents.orchestrator import AnalysisOrchestrator
from storage.settings import SettingsStore
from storage.analysis import AnalysisStore, AnalysisReport
from dependencies import get_settings_store, get_analysis_store, get_analysis_repository
from services.finnhub_cache_service import FinnhubCacheService
from services.analysis_report_repository import AnalysisReportRepository

router = APIRouter()

# 分析状态存储（简单内存实现，生产环境应使用数据库）
analysis_status: Dict[str, Dict[str, Any]] = {}


# Pydantic 模型
class TickerAnalysisRequest(BaseModel):
    """股票分析请求模型"""
    ticker: str = Field(..., description="股票代码")


class PortfolioAnalysisRequest(BaseModel):
    """投资组合分析请求模型"""
    tickers: Optional[List[str]] = Field(None, description="股票代码列表，为空则分析所有持仓")


class AnalysisStatus(BaseModel):
    """分析状态模型"""
    analysis_id: str = Field(..., description="分析 ID")
    status: str = Field(..., description="状态：pending, running, completed, failed")
    progress: float = Field(..., description="进度 0-100")
    result: Optional[Dict[str, Any]] = Field(None, description="分析结果")
    error: Optional[str] = Field(None, description="错误信息")


def get_orchestrator(model_config: Dict[str, Any] = None) -> AnalysisOrchestrator:
    """
    获取或创建 AnalysisOrchestrator 实例
    
    Args:
        model_config: 模型配置
    
    Returns:
        AnalysisOrchestrator 实例
    """
    # 这里可以缓存 orchestrator 实例
    return AnalysisOrchestrator(model_config=model_config)


async def run_ticker_analysis(
    analysis_id: str,
    ticker: str,
    user_settings: Dict[str, Any],
    model_config: Dict[str, Any]
):
    """
    后台执行股票分析
    
    Args:
        analysis_id: 分析 ID
        ticker: 股票代码
        user_settings: 用户设置
        model_config: 模型配置
    """
    try:
        # 更新状态为运行中
        analysis_status[analysis_id]["status"] = "running"
        analysis_status[analysis_id]["progress"] = 10.0
        
        # 创建 orchestrator
        orchestrator = get_orchestrator(model_config)
        
        # 执行分析
        analysis_status[analysis_id]["progress"] = 50.0
        result = await orchestrator.analyze_ticker(ticker, user_settings)
        
        # 更新状态为完成
        analysis_status[analysis_id]["status"] = "completed"
        analysis_status[analysis_id]["progress"] = 100.0
        analysis_status[analysis_id]["result"] = result
        
    except Exception as e:
        # 更新状态为失败
        analysis_status[analysis_id]["status"] = "failed"
        analysis_status[analysis_id]["error"] = str(e)


async def run_portfolio_analysis(
    analysis_id: str,
    tickers: List[str],
    user_settings: Dict[str, Any],
    model_config: Dict[str, Any]
):
    """
    后台执行投资组合分析
    
    Args:
        analysis_id: 分析 ID
        tickers: 股票代码列表
        user_settings: 用户设置
        model_config: 模型配置
    """
    try:
        # 更新状态为运行中
        analysis_status[analysis_id]["status"] = "running"
        analysis_status[analysis_id]["progress"] = 10.0
        
        # 创建 orchestrator
        orchestrator = get_orchestrator(model_config)
        
        # 执行分析
        analysis_status[analysis_id]["progress"] = 50.0
        results = await orchestrator.analyze_portfolio(tickers, user_settings)
        
        # 更新状态为完成
        analysis_status[analysis_id]["status"] = "completed"
        analysis_status[analysis_id]["progress"] = 100.0
        analysis_status[analysis_id]["result"] = {
            "reports": results,
            "count": len(results)
        }
        
    except Exception as e:
        # 更新状态为失败
        analysis_status[analysis_id]["status"] = "failed"
        analysis_status[analysis_id]["error"] = str(e)


@router.post("/analysis/ticker", response_model=AnalysisStatus, status_code=status.HTTP_202_ACCEPTED)
async def analyze_ticker(
    request: TickerAnalysisRequest,
    background_tasks: BackgroundTasks,
    settings_store: SettingsStore = Depends(get_settings_store)
):
    """
    分析单个股票
    
    Args:
        request: 分析请求
        background_tasks: 后台任务
        settings_store: 设置存储
    
    Returns:
        分析状态
    """
    try:
        # 生成分析 ID
        import uuid
        analysis_id = str(uuid.uuid4())
        
        # 获取用户设置
        settings = settings_store.load()
        user_settings = {
            "investment_style": settings.investment_style,
            "ticker_notes": {},
            "skills": [],
            "agent_skills": settings.agent_skills or {},
        }
        llm_cfg = settings.llm_config
        
        # 初始化状态
        analysis_status[analysis_id] = {
            "analysis_id": analysis_id,
            "status": "pending",
            "progress": 0.0,
            "result": None,
            "error": None,
            "ticker": request.ticker
        }
        
        # 添加后台任务
        background_tasks.add_task(
            run_ticker_analysis,
            analysis_id,
            request.ticker,
            user_settings,
            llm_cfg
        )
        
        return AnalysisStatus(**analysis_status[analysis_id])
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"启动分析失败: {str(e)}"
        )


@router.post("/analysis/portfolio", response_model=AnalysisStatus, status_code=status.HTTP_202_ACCEPTED)
async def analyze_portfolio(
    request: PortfolioAnalysisRequest,
    background_tasks: BackgroundTasks,
    settings_store: SettingsStore = Depends(get_settings_store)
):
    """
    分析整个持仓
    
    Args:
        request: 分析请求
        background_tasks: 后台任务
        settings_store: 设置存储
    
    Returns:
        分析状态
    """
    try:
        # 如果没有指定 tickers，从持仓中获取
        if not request.tickers:
            from storage.portfolio import PortfolioStore
            from dependencies import get_portfolio_store
            portfolio_store = get_portfolio_store()
            holdings = portfolio_store.get_all()
            request.tickers = [h.ticker for h in holdings]
        
        if not request.tickers:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="没有可分析的持仓"
            )
        
        # 生成分析 ID
        import uuid
        analysis_id = str(uuid.uuid4())
        
        # 获取用户设置
        settings = settings_store.load()
        user_settings = {
            "investment_style": settings.investment_style,
            "ticker_notes": {},
            "skills": [],
            "agent_skills": settings.agent_skills or {},
        }
        llm_cfg = settings.llm_config
        
        # 初始化状态
        analysis_status[analysis_id] = {
            "analysis_id": analysis_id,
            "status": "pending",
            "progress": 0.0,
            "result": None,
            "error": None,
            "tickers": request.tickers
        }
        
        # 添加后台任务
        background_tasks.add_task(
            run_portfolio_analysis,
            analysis_id,
            request.tickers,
            user_settings,
            llm_cfg
        )
        
        return AnalysisStatus(**analysis_status[analysis_id])
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"启动分析失败: {str(e)}"
        )


@router.get("/analysis/status/{analysis_id}", response_model=AnalysisStatus)
async def get_analysis_status(analysis_id: str):
    """
    获取分析状态
    
    Args:
        analysis_id: 分析 ID
    
    Returns:
        分析状态
    """
    try:
        if analysis_id not in analysis_status:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"未找到分析: {analysis_id}"
            )
        
        return AnalysisStatus(**analysis_status[analysis_id])
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取分析状态失败: {str(e)}"
        )


@router.post("/analysis/ticker/stream")
async def analyze_ticker_stream(
    request: TickerAnalysisRequest,
    settings_store: SettingsStore = Depends(get_settings_store),
    analysis_store: AnalysisStore = Depends(get_analysis_store)
):
    """
    流式分析单个股票 (Server-Sent Events)
    
    使用 asyncio.Queue 实现实时进度推送，每个 Agent 完成时立即发送中间结果。
    
    Args:
        request: 分析请求
        settings_store: 设置存储
    
    Returns:
        StreamingResponse (SSE)
    """
    async def event_generator():
        progress_queue: asyncio.Queue = asyncio.Queue()
        report_id = str(uuid.uuid4())

        import logging
        logger = logging.getLogger("analysis_stream")

        try:
            # 发送初始状态
            yield f"data: {json.dumps({'type': 'start', 'ticker': request.ticker, 'progress': 0, 'message': '开始分析...'})}\n\n"
            
            # 获取用户设置
            settings = settings_store.load()
            user_settings = {
                "investment_style": settings.investment_style,
                "ticker_notes": {},
                "skills": [],
                "agent_skills": settings.agent_skills or {},
            }
            llm_cfg = settings.llm_config
            
            # 创建 orchestrator
            orchestrator = get_orchestrator(llm_cfg)
            
            import logging
            logger = logging.getLogger("analysis_stream")
            
            # 进度回调：直接往 Queue 中放消息，不阻塞
            def progress_callback(stage: str, message: str, progress: float, agent_name: str = None, agent_content: str = None):
                event = {
                    "type": "progress",
                    "stage": stage,
                    "message": message,
                    "progress": progress
                }
                if agent_name:
                    event["agent_name"] = agent_name
                if agent_content:
                    # 截断过长的 agent_content 避免 SSE 单条消息过大
                    event["agent_content"] = agent_content[:50000] if len(agent_content) > 50000 else agent_content
                logger.info(f"[SSE] progress_callback: stage={stage}, progress={progress}, agent_name={agent_name}, content_len={len(agent_content) if agent_content else 0}")
                try:
                    progress_queue.put_nowait(event)
                except Exception as e:
                    logger.error(f"[SSE] put_nowait 失败: {e}")
            
            result = None
            error = None
            
            async def run_analysis():
                nonlocal result, error
                try:
                    logger.info(f"[SSE] 开始分析 {request.ticker}")
                    result = await orchestrator.analyze_ticker(
                        request.ticker, 
                        user_settings,
                        progress_callback=progress_callback
                    )
                    logger.info(f"[SSE] 分析完成，result keys: {list(result.keys()) if result else 'None'}")
                except Exception as e:
                    logger.exception(f"[SSE] 分析异常: {e}")
                    error = str(e)
                finally:
                    # 放入哨兵值表示分析结束
                    await progress_queue.put(None)
                    logger.info("[SSE] 哨兵值已放入 Queue")
            
            # 启动分析任务
            analysis_task = asyncio.create_task(run_analysis())
            
            # 从 Queue 中持续读取并发送进度事件
            while True:
                try:
                    msg = await asyncio.wait_for(progress_queue.get(), timeout=0.5)
                except asyncio.TimeoutError:
                    # 超时时检查任务是否已结束（防止哨兵丢失）
                    if analysis_task.done():
                        break
                    continue
                
                if msg is None:
                    # 哨兵值，分析已结束
                    break
                
                try:
                    yield f"data: {json.dumps(msg, ensure_ascii=False)}\n\n"
                except Exception as e:
                    logger.error(f"[SSE] JSON 序列化进度消息失败: {e}")
                    # 发送不含 agent_content 的简化消息
                    safe_msg = {k: v for k, v in msg.items() if k != 'agent_content'}
                    yield f"data: {json.dumps(safe_msg, ensure_ascii=False)}\n\n"
            
            # 排空队列中剩余的消息
            while not progress_queue.empty():
                msg = progress_queue.get_nowait()
                if msg is not None:
                    try:
                        yield f"data: {json.dumps(msg, ensure_ascii=False)}\n\n"
                    except Exception as e:
                        logger.error(f"[SSE] JSON 序列化剩余消息失败: {e}")
            
            # 发送最终结果：分拆为多条小消息，避免单条 SSE 过大
            if error:
                yield f"data: {json.dumps({'type': 'error', 'message': error}, ensure_ascii=False)}\n\n"
            elif result:
                try:
                    # 保存分析报告
                    try:
                        # 从result中提取各个agent的输出
                        agent_outputs = result.get('agent_outputs', {})
                        metadata = result.get('metadata', {})
                        quote_data = metadata.get('quote', {})

                        report = AnalysisReport(
                            report_id=report_id,
                            ticker=request.ticker,
                            company_name=metadata.get('company_name', request.ticker),
                            status='completed',
                            current_price=quote_data.get('current_price', 0),
                            change_percent=quote_data.get('change_percent', 0),
                            fusion_summary=result.get('fusion_output', ''),
                            news_report=agent_outputs.get('news_agent', ''),
                            sec_report=agent_outputs.get('sec_agent', ''),
                            fundamentals_report=agent_outputs.get('fundamentals_agent', ''),
                            technical_report=agent_outputs.get('technical_agent', ''),
                            custom_skill_report=agent_outputs.get('custom_skill_agent', '')
                        )
                        analysis_store.save_report(report)
                        logger.info(f"分析报告已保存: {report_id}")
                    except Exception as save_err:
                        logger.error(f"保存分析报告失败: {save_err}")

                    # 先逐个发送各 Agent 的输出
                    agent_outputs = result.get('agent_outputs', {})
                    for agent_name, agent_content in agent_outputs.items():
                        yield f"data: {json.dumps({'type': 'agent_result', 'agent_name': agent_name, 'agent_content': agent_content}, ensure_ascii=False)}\n\n"
                    
                    # 再发送 fusion 输出
                    yield f"data: {json.dumps({'type': 'fusion_result', 'fusion_output': result.get('fusion_output', '')}, ensure_ascii=False)}\n\n"
                    
                    # 最后发送 complete 信号（不含大文本，只含元数据）
                    complete_data = {
                        'type': 'complete',
                        'progress': 100,
                        'ticker': result.get('ticker', ''),
                        'investment_style': result.get('investment_style', ''),
                        'metadata': result.get('metadata', {}),
                        'report_id': report_id
                    }
                    yield f"data: {json.dumps(complete_data, ensure_ascii=False)}\n\n"
                except Exception as e:
                    logger.exception(f"[SSE] 发送最终结果失败: {e}")
                    yield f"data: {json.dumps({'type': 'error', 'message': f'结果序列化失败: {str(e)}'}, ensure_ascii=False)}\n\n"
            else:
                yield f"data: {json.dumps({'type': 'complete', 'progress': 100}, ensure_ascii=False)}\n\n"
                
        except Exception as e:
            logger.exception(f"[SSE] event_generator 异常: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.get("/analysis/reports", response_model=List[AnalysisReport])
async def get_analysis_reports(
    ticker: Optional[str] = None,
    limit: int = 20,
    analysis_store: AnalysisStore = Depends(get_analysis_store)
):
    """
    获取分析报告列表

    Args:
        ticker: 可选的股票代码，为空则返回所有报告
        limit: 返回的报告数量限制
        analysis_store: 分析报告存储

    Returns:
        分析报告列表
    """
    try:
        if ticker:
            reports = analysis_store.load_by_ticker(ticker)
        else:
            reports = analysis_store.get_recent_reports(limit)

        return reports
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取分析报告失败: {str(e)}"
        )


@router.get("/analysis/reports/{report_id}", response_model=AnalysisReport)
async def get_analysis_report(
    report_id: str,
    analysis_store: AnalysisStore = Depends(get_analysis_store)
):
    """
    获取单个分析报告详情

    Args:
        report_id: 报告ID
        analysis_store: 分析报告存储

    Returns:
        分析报告详情
    """
    try:
        report = analysis_store.load_by_id(report_id)
        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"未找到报告: {report_id}"
            )
        return report
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取分析报告失败: {str(e)}"
        )


@router.delete("/analysis/reports/{report_id}")
async def delete_analysis_report(
    report_id: str,
    analysis_store: AnalysisStore = Depends(get_analysis_store)
):
    """
    删除分析报告

    Args:
        report_id: 报告ID
        analysis_store: 分析报告存储

    Returns:
        删除结果
    """
    try:
        deleted = analysis_store.delete_report(report_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"未找到报告: {report_id}"
            )
        return {"success": True, "message": "报告已删除"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除分析报告失败: {str(e)}"
        )
