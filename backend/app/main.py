from fastapi import FastAPI
from app.routers import health, chat, auth

app = FastAPI(title="Bangla Government-Service Assistant")

app.include_router(health.router)
app.include_router(chat.router)
app.include_router(auth.router)