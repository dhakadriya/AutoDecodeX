"""
AutoDecodeX FastAPI application entry point.
"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api.routes import router
from backend.api.case_routes import case_router
from backend.stego.routes import stego_router

app = FastAPI(
    title="AutoDecodeX",
    description=(
        "Digital forensics and steganalysis platform. "
        "Provides encoding detection, recursive decoding, steganalysis, "
        "case management, and forensic report generation."
    ),
    version="2.0.0",
)

origins_env = os.getenv("ALLOWED_ORIGINS")
if origins_env:
    allow_origins = [o.strip() for o in origins_env.split(",") if o.strip()]
else:
    allow_origins = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
        "http://localhost:3002",
        "http://127.0.0.1:3002",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
app.include_router(stego_router)
app.include_router(case_router)


@app.get("/")
def root():
    return {
        "message": "AutoDecodeX API v2.0.0 is running. Visit /docs for Swagger UI.",
        "endpoints": {
            "decode": "POST /api/decode",
            "detect": "POST /api/detect",
            "cases": "POST /api/cases | GET /api/cases",
            "report_json": "GET /api/cases/{id}/report/json",
            "report_pdf": "GET /api/cases/{id}/report/pdf",
            "stego": "POST /api/stego/analyze",
            "benchmark": "POST /api/benchmark/run",
            "health": "GET /health",
        }
    }

@app.get("/health")
def health():
    from backend.models.case_store import case_count
    return {
        "status": "healthy",
        "service": "AutoDecodeX",
        "version": "2.0.0",
        "cases_in_memory": case_count(),
        "storage": "in-process (ephemeral — does not survive restart)",
    }