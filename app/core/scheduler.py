import asyncio
import httpx
import json
from datetime import datetime, timedelta
from sqlalchemy.future import select
from sqlalchemy import update
from app.db.base import AsyncSessionLocal
from app.db.models import Monitor, CheckResult, Alert
from app.core.redis_client import redis_client
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()

async def run_check(monitor_id: int):
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Monitor).where(Monitor.id == monitor_id))
        monitor = result.scalars().first()
        if not monitor or not monitor.is_active:
            return

        async with httpx.AsyncClient(timeout=monitor.timeout_ms / 1000.0) as client:
            start_time = datetime.utcnow()
            try:
                response = await client.get(monitor.url)
                end_time = datetime.utcnow()
                response_time_ms = int((end_time - start_time).total_seconds() * 1000)
                
                passed = response.status_code == monitor.expected_status
                if passed and monitor.expected_body_contains:
                    passed = monitor.expected_body_contains in response.text
                
                result = CheckResult(
                    monitor_id=monitor.id,
                    status_code=response.status_code,
                    response_time_ms=response_time_ms,
                    passed=passed,
                    error_message=None if passed else "Validation failed"
                )
            except Exception as e:
                result = CheckResult(
                    monitor_id=monitor.id,
                    status_code=None,
                    response_time_ms=None,
                    passed=False,
                    error_message=str(e)
                )
            
            db.add(result)
            
            await db.execute(
                update(Monitor)
                .where(Monitor.id == monitor.id)
                .values(last_checked_at=datetime.utcnow())
            )
            
            redis = await redis_client.get_client()
            await redis.publish(f"monitor:{monitor.id}", json.dumps({
                "status_code": result.status_code,
                "response_time_ms": result.response_time_ms,
                "passed": result.passed,
                "checked_at": str(datetime.utcnow())
            }))

            if not result.passed:
                alert_result = await db.execute(select(Alert).where(Alert.monitor_id == monitor.id))
                alert = alert_result.scalars().first()
                if alert:
                    try:
                        async with httpx.AsyncClient() as alert_client:
                            await alert_client.post(alert.webhook_url, json={
                                "event": "monitor_failed",
                                "monitor_name": monitor.name,
                                "url": monitor.url,
                                "error": result.error_message or f"Status {result.status_code}"
                            })
                    except Exception:
                        pass
            
            await db.commit()

async def check_all_monitors():
    async with AsyncSessionLocal() as db:
        now = datetime.utcnow()
        result = await db.execute(
            select(Monitor.id).where(
                Monitor.is_active == True,
                (Monitor.last_checked_at == None) | 
                (Monitor.last_checked_at <= now - timedelta(seconds=1) * Monitor.interval_seconds)
            )
        )
        monitor_ids = result.scalars().all()
        
        tasks = [run_check(m_id) for m_id in monitor_ids]
        if tasks:
            await asyncio.gather(*tasks)

def start_scheduler():
    scheduler.add_job(check_all_monitors, "interval", seconds=10)
    scheduler.start()
