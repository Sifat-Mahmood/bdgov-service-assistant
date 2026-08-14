from fastapi import FastAPI
from app.routers import health, chat

app = FastAPI(title="Bangla Government-Service Assistant")

app.include_router(health.router)
app.include_router(chat.router)