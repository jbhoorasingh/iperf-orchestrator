from sqlalchemy import Column, Integer, String, DateTime, JSON, UniqueConstraint
from app.database import Base


class IdempotencyLog(Base):
    __tablename__ = "idempotency_log"
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, nullable=False, index=True)
    endpoint = Column(String, nullable=False)
    response = Column(JSON, nullable=False)
    created_at = Column(DateTime, nullable=False)
