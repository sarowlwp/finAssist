"""
持仓数据存储模块
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from pathlib import Path
import json
from datetime import datetime


class PortfolioItem(BaseModel):
    """持仓项模型"""
    ticker: str = Field(..., description="股票代码")
    quantity: int = Field(..., gt=0, description="持仓数量")
    cost_price: float = Field(..., gt=0, description="成本价")
    note: Optional[str] = Field(None, description="备注")
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat(), description="创建时间")
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat(), description="更新时间")
    


class PortfolioStore:
    """持仓存储类"""
    
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.portfolio_file = data_dir / "portfolio.json"
        self._ensure_file_exists()
    
    def _ensure_file_exists(self) -> None:
        """确保数据文件存在"""
        if not self.portfolio_file.exists():
            self._save_initial_data()
    
    def _save_initial_data(self) -> None:
        """保存初始示例数据"""
        initial_data = [
            PortfolioItem(ticker="AAPL", quantity=10, cost_price=150.0, note="长期持有").model_dump(),
            PortfolioItem(ticker="NVDA", quantity=5, cost_price=800.0, note="AI 赛道").model_dump(),
            PortfolioItem(ticker="TSLA", quantity=3, cost_price=200.0, note="电动车").model_dump()
        ]
        self._write_file(initial_data)
    
    def _write_file(self, data: List[Dict[str, Any]]) -> None:
        """写入文件"""
        self.portfolio_file.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
    
    def _read_file(self) -> List[Dict[str, Any]]:
        """读取文件"""
        try:
            content = self.portfolio_file.read_text(encoding="utf-8")
            return json.loads(content) if content else []
        except Exception as e:
            print(f"Error reading portfolio file: {e}")
            return []
    
    def load(self) -> List[PortfolioItem]:
        """加载所有持仓"""
        data = self._read_file()
        return [PortfolioItem(**item) for item in data]
    
    def save(self, items: List[PortfolioItem]) -> None:
        """保存所有持仓"""
        data = [item.model_dump() for item in items]
        self._write_file(data)
    
    def add_item(self, item: PortfolioItem) -> PortfolioItem:
        """添加持仓项"""
        items = self.load()
        
        # 检查是否已存在
        existing_index = next(
            (i for i, existing in enumerate(items) if existing.ticker == item.ticker),
            None
        )
        
        if existing_index is not None:
            # 更新现有持仓
            existing_item = items[existing_index]
            new_quantity = existing_item.quantity + item.quantity
            total_cost = (existing_item.quantity * existing_item.cost_price + 
                         item.quantity * item.cost_price)
            new_cost_price = total_cost / new_quantity
            
            updated_item = PortfolioItem(
                ticker=item.ticker,
                quantity=new_quantity,
                cost_price=round(new_cost_price, 2),
                note=item.note or existing_item.note
            )
            items[existing_index] = updated_item
        else:
            # 添加新持仓
            items.append(item)
        
        self.save(items)
        return items[existing_index] if existing_index is not None else item
    
    def remove_item(self, ticker: str) -> bool:
        """移除持仓项"""
        items = self.load()
        original_length = len(items)
        items = [item for item in items if item.ticker.upper() != ticker.upper()]
        
        if len(items) < original_length:
            self.save(items)
            return True
        return False
    
    def update_item(self, ticker: str, **kwargs) -> Optional[PortfolioItem]:
        """更新持仓项"""
        items = self.load()
        for i, item in enumerate(items):
            if item.ticker.upper() == ticker.upper():
                # 更新字段
                update_data = item.model_dump()
                update_data.update(kwargs)
                update_data["updated_at"] = datetime.now().isoformat()
                
                items[i] = PortfolioItem(**update_data)
                self.save(items)
                return items[i]
        return None
    
    def get_all(self) -> List[PortfolioItem]:
        """获取所有持仓"""
        return self.load()
    
    def get_by_ticker(self, ticker: str) -> Optional[PortfolioItem]:
        """根据股票代码获取持仓"""
        items = self.load()
        for item in items:
            if item.ticker.upper() == ticker.upper():
                return item
        return None
