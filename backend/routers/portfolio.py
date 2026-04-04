"""
持仓管理路由
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from storage.portfolio import PortfolioStore, PortfolioItem
from services.finnhub_service import FinnhubService
from dependencies import get_portfolio_store, get_finnhub_service

router = APIRouter()


# Pydantic 模型
class PortfolioCreate(BaseModel):
    """创建持仓请求模型"""
    ticker: str = Field(..., description="股票代码")
    quantity: int = Field(..., gt=0, description="持仓数量")
    cost_price: float = Field(..., gt=0, description="成本价")
    note: Optional[str] = Field(None, description="备注")


class PortfolioUpdate(BaseModel):
    """更新持仓请求模型"""
    quantity: Optional[int] = Field(None, gt=0, description="持仓数量")
    cost_price: Optional[float] = Field(None, gt=0, description="成本价")
    note: Optional[str] = Field(None, description="备注")


class PortfolioSummary(BaseModel):
    """持仓汇总模型"""
    total_market_value: float = Field(..., description="总市值")
    total_cost: float = Field(..., description="总成本")
    total_profit_loss: float = Field(..., description="总盈亏")
    total_profit_loss_percent: float = Field(..., description="总盈亏百分比")
    holdings_count: int = Field(..., description="持仓数量")
    holdings: List[dict] = Field(..., description="持仓详情")


@router.get("/portfolio")
async def get_all_portfolio(
    portfolio_store: PortfolioStore = Depends(get_portfolio_store),
    finnhub_service: Optional[FinnhubService] = Depends(get_finnhub_service)
):
    """
    获取所有持仓（包含实时价格和盈亏计算）
    
    Returns:
        持仓列表（含计算字段）
    """
    try:
        holdings = portfolio_store.get_all()
        result = []
        
        for holding in holdings:
            # 获取当前价格
            current_price = 0.0
            if finnhub_service:
                quote = finnhub_service.get_quote(holding.ticker)
                if quote.get("success"):
                    current_price = quote.get("current_price", 0.0)
            
            cost = holding.quantity * holding.cost_price
            market_value = holding.quantity * current_price
            profit_loss = market_value - cost
            profit_loss_percent = (profit_loss / cost * 100) if cost > 0 else 0.0
            
            result.append({
                "ticker": holding.ticker,
                "quantity": holding.quantity,
                "cost_price": holding.cost_price,
                "current_price": current_price,
                "market_value": market_value,
                "total_cost": cost,
                "profit_loss": profit_loss,
                "profit_loss_percent": profit_loss_percent,
                "note": holding.note,
                "created_at": holding.created_at,
                "updated_at": holding.updated_at
            })
        
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取持仓失败: {str(e)}"
        )

@router.get("/portfolio/summary", response_model=PortfolioSummary)
async def get_portfolio_summary(
    portfolio_store: PortfolioStore = Depends(get_portfolio_store),
    finnhub_service: Optional[FinnhubService] = Depends(get_finnhub_service)
):
    """
    获取持仓汇总
    
    Returns:
        持仓汇总信息
    """
    try:
        holdings = portfolio_store.get_all()
        
        if not holdings:
            return PortfolioSummary(
                total_market_value=0.0,
                total_cost=0.0,
                total_profit_loss=0.0,
                total_profit_loss_percent=0.0,
                holdings_count=0,
                holdings=[]
            )
        
        total_cost = 0.0
        total_market_value = 0.0
        holdings_detail = []
        
        for holding in holdings:
            cost = holding.quantity * holding.cost_price
            total_cost += cost
            
            # 获取当前价格
            current_price = 0.0
            if finnhub_service:
                quote = finnhub_service.get_quote(holding.ticker)
                if quote.get("success"):
                    current_price = quote.get("current_price", 0.0)
            
            market_value = holding.quantity * current_price
            total_market_value += market_value
            
            profit_loss = market_value - cost
            profit_loss_percent = (profit_loss / cost * 100) if cost > 0 else 0.0
            
            holdings_detail.append({
                "ticker": holding.ticker,
                "quantity": holding.quantity,
                "cost_price": holding.cost_price,
                "current_price": current_price,
                "market_value": market_value,
                "cost": cost,
                "profit_loss": profit_loss,
                "profit_loss_percent": profit_loss_percent,
                "note": holding.note
            })
        
        total_profit_loss = total_market_value - total_cost
        total_profit_loss_percent = (total_profit_loss / total_cost * 100) if total_cost > 0 else 0.0
        
        return PortfolioSummary(
            total_market_value=round(total_market_value, 2),
            total_cost=round(total_cost, 2),
            total_profit_loss=round(total_profit_loss, 2),
            total_profit_loss_percent=round(total_profit_loss_percent, 2),
            holdings_count=len(holdings),
            holdings=holdings_detail
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取持仓汇总失败: {str(e)}"
        )

@router.post("/portfolio", response_model=PortfolioItem, status_code=status.HTTP_201_CREATED)
async def add_portfolio_item(
    item: PortfolioCreate,
    portfolio_store: PortfolioStore = Depends(get_portfolio_store)
):
    """
    添加持仓
    
    Args:
        item: 持仓信息
    
    Returns:
        添加后的持仓
    """
    try:
        portfolio_item = PortfolioItem(**item.model_dump())
        result = portfolio_store.add_item(portfolio_item)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"添加持仓失败: {str(e)}"
        )

@router.put("/portfolio/{ticker}", response_model=PortfolioItem)
async def update_portfolio_item(
    ticker: str,
    item: PortfolioUpdate,
    portfolio_store: PortfolioStore = Depends(get_portfolio_store)
):
    """
    更新持仓
    
    Args:
        ticker: 股票代码
        item: 更新的持仓信息
    
    Returns:
        更新后的持仓
    """
    try:
        # 检查持仓是否存在
        existing = portfolio_store.get_by_ticker(ticker)
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"未找到持仓: {ticker}"
            )
        
        # 更新持仓
        update_data = item.model_dump(exclude_unset=True)
        result = portfolio_store.update_item(ticker, **update_data)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="更新持仓失败"
            )
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新持仓失败: {str(e)}"
        )

@router.get("/portfolio/{ticker}", response_model=PortfolioItem)
async def get_portfolio_item(
    ticker: str,
    portfolio_store: PortfolioStore = Depends(get_portfolio_store)
):
    """
    获取单个持仓
    
    Args:
        ticker: 股票代码
    
    Returns:
        持仓详情
    """
    try:
        item = portfolio_store.get_by_ticker(ticker)
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"未找到持仓: {ticker}"
            )
        return item
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取持仓失败: {str(e)}"
        )

@router.delete("/portfolio/{ticker}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_portfolio_item(
    ticker: str,
    portfolio_store: PortfolioStore = Depends(get_portfolio_store)
):
    """
    删除持仓
    
    Args:
        ticker: 股票代码
    """
    try:
        success = portfolio_store.remove_item(ticker)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"未找到持仓: {ticker}"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除持仓失败: {str(e)}"
        )