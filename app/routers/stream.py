import asyncio
import json
from fastapi import APIRouter, Depends, HTTPException, Request
from sse_starlette.sse import EventSourceResponse
from app.db.base import get_db
from app.db.models import Monitor, User
from app.routers.auth import get_current_user
from app.core.redis_client import redis_client
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

router = APIRouter(prefix="/stream", tags=["stream"])

@router.get("/{monitor_id}")
async def stream_results(
    monitor_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Ensure monitor belongs to user
    m_result = await db.execute(select(Monitor).where(Monitor.id == monitor_id, Monitor.user_id == current_user.id))
    if not m_result.scalars().first():
        raise HTTPException(status_code=404, detail="Monitor not found")

    async def event_generator():
        r = await redis_client.get_client()
        pubsub = r.pubsub()
        await pubsub.subscribe(f"monitor:{monitor_id}")
        
        try:
            while True:
                if await request.is_disconnected():
                    break
                
                message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                if message:
                    yield {
                        "event": "message",
                        "data": message["data"]
                    }
                await asyncio.sleep(0.1)
        finally:
            await pubsub.unsubscribe(f"monitor:{monitor_id}")

    return EventSourceResponse(event_generator())
