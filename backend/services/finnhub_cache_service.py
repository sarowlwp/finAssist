from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from models import FinnhubCache
from typing import Dict, Any, Optional
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 常量定义
DEFAULT_TTL = timedelta(hours=1)
CACHE_TTL_CONFIG = {
    "quote": timedelta(minutes=5),
    "company_profile": timedelta(hours=24),
    "financials": timedelta(hours=12),
    "news": timedelta(hours=1),
    "technical_indicators": timedelta(hours=6)
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
            if cache_entry:
                logger.info(f"Cache hit for key: {cache_key}")
                return cache_entry.data
            else:
                logger.info(f"Cache miss for key: {cache_key}")
                return None
        except Exception as e:
            logger.error(f"Error getting cache for key {cache_key}: {str(e)}")
            self.db.rollback()
            return None

    def set_cache(self, data_type: str, ticker: str, data: Dict[str, Any], expires_in: Optional[timedelta] = None) -> None:
        try:
            cache_key = self._get_cache_key(data_type, ticker)

            # 确定过期时间
            if expires_in is not None:
                ttl = expires_in
            else:
                ttl = CACHE_TTL_CONFIG.get(data_type, DEFAULT_TTL)

            expires_at = datetime.now(timezone.utc) + ttl

            existing = self.db.query(FinnhubCache).filter(
                FinnhubCache.cache_key == cache_key
            ).first()

            if existing:
                existing.data = data
                existing.expires_at = expires_at
                logger.info(f"Cache updated for key: {cache_key}, expires in {ttl}")
            else:
                new_cache = FinnhubCache(
                    cache_key=cache_key,
                    data_type=data_type,
                    ticker=ticker.upper(),
                    data=data,
                    expires_at=expires_at
                )
                self.db.add(new_cache)
                logger.info(f"Cache created for key: {cache_key}, expires in {ttl}")

            self.db.commit()
        except Exception as e:
            logger.error(f"Error setting cache for key {cache_key}: {str(e)}")
            self.db.rollback()

    def delete_cache(self, data_type: str, ticker: str) -> None:
        try:
            cache_key = self._get_cache_key(data_type, ticker)
            deleted_count = self.db.query(FinnhubCache).filter(FinnhubCache.cache_key == cache_key).delete()
            self.db.commit()
            logger.info(f"Cache deleted for key: {cache_key}, deleted {deleted_count} entries")
        except Exception as e:
            logger.error(f"Error deleting cache for key {cache_key}: {str(e)}")
            self.db.rollback()

    def delete_expired_cache(self) -> None:
        try:
            deleted_count = self.db.query(FinnhubCache).filter(
                FinnhubCache.expires_at <= datetime.now(timezone.utc)
            ).delete()
            self.db.commit()
            logger.info(f"Expired cache cleanup completed, deleted {deleted_count} entries")
        except Exception as e:
            logger.error(f"Error deleting expired cache: {str(e)}")
            self.db.rollback()
