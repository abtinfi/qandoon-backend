from fastapi import Request
from fastapi import HTTPException, status


def get_redis(request: Request):
    """
    Dependency to get the Async Redis client stored in app.state.
    """
    redis_client = getattr(request.app.state, 'redis', None)

    if redis_client is None:
         print("Redis client not available in app.state. Check lifespan initialization.")
         raise HTTPException(
             status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
             detail="Redis service is not available."
         )
    return redis_client