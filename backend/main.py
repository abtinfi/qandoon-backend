from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import redis.asyncio as redis
import os
from dotenv import load_dotenv
from backend.routes import users, pastries, order
from backend.database.config import engine, Base
from contextlib import asynccontextmanager


load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan: Initializes database and Redis clients.
    """
    print("Application startup: Initializing resources...")

    # --- Database Schema Creation ---
    try:
        print("Attempting to create database schema...")
        Base.metadata.create_all(bind=engine)
        print("Database schema check/creation complete.")
    except Exception as e:
        print(f"Error during database schema creation: {e}")

    # --- Redis Client Setup ---
    try:
        redis_url = os.getenv("REDIS_URL")
        if not redis_url:
            print("REDIS_URL environment variable not set. Redis client will not be initialized.")
            app.state.redis = None
        else:
            print(f"Connecting to Redis ...")
            redis_client = redis.from_url(redis_url, encoding="utf-8", decode_responses=True)
            await redis_client.ping()
            print("Redis connection successful.")
            app.state.redis = redis_client 
            print("Redis client stored in app.state.")

    except Exception as e:
        print(f"Error connecting to Redis: {e}")
        app.state.redis = None

    yield 

    # --- Application Shutdown ---
    print("Application shutdown: Cleaning up resources...")
    if hasattr(app.state, 'redis') and app.state.redis is not None:
        print("Closing Redis client connection...")
        await app.state.redis.close()
        print("Redis client connection closed.")


app = FastAPI(lifespan=lifespan)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(pastries.router, prefix="/pastries", tags=["pastries"])
app.include_router(order.router, prefix="/order", tags=["orders"])


@app.get("/")
async def root():
    return {"message": "Welcome to the API for the Pastry shop!"}