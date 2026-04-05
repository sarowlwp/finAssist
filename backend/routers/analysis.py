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
from sqlalchemy.orm import Session

from agents.orchestrator import AnalysisOrchestrator
from storage.settings import SettingsStore
from storage.analysis import AnalysisStore, AnalysisReport
from dependencies import get_settings_store, get_analysis_store, get_analysis_repository, get_db
from services.finnhub_cache_service import FinnhubCacheService
from services.analysis_report_repository import AnalysisReportRepository
from models import AnalysisTask

router = APIRouter()


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


class AnalysisTaskStatus(BaseModel):
    """分析任务状态模型"""
    task_id: str = Field(..., description="任务 ID")
    ticker: str = Field(..., description="股票代码")
    company_name: str = Field(..., description="公司名称")
    status: str = Field(..., description="状态：pending, analyzing, completed, failed")
    progress: int = Field(..., description="进度 0-100")
    progress_message: Optional[str] = Field(None, description="进度消息")
    progress_stage: Optional[str] = Field(None, description="进度阶段")
    report_id: Optional[str] = Field(None, description="关联的报告 ID")
    error_message: Optional[str] = Field(None, description="错误信息")
    created_at: str = Field(..., description="创建时间")
    updated_at: str = Field(..., description="更新时间")


class StartAnalysisResponse(BaseModel):
    """启动分析响应模型"""
    success: bool = Field(..., description="是否成功")
    task_id: str = Field(..., description="任务 ID")
    ticker: str = Field(..., description="股票代码")
    message: str = Field(..., description="消息")


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


