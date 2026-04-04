from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from models import FinnhubCache
from typing import Dict, Any, Optional

# 常量定义
DEFAULT_TTL = timedelta(hours=1)
CACHE_TTL_CONFIG = {
    "quote": timedelta(minutes=5),
    "profile": timedelta(hours=24),
    "financials": timedelta(hours=12),
    "news": timedelta(hours=1),
    "technical": timedelta(hours=4)
}

class FinnhubCacheService:
    def __init__(self, db: Session):
        self.db = db

    def _get_cache_key(self, data_type: str, ticker: str) -> str:
        """生成缓存键的私有方法"""
        return f"{data_type}:{ticker.upper()}"

    def get_cache(self, data_type: str, ticker: str) -> Optional[Dict[str, Any]]:
        try:
            cache_key = self._get_cache_key(data_type, ticker)
            cache_entry = self.db.query(FinnhubCache).filter(
                FinnhubCache.cache_key == cache_key,
                FinnhubCache.expires_at > datetime.now(timezone.utc)
            ).first()
            return cache_entry.data if cache_entry else None
        except Exception as e:
            self.db.rollback()
            return None

    def set_cache(self, data_type: str, ticker: str, data: Dict[str, Any]) -> None:
        try:
            cache_key = self._get_cache_key(data_type, ticker)
            ttl = CACHE_TTL_CONFIG.get(data_type, DEFAULT_TTL)
            expires_at = datetime.now(timezone.utc) + ttl

            existing = self.db.query(FinnhubCache).filter(
                FinnhubCache.cache_key == cache_key
            ).first()

            if existing:
                existing.data = data
                existing.expires_at = expires_at
            else:
                new_cache = FinnhubCache(
                    cache_key=cache_key,
                    data_type=data_type,
                    ticker=ticker.upper(),
                    data=data,
                    expires_at=expires_at
                )
                self.db.add(new_cache)

            self.db.commit()
        except Exception as e:
            self.db.rollback()

    def delete_cache(self, data_type: str, ticker: str) -> None:
        try:
            cache_key = self._get_cache_key(data_type, ticker)
            self.db.query(FinnhubCache).filter(FinnhubCache.cache_key == cache_key).delete()
            self.db.commit()
        except Exception as e:
            self.db.rollback()

    def delete_expired_cache(self) -> None:
        try:
            self.db.query(FinnhubCache).filter(
                FinnhubCache.expires_at <= datetime.now(timezone.utc)
            ).delete()
            self.db.commit()
        except Exception as e:
            self.db.rollback()
