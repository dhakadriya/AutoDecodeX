"""
FastAPI route definitions.
"""
import time
from fastapi import APIRouter, UploadFile, File
from pydantic import BaseModel
from typing import Optional

from backend.engine.orchestrator import decode, brute_force_caesar, brute_force_xor
from backend.detectors.detector import detect_all
from backend.tests.demo_dataset import DATASET_SAMPLES
from backend.stego.lsb_extractor import extract_lsb
from backend.stego.metadata_analyzer import full_metadata_pipeline
from backend.stego.entropy_analyzer import analyze_entropy

router = APIRouter(prefix="/api")


class DecodeRequest(BaseModel):
    input: str
    ctf_mode: bool = False
    confidence_threshold: Optional[float] = None
    max_depth: Optional[int] = None


class DetectRequest(BaseModel):
    input: str


class BruteForceRequest(BaseModel):
    input: str
    mode: str = "caesar"  # "caesar" or "xor"


@router.post("/decode")
def decode_endpoint(req: DecodeRequest):
    thresh = req.confidence_threshold
    if thresh is not None:
        # If passed as an integer percent (e.g. 60), convert to float (0.60)
        if thresh > 1.0:
            thresh = thresh / 100.0
            
    result = decode(
        req.input,
        ctf_mode=req.ctf_mode,
        confidence_threshold=thresh,
        max_depth=req.max_depth
    )
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


@router.post("/experiments/run")
def run_experiments():
    results = []
    total_time = 0.0
    successful_decodes = 0
    
    depth_stats = {} # depth -> {"total": 0, "success": 0}

    for sample in DATASET_SAMPLES:
        start_time = time.perf_counter()
        dec_res = decode(sample["input"])
        elapsed = time.perf_counter() - start_time
        total_time += elapsed

        # Check success: exact output or expected contained in output
        success = (dec_res.final_output.strip() == sample["expected"].strip() or
                   sample["expected"].strip() in dec_res.final_output.strip())
        
        if success:
            successful_decodes += 1

        depth = sample["depth"]
        if depth not in depth_stats:
            depth_stats[depth] = {"total": 0, "success": 0}
        depth_stats[depth]["total"] += 1
        if success:
            depth_stats[depth]["success"] += 1

        results.append({
            "type": sample["type"],
            "input": sample["input"],
            "expected": sample["expected"],
            "output": dec_res.final_output,
            "success": success,
            "time_ms": round(elapsed * 1000, 2),
            "depth": depth,
            "steps": [s.encoding_type for s in dec_res.steps]
        })

    num_samples = len(DATASET_SAMPLES)
    overall_accuracy = (successful_decodes / num_samples) * 100 if num_samples > 0 else 0.0
    avg_time_ms = (total_time / num_samples) * 1000 if num_samples > 0 else 0.0

    breakdown = {}
    for d, stats in depth_stats.items():
        breakdown[f"Depth {d}"] = {
            "accuracy": round((stats["success"] / stats["total"]) * 100, 2),
            "total": stats["total"],
            "success": stats["success"]
        }

    return {
        "accuracy": round(overall_accuracy, 2),
        "average_time_ms": round(avg_time_ms, 2),
        "total_runs": num_samples,
        "successful_runs": successful_decodes,
        "depth_breakdown": breakdown,
        "individual_runs": results
    }


@router.post("/file/analyze")
async def analyze_file_endpoint(file: UploadFile = File(...)):
    content = await file.read()
    
    # Run full metadata pipeline
    meta_result = full_metadata_pipeline(content)
    
    # Run LSB extraction (1 bit, RGB, no password)
    lsb_result = extract_lsb(content, bits=1, channels="RGB", password=None)
    
    # Run entropy analysis
    entropy_result = analyze_entropy(content)
    
    # Auto-decode LSB text if present
    lsb_text = lsb_result.get("ascii_text", "")
    lsb_decode = None
    if lsb_text and len(lsb_text) >= 4:
        try:
            dr = decode(lsb_text)
            lsb_decode = {
                "success": dr.success,
                "final_output": dr.final_output,
                "total_score": round(dr.total_score, 3),
                "path_description": dr.path_description,
                "is_ctf_flag": dr.is_ctf_flag,
            }
        except Exception:
            pass
            
    # Combine results
    return {
        "filename": file.filename,
        "metadata": meta_result,
        "lsb": lsb_result,
        "lsb_decode": lsb_decode,
        "entropy": entropy_result,
    }


@router.get("/health")
def health():
    return {"status": "ok", "service": "AutoDecodeX"}
