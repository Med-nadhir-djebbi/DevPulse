from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class CheckResultResponse(BaseModel):
    id: int
    monitor_id: int
    checked_at: datetime
    status_code: Optional[int]
    response_time_ms: Optional[int]
    passed: bool
    error_message: Optional[str]

    class Config:
        from_attributes = True

class MonitorStats(BaseModel):
    uptime_percentage: float
    avg_response_time_ms: float
    total_checks: int
    passed_checks: int
    failed_checks: int
