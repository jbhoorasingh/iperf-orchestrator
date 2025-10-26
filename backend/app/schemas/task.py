from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime


class TaskBase(BaseModel):
    type: str
    agent_id: int
    status: str
    payload: Dict[str, Any] = {}


class Task(TaskBase):
    id: int
    created_at: datetime
    accepted_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    
    class Config:
        from_attributes = True


class TaskResponse(Task):
    pass


class TaskCancel(BaseModel):
    canceled: bool = True
    task: TaskResponse


class TaskStartedRequest(BaseModel):
    pid: Optional[int] = None


class TaskResultRequest(BaseModel):
    status: str
    result: Optional[Dict[str, Any]] = None
    stderr: Optional[str] = None
    exit_code: int = 0
