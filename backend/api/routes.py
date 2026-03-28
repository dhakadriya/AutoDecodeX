"""
FastAPI route definitions.
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

from backend.engine.orchestrator import decode, brute_force_caesar, brute_force_xor
from backend.detectors.detector import detect_all

router = APIRouter(prefix="/api")


class DecodeRequest(BaseModel):
    input: str
    ctf_mode: bool = False


class DetectRequest(BaseModel):
    input: str


class BruteForceRequest(BaseModel):
    input: str
    mode: str = "caesar"  # "caesar" or "xor"


@router.post("/decode")
def decode_endpoint(req: DecodeRequest):
    result = decode(req.input, ctf_mode=req.ctf_mode)
    return {
        "success": result.success,
        "final_output": result.final_output,
        "total_score": round(result.total_score, 3),
        "path_description": result.path_description,
        "is_ctf_flag": result.is_ctf_flag,
        "steps": [
            {
                "step_number": s.step_number,
                "encoding_type": s.encoding_type,
                "confidence": s.confidence,
                "input_text": s.input_text[:500],  # truncate for safety
                "output_text": s.output_text[:500],
                "score": round(s.score, 3),
            }
            for s in result.steps
        ],
    }


@router.post("/detect")
def detect_endpoint(req: DetectRequest):
    detections = detect_all(req.input)
    return {"detections": detections}


@router.post("/brute-force")
def brute_force_endpoint(req: BruteForceRequest):
    if req.mode == "caesar":
        results = brute_force_caesar(req.input)
        return {"mode": "caesar", "results": results[:26]}
    elif req.mode == "xor":
        results = brute_force_xor(req.input)
        return {"mode": "xor", "results": results[:10]}
    return {"error": "Unknown mode. Use 'caesar' or 'xor'."}


@router.get("/health")
def health():
    return {"status": "ok", "service": "AutoDecodeX"}
