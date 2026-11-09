from fastapi import FastAPI

from app import models
from app.database import Base, engine
from app.routers import tasks

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="TaskFlow API",
    description="A simple task manager REST API built with FastAPI.",
    version="1.0.0",
)

app.include_router(tasks.router)


@app.get("/", tags=["Health"])
def health_check():
    return {"status": "ok", "message": "TaskFlow API is running"}
