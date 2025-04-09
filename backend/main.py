from fastapi import FastAPI
from backend.routes.auth import router as auth_router
from backend.database.config import engine, Base

Base.metadata.create_all(bind=engine) #creat db for ferst time in dev

app = FastAPI()

app.include_router(auth_router, prefix="/api/auth", tags=["auth"])

@app.get("/")
async def root():
    return {"message": "Hello  main page"}
