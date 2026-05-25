try:
    import fastapi
    import sqlalchemy
    import redis.asyncio
    import apscheduler
    import httpx
    import jose
    import passlib
    from app.main import app
    print("Import successful")
except ImportError as e:
    print(f"Missing dependency: {e}")
except Exception as e:
    print(f"Error: {e}")
