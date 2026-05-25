from fastapi import FastAPI
from app.routers import auth, monitors, results, stream
from app.db.base import engine, Base
from app.core.config import settings
from app.core.scheduler import start_scheduler
from app.core.redis_client import redis_client
import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title=settings.PROJECT_NAME)

@app.on_event("startup")
async def startup():
    retries = 5
    while retries > 0:
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("Database connection established and tables created.")
            break
        except Exception as e:
            retries -= 1
            logger.warning(f"Database connection failed. Retrying... ({retries} left). Error: {e}")
            await asyncio.sleep(5)
    
    if retries == 0:
        logger.error("Could not connect to the database. Exiting.")
        raise RuntimeError("Database connection failed")

    await redis_client.connect()
    logger.info("Connected to Redis.")
    
    start_scheduler()
    logger.info("Scheduler started.")

@app.on_event("shutdown")
async def shutdown():
    await redis_client.disconnect()
    logger.info("Disconnected from Redis.")

app.include_router(auth.router)
app.include_router(monitors.router)
app.include_router(results.router)
app.include_router(stream.router)

@app.get("/")
async def root():
    return {"message": "Welcome to DevPulse API"}
