import redis
import os

redis_client = redis.from_url(os.getenv("REDIS_URL"))

def get_redis():
    """Dependency to get Redis client."""
    try:
        yield redis_client
    finally:
        pass