from pydantic import BaseModel
from typing import Optional


class TestBase(BaseModel):
    server_agent_id: int
    client_agent_id: int
    server_port: int
    udp: bool = False
    parallel: int = 1
    time_seconds: Optional[int] = None


class TestCreate(TestBase):
    pass


class Test(TestBase):
    id: int
    exercise_id: int
    server_task_id: Optional[int] = None
    client_task_id: Optional[int] = None
    
    class Config:
        from_attributes = True


class TestResponse(Test):
    pass
