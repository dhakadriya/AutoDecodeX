"""
FastAPI route definitions.
"""
import time
from fastapi import APIRouter, UploadFile, File, HTTPException
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
    import hashlib
    import math
    from collections import Counter
    from backend.engine.file_handler import validate_and_save_temp_file, cleanup_temp_file
    
    temp_path = None
    try:
        # Validate size up to 50MB and save securely
        temp_path, content = await validate_and_save_temp_file(
            file,
            max_size=50 * 1024 * 1024, # 50MB
            allowed_extensions=None,
            allowed_mime_types=None,
            validate_magic=False
        )
        
        # 1. Hashes
        sha256 = hashlib.sha256(content).hexdigest()
        md5 = hashlib.md5(content).hexdigest()
        
        # 2. Entropy
        def _calculate_entropy(data: bytes) -> float:
            if not data:
                return 0.0
            counts = Counter(data)
            total = len(data)
            return -sum((c / total) * math.log2(c / total) for c in counts.values())
        
        entropy = _calculate_entropy(content)
        
        # 3. Magic Bytes
        magic_bytes = " ".join(f"{b:02X}" for b in content[:16])
        
        # 4. Printable Ratio
        printable_count = sum(1 for b in content if 32 <= b <= 126)
        printable_ratio = (printable_count / len(content)) * 100 if len(content) > 0 else 0.0
        
        # 5. Extract Strings
        def _extract_strings(data: bytes, min_len: int = 4) -> list[str]:
            strings = []
            current = []
            for b in data:
                if 32 <= b <= 126:
                    current.append(chr(b))
                else:
                    if len(current) >= min_len:
                        strings.append("".join(current))
                    current = []
            if len(current) >= min_len:
                strings.append("".join(current))
            return strings[:100]
            
        strings = _extract_strings(content)
        
        # 6. Metadata pipeline
        meta_result = full_metadata_pipeline(content)
        file_type = meta_result["metadata"]["file_info"].get("format", "Unknown")
        
        # 7. LSB & Entropy details (if it's an image)
        lsb_result = None
        lsb_decode = None
        entropy_details = None
        
        is_image = file_type in ("PNG image", "JPEG image", "BMP image", "GIF image", "PNG", "JPEG", "BMP") or file.content_type in ("image/png", "image/jpeg", "image/jpg", "image/bmp", "image/webp")
        if is_image:
            try:
                lsb_result = extract_lsb(content, bits=1, channels="RGB", password=None)
                entropy_details = analyze_entropy(content)
                
                # Auto-decode LSB text if present
                lsb_text = lsb_result.get("ascii_text", "")
                if lsb_text and len(lsb_text) >= 4:
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
                
        return {
            "name": file.filename,
            "filename": file.filename,
            "size": len(content),
            "type": file_type,
            "sha256": sha256,
            "md5": md5,
            "entropy": round(entropy, 4),
            "strings": strings,
            "printableRatio": round(printable_ratio, 2),
            "magicBytes": magic_bytes,
            "metadata": meta_result,
            "lsb": lsb_result,
            "lsb_decode": lsb_decode,
            "entropy_details": entropy_details,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail={"status": "error", "message": f"File analysis failed: {str(e)}"}
        )
    finally:
        if temp_path:
            cleanup_temp_file(temp_path)


@router.get("/health")
def health():
    return {"status": "ok", "service": "AutoDecodeX"}
