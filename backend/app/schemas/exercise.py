from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from .test import TestResponse
from .task import TaskResponse


class ExerciseBase(BaseModel):
    name: str
    duration_seconds: int = 30
    notes: Optional[str] = None


class ExerciseCreate(ExerciseBase):
    pass


class Exercise(ExerciseBase):
    id: int
    created_at: datetime
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class ExerciseResponse(Exercise):
    pass


class ExerciseDetail(Exercise):
    tests: List[TestResponse] = []
    tasks: List[TaskResponse] = []
