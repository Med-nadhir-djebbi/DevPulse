from pydantic import BaseModel, HttpUrl
from datetime import datetime
from typing import Optional

class MonitorBase(BaseModel):
    name: str
    url: str
    interval_seconds: int = 60
    expected_status: int = 200
    expected_body_contains: Optional[str] = None
    timeout_ms: int = 5000
    is_active: bool = True

class MonitorCreate(MonitorBase):
    pass

class MonitorUpdate(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    interval_seconds: Optional[int] = None
    expected_status: Optional[int] = None
    expected_body_contains: Optional[str] = None
    timeout_ms: Optional[int] = None
    is_active: Optional[bool] = None

class MonitorResponse(MonitorBase):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True
