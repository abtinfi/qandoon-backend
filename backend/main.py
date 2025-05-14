from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
import redis.asyncio as redis
import os
from dotenv import load_dotenv
from backend.routes import users, pastries
from backend.database.config import engine, Base
from contextlib import asynccontextmanager
from sqlalchemy import inspect

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Check if tables exist before creating them
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()
    
    # Only create tables that don't exist
    tables_to_create = []
    for table in Base.metadata.tables:
        if table not in existing_tables:
            tables_to_create.append(Base.metadata.tables[table])
    
    if tables_to_create:
        Base.metadata.create_all(bind=engine, tables=tables_to_create)
    
    redis_client = redis.from_url(os.getenv("REDIS_URL"), encoding="utf-8", decode_responses=True)
    app.state.redis = redis_client
    yield
    await redis_client.close()

app = FastAPI(lifespan=lifespan)
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files directory
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(pastries.router, prefix="/pastries", tags=["pastries"])

@app.get("/")
async def root():
    return {"message": "Welcome to the API for the Pastry Shop!"}
