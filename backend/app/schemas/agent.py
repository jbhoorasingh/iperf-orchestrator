from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class AgentBase(BaseModel):
    name: str
    registration_key: str
    operating_system: Optional[str] = None


class AgentCreate(AgentBase):
    pass


class Agent(AgentBase):
    id: int
    status: str
    first_registered: datetime
    last_heartbeat: Optional[datetime] = None
    ip_address: Optional[str] = None

    class Config:
        from_attributes = True


class AgentResponse(Agent):
    pass


class AgentRegisterRequest(BaseModel):
    ip_address: str
    operating_system: Optional[str] = None


class AgentHeartbeatRequest(BaseModel):
    ip_address: str
    running: List[Dict[str, Any]] = []
