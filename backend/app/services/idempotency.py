from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models.idempotency_log import IdempotencyLog
from datetime import datetime


class IdempotencyService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_cached_response(self, key: str, endpoint: str) -> Optional[Dict[str, Any]]:
        """Get cached response for idempotency key"""
        cached = self.db.query(IdempotencyLog).filter(
            IdempotencyLog.key == key,
            IdempotencyLog.endpoint == endpoint
        ).first()
        
        if cached:
            return cached.response
        return None
    
    def cache_response(self, key: str, endpoint: str, response: Dict[str, Any]) -> None:
        """Cache response for idempotency key"""
        cached = IdempotencyLog(
            key=key,
            endpoint=endpoint,
            response=response,
            created_at=datetime.utcnow()
        )
        self.db.add(cached)
        self.db.commit()
