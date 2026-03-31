"""
AutoDecodeX FastAPI application entry point.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api.routes import router
from backend.stego.routes import stego_router

app = FastAPI(
    title="AutoDecodeX",
    description="AI-assisted encoding detection and decoding engine for CTF players.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
app.include_router(stego_router)


@app.get("/")
def root():
    return {"message": "AutoDecodeX API is running. Visit /docs for Swagger UI."}
