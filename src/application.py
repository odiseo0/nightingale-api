from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.settings.api_settings import api_settings

app = FastAPI(title="Nightingale API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=api_settings.cors_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def welcome():
    return {"message": "Bienvenido a Nightingale API"}
