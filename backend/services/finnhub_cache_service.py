from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from models import FinnhubCache
from typing import Dict, Any, Optional

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

    def get_cache(self, data_type: str, ticker: str) -> Optional[Dict[str, Any]]:
        cache_key = f"{data_type}:{ticker.upper()}"

        cache_entry = self.db.query(FinnhubCache).filter(
            FinnhubCache.cache_key == cache_key,
            FinnhubCache.expires_at > datetime.now()
        ).first()

        if cache_entry:
            return cache_entry.data

        return None

    def set_cache(self, data_type: str, ticker: str, data: Dict[str, Any]):
        cache_key = f"{data_type}:{ticker.upper()}"

        ttl = CACHE_TTL_CONFIG.get(data_type, timedelta(hours=1))
        expires_at = datetime.now() + ttl

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

    def delete_cache(self, data_type: str, ticker: str):
        cache_key = f"{data_type}:{ticker.upper()}"
        self.db.query(FinnhubCache).filter(FinnhubCache.cache_key == cache_key).delete()
        self.db.commit()

    def delete_expired_cache(self):
        self.db.query(FinnhubCache).filter(
            FinnhubCache.expires_at <= datetime.now()
        ).delete()
        self.db.commit()
