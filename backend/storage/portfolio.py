"""
持仓数据存储模块 - SQLite 版本
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from decimal import Decimal
from datetime import datetime
from pathlib import Path
import json

from models import PortfolioHolding


class PortfolioItem(BaseModel):
    """持仓项模型"""
    ticker: str = Field(..., description="股票代码")
    quantity: int = Field(..., gt=0, description="持仓数量")
    cost_price: float = Field(..., gt=0, description="成本价")
    note: Optional[str] = Field(None, description="备注")
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat(), description="创建时间")
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat(), description="更新时间")

    class Config:
        from_attributes = True


class PortfolioStore:
    """持仓存储类 - SQLite 版本"""

    def __init__(self, db: Session, data_dir: Optional[Path] = None):
        """
        初始化持仓存储

        Args:
            db: 数据库会话
            data_dir: 数据目录（用于迁移旧 JSON 数据）
        """
        self.db = db
        self.data_dir = data_dir

        # 尝试迁移旧数据
        if data_dir:
            self._migrate_from_json()

    def _migrate_from_json(self) -> None:
        """从旧的 JSON 文件迁移数据"""
        portfolio_file = self.data_dir / "portfolio.json"

        if not portfolio_file.exists():
            return

        try:
            content = portfolio_file.read_text(encoding="utf-8")
            data = json.loads(content) if content else []

            if not data:
                return

            # 检查数据库是否已经有数据
            existing_count = self.db.query(PortfolioHolding).count()
            if existing_count > 0:
                print(f"Database already has {existing_count} holdings, skipping migration")
                return

            print(f"Migrating {len(data)} holdings from JSON to SQLite...")

            for item in data:
                holding = PortfolioHolding(
                    ticker=item["ticker"],
                    quantity=item["quantity"],
                    cost_price=Decimal(str(item["cost_price"])),
                    note=item.get("note")
                )
                # 处理时间
                if "created_at" in item:
                    holding.created_at = datetime.fromisoformat(item["created_at"])
                if "updated_at" in item:
                    holding.updated_at = datetime.fromisoformat(item["updated_at"])

                self.db.add(holding)

            self.db.commit()
            print(f"Successfully migrated {len(data)} holdings to SQLite")

            # 备份旧文件
            backup_file = self.data_dir / "portfolio.json.backup"
            portfolio_file.rename(backup_file)
            print(f"Backed up old JSON file to {backup_file}")

        except Exception as e:
            print(f"Error migrating from JSON: {e}")
            self.db.rollback()

    def _holding_to_item(self, holding: PortfolioHolding) -> PortfolioItem:
        """将数据库模型转换为 PortfolioItem"""
        return PortfolioItem(
            ticker=holding.ticker,
            quantity=holding.quantity,
            cost_price=float(holding.cost_price),
            note=holding.note,
            created_at=holding.created_at.isoformat() if holding.created_at else datetime.now().isoformat(),
            updated_at=holding.updated_at.isoformat() if holding.updated_at else datetime.now().isoformat()
        )

    def load(self) -> List[PortfolioItem]:
        """加载所有持仓"""
        holdings = self.db.query(PortfolioHolding).order_by(PortfolioHolding.ticker).all()
        return [self._holding_to_item(h) for h in holdings]

    def save(self, items: List[PortfolioItem]) -> None:
        """保存所有持仓（替换现有数据）"""
        try:
            # 删除所有现有持仓
            self.db.query(PortfolioHolding).delete()

            # 添加新持仓
            for item in items:
                holding = PortfolioHolding(
                    ticker=item.ticker,
                    quantity=item.quantity,
                    cost_price=Decimal(str(item.cost_price)),
                    note=item.note
                )
                if item.created_at:
                    holding.created_at = datetime.fromisoformat(item.created_at)
                if item.updated_at:
                    holding.updated_at = datetime.fromisoformat(item.updated_at)
                self.db.add(holding)

            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

    def add_item(self, item: PortfolioItem) -> PortfolioItem:
        """添加持仓项"""
        try:
            # 检查是否已存在
            existing = self.db.query(PortfolioHolding).filter(
                PortfolioHolding.ticker.ilike(item.ticker)
            ).first()

            if existing:
                # 更新现有持仓
                new_quantity = existing.quantity + item.quantity
                total_cost = (existing.quantity * existing.cost_price +
                             item.quantity * Decimal(str(item.cost_price)))
                new_cost_price = total_cost / new_quantity

                existing.quantity = new_quantity
                existing.cost_price = new_cost_price
                if item.note:
                    existing.note = item.note
                existing.updated_at = datetime.now()

                self.db.commit()
                self.db.refresh(existing)
                return self._holding_to_item(existing)
            else:
                # 添加新持仓
                holding = PortfolioHolding(
                    ticker=item.ticker,
                    quantity=item.quantity,
                    cost_price=Decimal(str(item.cost_price)),
                    note=item.note
                )
                self.db.add(holding)
                self.db.commit()
                self.db.refresh(holding)
                return self._holding_to_item(holding)

        except IntegrityError:
            self.db.rollback()
            # 重新尝试，处理并发
            return self.add_item(item)
        except Exception:
            self.db.rollback()
            raise

    def remove_item(self, ticker: str) -> bool:
        """移除持仓项"""
        try:
            result = self.db.query(PortfolioHolding).filter(
                PortfolioHolding.ticker.ilike(ticker)
            ).delete()
            self.db.commit()
            return result > 0
        except Exception:
            self.db.rollback()
            raise

    def update_item(self, ticker: str, **kwargs) -> Optional[PortfolioItem]:
        """更新持仓项"""
        try:
            holding = self.db.query(PortfolioHolding).filter(
                PortfolioHolding.ticker.ilike(ticker)
            ).first()

            if not holding:
                return None

            # 更新字段
            if "quantity" in kwargs:
                holding.quantity = kwargs["quantity"]
            if "cost_price" in kwargs:
                holding.cost_price = Decimal(str(kwargs["cost_price"]))
            if "note" in kwargs:
                holding.note = kwargs["note"]

            holding.updated_at = datetime.now()

            self.db.commit()
            self.db.refresh(holding)
            return self._holding_to_item(holding)

        except Exception:
            self.db.rollback()
            raise

    def get_all(self) -> List[PortfolioItem]:
        """获取所有持仓"""
        return self.load()

    def get_by_ticker(self, ticker: str) -> Optional[PortfolioItem]:
        """根据股票代码获取持仓"""
        holding = self.db.query(PortfolioHolding).filter(
            PortfolioHolding.ticker.ilike(ticker)
        ).first()

        if holding:
            return self._holding_to_item(holding)
        return None
