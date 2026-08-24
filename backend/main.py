"""
AutoDecodeX FastAPI application entry point.
"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api.routes import router
from backend.stego.routes import stego_router

app = FastAPI(
    title="AutoDecodeX",
    description="AI-assisted encoding detection and decoding engine for CTF players.",
    version="1.0.0",
)

origins_env = os.getenv("ALLOWED_ORIGINS")
if origins_env:
    allow_origins = [o.strip() for o in origins_env.split(",") if o.strip()]
else:
    allow_origins = ["http://localhost:3000", "http://127.0.0.1:3000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
app.include_router(stego_router)


@app.get("/")
def root():
    return {"message": "AutoDecodeX API is running. Visit /docs for Swagger UI."}

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "stego-analyzer"
    }