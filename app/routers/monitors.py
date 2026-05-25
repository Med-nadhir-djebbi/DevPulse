from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
from app.db.base import get_db
from app.db.models import Monitor, User
from app.schemas.monitor import MonitorCreate, MonitorUpdate, MonitorResponse
from app.routers.auth import get_current_user

router = APIRouter(prefix="/monitors", tags=["monitors"])

@router.post("/", response_model=MonitorResponse)
async def create_monitor(
    monitor_in: MonitorCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    monitor = Monitor(**monitor_in.dict(), user_id=current_user.id)
    db.add(monitor)
    await db.commit()
    await db.refresh(monitor)
    return monitor

@router.get("/", response_model=List[MonitorResponse])
async def list_monitors(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(Monitor).where(Monitor.user_id == current_user.id))
    return result.scalars().all()

@router.get("/{id}", response_model=MonitorResponse)
async def get_monitor(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(Monitor).where(Monitor.id == id, Monitor.user_id == current_user.id))
    monitor = result.scalars().first()
    if not monitor:
        raise HTTPException(status_code=404, detail="Monitor not found")
    return monitor

@router.patch("/{id}", response_model=MonitorResponse)
async def update_monitor(
    id: int,
    monitor_in: MonitorUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(Monitor).where(Monitor.id == id, Monitor.user_id == current_user.id))
    monitor = result.scalars().first()
    if not monitor:
        raise HTTPException(status_code=404, detail="Monitor not found")
    
    update_data = monitor_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(monitor, field, value)
    
    await db.commit()
    await db.refresh(monitor)
    return monitor

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_monitor(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(Monitor).where(Monitor.id == id, Monitor.user_id == current_user.id))
    monitor = result.scalars().first()
    if not monitor:
        raise HTTPException(status_code=404, detail="Monitor not found")
    
    await db.delete(monitor)
    await db.commit()
    return None
