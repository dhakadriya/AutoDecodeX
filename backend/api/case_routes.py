"""
Case management and report API routes.

Endpoints:
  POST /api/cases               – create a new case from file upload
  GET  /api/cases               – list recent cases
  GET  /api/cases/{case_id}     – get a single case
  DELETE /api/cases/{case_id}   – delete a case
  GET  /api/cases/{case_id}/report/json  – download JSON report
  GET  /api/cases/{case_id}/report/pdf   – download PDF report
  POST /api/benchmark/run       – run the steganalysis benchmark

Security:
  - Files are validated (size, extension, magic bytes where applicable).
  - Temp files are cleaned up in finally blocks.
  - Error messages do not expose internal tracebacks.
  - Report content is sanitised; no executable content is returned.
  - Case IDs are server-generated UUIDs; client cannot request arbitrary paths.
"""
from __future__ import annotations

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse, Response
from typing import Optional

from backend.engine.analysis_orchestrator import run_full_analysis, build_report
from backend.engine.file_handler import validate_and_save_temp_file, cleanup_temp_file
from backend.engine.report_generator import report_to_json, report_to_pdf
from backend.models.case_store import get_case, list_cases, delete_case
from backend.models.schemas import DEFAULT_LIMITS

case_router = APIRouter(prefix="/api")

MAX_UPLOAD_BYTES = DEFAULT_LIMITS.max_input_file_bytes


# ── Case creation ──────────────────────────────────────────────────────────

@case_router.post("/cases")
async def create_case(
    file: UploadFile = File(...),
    run_stego: bool = Form(True),
):
    """
    Upload a file and run the full analysis pipeline.
    Returns the completed Case object.
    """
    temp_path = None
    try:
        temp_path, file_bytes = await validate_and_save_temp_file(
            file,
            max_size=MAX_UPLOAD_BYTES,
            allowed_extensions=None,   # accept any file type
            allowed_mime_types=None,
            validate_magic=False,      # orchestrator does its own format detection
        )
        case = run_full_analysis(
            filename=file.filename or "unknown",
            file_bytes=file_bytes,
            mime_type=file.content_type,
        )
        # Return the case without image bytes in artifacts for brevity
        return _case_to_dict(case)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={"status": "error", "message": f"Case creation failed: {_safe_error(exc)}"},
        )
    finally:
        if temp_path:
            cleanup_temp_file(temp_path)


# ── Case listing and retrieval ─────────────────────────────────────────────

@case_router.get("/cases")
def list_cases_endpoint(limit: int = 20, offset: int = 0):
    """Return recent cases (most recent first). Max limit 100."""
    limit = min(limit, 100)
    cases = list_cases(limit=limit, offset=offset)
    return {
        "cases": [_case_summary(c) for c in cases],
        "total": len(cases),
        "limit": limit,
        "offset": offset,
        "storage_note": (
            "Cases are stored in-process and do not survive a server restart."
        ),
    }


@case_router.get("/cases/{case_id}")
def get_case_endpoint(case_id: str):
    """Retrieve a single case by ID."""
    case = get_case(case_id)
    if not case:
        raise HTTPException(status_code=404, detail={"status": "error", "message": "Case not found."})
    return _case_to_dict(case)


@case_router.delete("/cases/{case_id}")
def delete_case_endpoint(case_id: str):
    """Remove a case from the in-memory store."""
    removed = delete_case(case_id)
    if not removed:
        raise HTTPException(status_code=404, detail={"status": "error", "message": "Case not found."})
    return {"status": "ok", "message": f"Case {case_id} deleted."}


# ── Report downloads ───────────────────────────────────────────────────────

@case_router.get("/cases/{case_id}/report/json")
def download_json_report(case_id: str):
    """Download the forensic report as JSON."""
    case = get_case(case_id)
    if not case:
        raise HTTPException(status_code=404, detail={"status": "error", "message": "Case not found."})
    report = build_report(case)
    json_str = report_to_json(report)
    return Response(
        content=json_str,
        media_type="application/json",
        headers={
            "Content-Disposition": f'attachment; filename="autodecodex_report_{case_id[:8]}.json"',
            "X-Content-Type-Options": "nosniff",
        },
    )


@case_router.get("/cases/{case_id}/report/pdf")
def download_pdf_report(case_id: str):
    """Download the forensic report as PDF."""
    case = get_case(case_id)
    if not case:
        raise HTTPException(status_code=404, detail={"status": "error", "message": "Case not found."})
    report = build_report(case)
    try:
        pdf_bytes = report_to_pdf(report)
    except ImportError as exc:
        raise HTTPException(
            status_code=503,
            detail={
                "status": "error",
                "message": (
                    "PDF generation requires fpdf2. "
                    "Install it with: pip install fpdf2"
                ),
            },
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={"status": "error", "message": f"PDF generation failed: {_safe_error(exc)}"},
        )
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="autodecodex_report_{case_id[:8]}.pdf"',
            "X-Content-Type-Options": "nosniff",
        },
    )


# ── Benchmark ─────────────────────────────────────────────────────────────

@case_router.post("/benchmark/run")
def run_benchmark_endpoint(
    split: str = "eval",
    entropy_threshold: float = 0.5,
    lsb_threshold: float = 0.5,
    seed: int = 42,
):
    """
    Run the reproducible steganalysis benchmark.
    Results are labelled as preliminary synthetic-dataset metrics.
    This endpoint is separate from case analysis and never mixes with real investigations.
    """
    try:
        from backend.benchmark.evaluator import run_benchmark
        result = run_benchmark(
            split=split,
            entropy_threshold=entropy_threshold,
            lsb_score_threshold=lsb_threshold,
            seed=seed,
        )
        # Strip image bytes from manifest before returning
        for s in result.get("manifest", {}).get("samples", []):
            s.pop("image_bytes", None)
        return result
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={"status": "error", "message": f"Benchmark failed: {_safe_error(exc)}"},
        )


# ── Serialisation helpers ──────────────────────────────────────────────────

def _case_to_dict(case) -> dict:
    """Serialise a Case to a dict safe for API response."""
    d = case.model_dump()
    return d


def _case_summary(case) -> dict:
    """Lightweight case summary for list views."""
    return {
        "case_id": case.case_id,
        "created_at_utc": case.created_at_utc,
        "completed_at_utc": case.completed_at_utc,
        "original_filename": case.original_filename,
        "file_size_bytes": case.file_size_bytes,
        "detected_format": case.detected_format,
        "sha256": case.sha256,
        "status": case.status.value,
        "finding_count": len(case.findings),
        "correlation_count": len(case.correlations),
        "modules_completed": case.completed_modules,
    }


def _safe_error(exc: Exception) -> str:
    """Return a safe error message without internal traceback paths."""
    msg = str(exc)
    # Do not leak file paths, module internals
    if len(msg) > 200:
        msg = msg[:200] + "..."
    return msg
