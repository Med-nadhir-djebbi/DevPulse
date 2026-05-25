from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from typing import List
import json
from app.db.base import get_db
from app.db.models import CheckResult, Monitor, User
from app.schemas.result import CheckResultResponse, MonitorStats
from app.routers.auth import get_current_user
from app.core.redis_client import redis_client

router = APIRouter(prefix="/monitors", tags=["results"])

@router.get("/{monitor_id}/results", response_model=List[CheckResultResponse])
async def get_results(
    monitor_id: int,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Ensure monitor belongs to user
    m_result = await db.execute(select(Monitor).where(Monitor.id == monitor_id, Monitor.user_id == current_user.id))
    if not m_result.scalars().first():
        raise HTTPException(status_code=404, detail="Monitor not found")
    
    result = await db.execute(
        select(CheckResult)
        .where(CheckResult.monitor_id == monitor_id)
        .order_by(CheckResult.checked_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()

@router.get("/{monitor_id}/stats", response_model=MonitorStats)
async def get_stats(
    monitor_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Try cache first
    r = await redis_client.get_client()
    cache_key = f"stats:{monitor_id}"
    cached_stats = await r.get(cache_key)
    if cached_stats:
        return MonitorStats(**json.loads(cached_stats))

    # Ensure monitor belongs to user
    m_result = await db.execute(select(Monitor).where(Monitor.id == monitor_id, Monitor.user_id == current_user.id))
    if not m_result.scalars().first():
        raise HTTPException(status_code=404, detail="Monitor not found")
    
    # Aggregate stats
    total_result = await db.execute(select(func.count(CheckResult.id)).where(CheckResult.monitor_id == monitor_id))
    total_checks = total_result.scalar() or 0
    
    if total_checks == 0:
        return MonitorStats(uptime_percentage=0, avg_response_time_ms=0, total_checks=0, passed_checks=0, failed_checks=0)
    
    passed_result = await db.execute(select(func.count(CheckResult.id)).where(CheckResult.monitor_id == monitor_id, CheckResult.passed == True))
    passed_checks = passed_result.scalar() or 0
    
    avg_lat_result = await db.execute(select(func.avg(CheckResult.response_time_ms)).where(CheckResult.monitor_id == monitor_id, CheckResult.passed == True))
    avg_lat = avg_lat_result.scalar() or 0
    
    uptime_pct = (passed_checks / total_checks) * 100
    
    stats = MonitorStats(
        uptime_percentage=uptime_pct,
        avg_response_time_ms=float(avg_lat),
        total_checks=total_checks,
        passed_checks=passed_checks,
        failed_checks=total_checks - passed_checks
    )
    
    # Cache for 60 seconds
    await r.setex(cache_key, 60, json.dumps(stats.dict()))
    
    return stats