def create_analysis_task(db: Session, ticker: str, company_name: str) -> AnalysisTask:
    """创建分析任务记录"""
    task_id = str(uuid.uuid4())
    task = AnalysisTask(
        task_id=task_id,
        ticker=ticker,
        company_name=company_name,
        status="pending",
        progress=0,
        progress_message="准备中..."
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def update_task_status(
    db: Session,
    task_id: str,
    status: Optional[str] = None,
    progress: Optional[int] = None,
    progress_message: Optional[str] = None,
    progress_stage: Optional[str] = None,
    report_id: Optional[str] = None,
    error_message: Optional[str] = None
):
    """更新任务状态"""
    task = db.query(AnalysisTask).filter(AnalysisTask.task_id == task_id).first()
    if task:
        if status:
            task.status = status
        if progress is not None:
            task.progress = progress
        if progress_message:
            task.progress_message = progress_message
        if progress_stage:
            task.progress_stage = progress_stage
        if report_id:
            task.report_id = report_id
        if error_message:
            task.error_message = error_message
        db.commit()
        db.refresh(task)
    return task


async def run_ticker_analysis(
    task_id: str,
    ticker: str,
    user_settings: Dict[str, Any],
    model_config: Dict[str, Any],
    db: Session
):
    """
    后台执行股票分析

    Args:
        task_id: 任务 ID
        ticker: 股票代码
        user_settings: 用户设置
        model_config: 模型配置
        db: 数据库会话
    """
    try:
        # 更新状态为分析中
        update_task_status(db, task_id, status="analyzing", progress=10, progress_message="开始分析...")

        # 创建 orchestrator
        orchestrator = get_orchestrator(model_config)

        # 进度回调
        def progress_callback(stage: str, message: str, progress: float, agent_name: str = None, agent_content: str = None):
            update_task_status(
                db,
                task_id,
                progress=int(progress),
                progress_message=message,
                progress_stage=stage
            )

        # 执行分析
        update_task_status(db, task_id, progress=30, progress_message="正在分析...")
        result = await orchestrator.analyze_ticker(ticker, user_settings, progress_callback=progress_callback)

        # 保存分析报告
        report_id = str(uuid.uuid4())
        agent_outputs = result.get('agent_outputs', {})
        metadata = result.get('metadata', {})
        quote_data = metadata.get('quote', {})

        # 转换所有报告为 Markdown
        from utils.json_to_markdown import json_to_markdown
        report = AnalysisReport(
            report_id=report_id,
            ticker=ticker,
            company_name=metadata.get('company_name', ticker),
            status='completed',
            current_price=quote_data.get('current_price', 0),
            change_percent=quote_data.get('change_percent', 0),
            fusion_summary=json_to_markdown(result.get('fusion_output', '')),
            news_report=json_to_markdown(agent_outputs.get('news_agent', '')),
            sec_report=json_to_markdown(agent_outputs.get('sec_agent', '')),
            fundamentals_report=json_to_markdown(agent_outputs.get('fundamentals_agent', '')),
            technical_report=json_to_markdown(agent_outputs.get('technical_agent', '')),
            custom_skill_report=json_to_markdown(agent_outputs.get('custom_skill_agent', ''))
        )

        # 这里需要获取 analysis_store 来保存报告
        from storage.analysis import AnalysisStore
        from dependencies import get_analysis_store
        analysis_store = get_analysis_store()
        analysis_store.save_report(report)

        # 更新任务状态为完成
        update_task_status(
            db,
            task_id,
            status="completed",
            progress=100,
            progress_message="分析完成",
            report_id=report_id
        )

    except Exception as e:
        # 更新状态为失败
        error_msg = str(e)
        update_task_status(db, task_id, status="failed", error_message=error_msg, progress_message=f"分析失败: {error_msg}")


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


@router.post("/analysis/ticker/start", response_model=StartAnalysisResponse, status_code=status.HTTP_202_ACCEPTED)
async def start_ticker_analysis(
    request: TickerAnalysisRequest,
    background_tasks: BackgroundTasks,
    settings_store: SettingsStore = Depends(get_settings_store),
    db: Session = Depends(get_db)
):
    """
    启动单个股票的异步分析任务

    Args:
        request: 分析请求
        background_tasks: 后台任务
        settings_store: 设置存储
        db: 数据库会话

    Returns:
        启动响应，包含任务 ID
    """
    try:
        # 获取公司名称
        company_name = request.ticker
        try:
            from services.finnhub_service import FinnhubService
            from dependencies import get_finnhub_service
            finnhub_service = get_finnhub_service(db)
            if finnhub_service:
                profile = finnhub_service.get_company_profile(request.ticker)
                if profile.get('success'):
                    company_name = profile.get('company_name', request.ticker)
        except Exception:
            pass

        # 创建任务记录
        task = create_analysis_task(db, request.ticker, company_name)

        # 获取用户设置
        settings = settings_store.load()
        user_settings = {
            "investment_style": settings.investment_style,
            "ticker_notes": {},
            "skills": [],
            "agent_skills": settings.agent_skills or {},
        }
        llm_cfg = settings.llm_config

        # 添加后台任务
        background_tasks.add_task(
            run_ticker_analysis,
            task.task_id,
            request.ticker,
            user_settings,
            llm_cfg,
            db
        )

        return StartAnalysisResponse(
            success=True,
            task_id=task.task_id,
            ticker=request.ticker,
            message=f"分析任务已启动，任务ID: {task.task_id}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"启动分析失败: {str(e)}"
        )


@router.get("/analysis/tasks", response_model=List[AnalysisTaskStatus])
async def get_analysis_tasks(
    ticker: Optional[str] = None,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """
    获取分析任务列表

    Args:
        ticker: 可选的股票代码过滤
        limit: 返回数量限制
        db: 数据库会话

    Returns:
        任务状态列表
    """
    query = db.query(AnalysisTask)
    if ticker:
        query = query.filter(AnalysisTask.ticker == ticker)
    tasks = query.order_by(AnalysisTask.created_at.desc()).limit(limit).all()

    return [
        AnalysisTaskStatus(
            task_id=task.task_id,
            ticker=task.ticker,
            company_name=task.company_name,
            status=task.status,
            progress=task.progress,
            progress_message=task.progress_message,
            progress_stage=task.progress_stage,
            report_id=task.report_id,
            error_message=task.error_message,
            created_at=task.created_at.isoformat() if task.created_at else "",
            updated_at=task.updated_at.isoformat() if task.updated_at else ""
        )
        for task in tasks
    ]


@router.get("/analysis/tasks/{task_id}", response_model=AnalysisTaskStatus)
async def get_analysis_task(
    task_id: str,
    db: Session = Depends(get_db)
):
    """
    获取单个分析任务状态

    Args:
        task_id: 任务 ID
        db: 数据库会话

    Returns:
        任务状态
    """
    task = db.query(AnalysisTask).filter(AnalysisTask.task_id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"未找到任务: {task_id}"
        )

    return AnalysisTaskStatus(
        task_id=task.task_id,
        ticker=task.ticker,
        company_name=task.company_name,
        status=task.status,
        progress=task.progress,
        progress_message=task.progress_message,
        progress_stage=task.progress_stage,
        report_id=task.report_id,
        error_message=task.error_message,
        created_at=task.created_at.isoformat() if task.created_at else "",
        updated_at=task.updated_at.isoformat() if task.updated_at else ""
    )


@router.post("/analysis/ticker", response_model=AnalysisStatus, status_code=status.HTTP_202_ACCEPTED)
async def analyze_ticker(
    request: TickerAnalysisRequest,
    background_tasks: BackgroundTasks,
    settings_store: SettingsStore = Depends(get_settings_store)
):
    """
    分析单个股票（兼容旧接口）

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

        # 初始化状态（内存中）
        from typing import Dict, Any
        analysis_status: Dict[str, Dict[str, Any]] = {}
        analysis_status[analysis_id] = {
            "analysis_id": analysis_id,
            "status": "pending",
            "progress": 0.0,
            "result": None,
            "error": None,
            "ticker": request.ticker
        }

        # 简单的后台任务（兼容旧版本）
        async def legacy_run_analysis():
            try:
                analysis_status[analysis_id]["status"] = "running"
                analysis_status[analysis_id]["progress"] = 100.0
                analysis_status[analysis_id]["status"] = "completed"
            except Exception as e:
                analysis_status[analysis_id]["status"] = "failed"
                analysis_status[analysis_id]["error"] = str(e)

        background_tasks.add_task(legacy_run_analysis)

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
                            fusion_summary=json_to_markdown(result.get('fusion_output', '')),
                            news_report=json_to_markdown(agent_outputs.get('news_agent', '')),
                            sec_report=json_to_markdown(agent_outputs.get('sec_agent', '')),
                            fundamentals_report=json_to_markdown(agent_outputs.get('fundamentals_agent', '')),
                            technical_report=json_to_markdown(agent_outputs.get('technical_agent', '')),
                            custom_skill_report=json_to_markdown(agent_outputs.get('custom_skill_agent', ''))
                        )
                        analysis_store.save_report(report)
                        logger.info(f"分析报告已保存: {report_id}")
                    except Exception as save_err:
                        logger.error(f"保存分析报告失败: {save_err}")

                    # 先逐个发送各 Agent 的输出
                    agent_outputs = result.get('agent_outputs', {})
                    for agent_name, agent_content in agent_outputs.items():
                        yield f"data: {json.dumps({'type': 'agent_result', 'agent_name': agent_name, 'agent_content': agent_content}, ensure_ascii=False)}\n\n"
                    
                    # 再发送 fusion 输出 - 转换为 Markdown
                    from utils.json_to_markdown import json_to_markdown
                    fusion_output = result.get('fusion_output', '')
                    fusion_markdown = json_to_markdown(fusion_output)
                    yield f"data: {json.dumps({'type': 'fusion_result', 'fusion_output': fusion_markdown}, ensure_ascii=False)}\n\n"
                    
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
