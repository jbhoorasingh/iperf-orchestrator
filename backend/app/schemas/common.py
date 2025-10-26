from pydantic import BaseModel
from typing import Optional, Dict, Any


class ErrorResponse(BaseModel):
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None
