from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import health, chat, auth

app = FastAPI(title="Bangla Government-Service Assistant")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(chat.router)
app.include_router(auth.router)