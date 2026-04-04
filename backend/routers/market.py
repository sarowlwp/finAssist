"""
市场数据路由
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status

from services.finnhub_service import FinnhubService
from dependencies import get_finnhub_service

router = APIRouter()


@router.get("/market/quote/{ticker}")
async def get_quote(
    ticker: str,
    finnhub_service: Optional[FinnhubService] = Depends(get_finnhub_service)
):
    """
    获取实时报价
    
    Args:
        ticker: 股票代码
        finnhub_service: Finnhub 服务实例
    
    Returns:
        报价信息
    """
    try:
        if not finnhub_service:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Finnhub 服务未配置，请设置 FINNHUB_API_KEY"
            )
        
        quote = finnhub_service.get_quote(ticker)
        
        if not quote.get("success"):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=quote.get("error", "获取报价失败")
            )
        
        return quote
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取报价失败: {str(e)}"
        )


@router.get("/market/profile/{ticker}")
async def get_profile(
    ticker: str,
    finnhub_service: Optional[FinnhubService] = Depends(get_finnhub_service)
):
    """
    获取公司概况
    
    Args:
        ticker: 股票代码
        finnhub_service: Finnhub 服务实例
    
    Returns:
        公司信息
    """
    try:
        if not finnhub_service:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Finnhub 服务未配置，请设置 FINNHUB_API_KEY"
            )
        
        profile = finnhub_service.get_company_profile(ticker)
        
        if not profile.get("success"):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=profile.get("error", "获取公司概况失败")
            )
        
        return profile
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取公司概况失败: {str(e)}"
        )


@router.get("/market/financials/{ticker}")
async def get_financials(
    ticker: str,
    finnhub_service: Optional[FinnhubService] = Depends(get_finnhub_service)
):
    """
    获取基本面数据
    
    Args:
        ticker: 股票代码
        finnhub_service: Finnhub 服务实例
    
    Returns:
        基本面数据
    """
    try:
        if not finnhub_service:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Finnhub 服务未配置，请设置 FINNHUB_API_KEY"
            )
        
        financials = finnhub_service.get_financials(ticker)
        
        if not financials.get("success"):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=financials.get("error", "获取基本面数据失败")
            )
        
        return financials
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取基本面数据失败: {str(e)}"
        )


@router.get("/market/news/{ticker}")
async def get_news(
    ticker: str,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    finnhub_service: Optional[FinnhubService] = Depends(get_finnhub_service)
):
    """
    获取公司新闻
    
    Args:
        ticker: 股票代码
        from_date: 开始日期 (YYYY-MM-DD)，默认为7天前
        to_date: 结束日期 (YYYY-MM-DD)，默认为今天
        finnhub_service: Finnhub 服务实例
    
    Returns:
        新闻列表
    """
    try:
        if not finnhub_service:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Finnhub 服务未配置，请设置 FINNHUB_API_KEY"
            )
        
        news = finnhub_service.get_company_news(ticker, from_date, to_date)
        
        if not news.get("success"):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=news.get("error", "获取新闻失败")
            )
        
        return news
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取新闻失败: {str(e)}"
        )


@router.get("/market/technical/{ticker}")
async def get_technical(
    ticker: str,
    finnhub_service: Optional[FinnhubService] = Depends(get_finnhub_service)
):
    """
    获取技术指标
    
    Args:
        ticker: 股票代码
        finnhub_service: Finnhub 服务实例
    
    Returns:
        技术指标
    """
    try:
        if not finnhub_service:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Finnhub 服务未配置，请设置 FINNHUB_API_KEY"
            )
        
        technical = finnhub_service.get_technical_indicators(ticker)
        
        if not technical.get("success"):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=technical.get("error", "获取技术指标失败")
            )
        
        return technical
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取技术指标失败: {str(e)}"
        )
