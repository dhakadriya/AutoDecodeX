"""
Steganography API routes.
"""
from __future__ import annotations
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pydantic import BaseModel
from typing import Optional
import base64

from backend.stego.lsb_extractor import extract_lsb, analyze_lsb, get_bit_planes, get_pixel_diff_map
from backend.stego.entropy_analyzer import analyze_entropy
from backend.stego.text_stego import extract_text_stego
from backend.stego.metadata_analyzer import full_metadata_pipeline
from backend.engine.orchestrator import decode as auto_decode
from backend.scoring.scorer import score_text

stego_router = APIRouter(prefix="/api/stego")

ALLOWED_TYPES = {"image/png", "image/jpeg", "image/jpg", "image/bmp", "image/webp"}
MAX_SIZE = 10 * 1024 * 1024  # 10 MB


def _validate_image(file: UploadFile):
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(400, f"Unsupported file type: {file.content_type}. Use PNG, JPEG, or BMP.")


@stego_router.post("/analyze")
async def analyze_image(
    file: UploadFile = File(...),
    bits: int = Form(1),
    channels: str = Form("RGB"),
    password: Optional[str] = Form(None),
    auto_decode_flag: bool = Form(True),
):
    """
    Full steganography analysis pipeline:
    1. LSB extraction
    2. Entropy analysis
    3. Auto-decode extracted data
    """
    _validate_image(file)
    image_bytes = await file.read()
    if len(image_bytes) > MAX_SIZE:
        raise HTTPException(413, "Image too large. Max 10MB.")

    bits = max(1, min(8, bits))

    # LSB extraction
    lsb_result = extract_lsb(image_bytes, bits=bits, channels=channels, password=password or None)

    # Entropy analysis
    entropy_result = analyze_entropy(image_bytes)

    # Auto-decode extracted text if enabled
    decode_result = None
    extracted_text = lsb_result.get("ascii_text", "")
    if auto_decode_flag and extracted_text and len(extracted_text) >= 4:
        try:
            dr = auto_decode(extracted_text)
            decode_result = {
                "success": dr.success,
                "final_output": dr.final_output,
                "total_score": round(dr.total_score, 3),
                "path_description": dr.path_description,
                "is_ctf_flag": dr.is_ctf_flag,
                "steps": [
                    {
                        "step_number": s.step_number,
                        "encoding_type": s.encoding_type,
                        "confidence": s.confidence,
                        "output_text": s.output_text[:300],
                        "score": round(s.score, 3),
                    }
                    for s in dr.steps
                ],
            }
        except Exception as e:
            decode_result = {"error": str(e)}

    return {
        "filename": file.filename,
        "lsb": lsb_result,
        "entropy": {
            "global_entropy": entropy_result["global_entropy"],
            "channel_entropy": entropy_result["channel_entropy"],
            "lsb_entropy": entropy_result["lsb_entropy"],
            "stego_likelihood": entropy_result["stego_likelihood"],
            "chi_square_score": entropy_result["chi_square_score"],
            "suspicious": entropy_result["suspicious"],
        },
        "auto_decode": decode_result,
    }


@stego_router.post("/brute-force")
async def brute_force_lsb(
    file: UploadFile = File(...),
    auto_decode_flag: bool = Form(True),
):
    """Try all LSB combinations and rank by readability."""
    _validate_image(file)
    image_bytes = await file.read()
    if len(image_bytes) > MAX_SIZE:
        raise HTTPException(413, "Image too large.")

    analysis = analyze_lsb(image_bytes)
    results = analysis["results"]

    # Auto-decode top results
    if auto_decode_flag:
        for r in results[:3]:
            text = r.get("ascii_text", "")
            if text and len(text) >= 4:
                try:
                    dr = auto_decode(text)
                    r["decode_result"] = {
                        "final_output": dr.final_output,
                        "path_description": dr.path_description,
                        "is_ctf_flag": dr.is_ctf_flag,
                        "total_score": round(dr.total_score, 3),
                    }
                except Exception:
                    pass

    return {"results": results}


@stego_router.post("/bit-planes")
async def bit_planes(file: UploadFile = File(...)):
    """Return all 8 bit-planes for R, G, B channels as base64 PNGs."""
    _validate_image(file)
    image_bytes = await file.read()
    if len(image_bytes) > MAX_SIZE:
        raise HTTPException(413, "Image too large.")
    planes = get_bit_planes(image_bytes)
    return {"planes": planes}


@stego_router.post("/pixel-diff")
async def pixel_diff(file: UploadFile = File(...)):
    """Return pixel difference map as base64 PNG."""
    _validate_image(file)
    image_bytes = await file.read()
    if len(image_bytes) > MAX_SIZE:
        raise HTTPException(413, "Image too large.")
    diff_b64 = get_pixel_diff_map(image_bytes)
    return {"diff_map": diff_b64}


@stego_router.post("/text")
async def analyze_text_stego(payload: dict):
    """Analyze text for steganographic content."""
    text = payload.get("text", "")
    if not text:
        raise HTTPException(400, "No text provided.")
    result = extract_text_stego(text)

    # Auto-decode any zero-width findings
    zw = result.get("zero_width", {})
    decoded_zw = zw.get("decoded", "")
    if decoded_zw and len(decoded_zw) >= 4:
        try:
            dr = auto_decode(decoded_zw)
            result["zero_width"]["auto_decode"] = {
                "final_output": dr.final_output,
                "is_ctf_flag": dr.is_ctf_flag,
            }
        except Exception:
            pass

    return result


@stego_router.post("/metadata")
async def metadata_endpoint(file: UploadFile = File(...)):
    """
    Full metadata extraction + analysis pipeline.
    Extracts EXIF, PNG text chunks, scans for encoded values,
    auto-decodes suspicious fields, detects embedded files.
    """
    _validate_image(file)
    image_bytes = await file.read()
    if len(image_bytes) > MAX_SIZE:
        raise HTTPException(413, "Image too large. Max 10MB.")

    result = full_metadata_pipeline(image_bytes)
    return result


@stego_router.post("/full-scan")
async def full_scan(
    file: UploadFile = File(...),
    bits: int = Form(1),
    channels: str = Form("RGB"),
    password: Optional[str] = Form(None),
):
    """
    Complete unified pipeline:
    Step 1: Metadata extraction + analysis
    Step 2: LSB extraction
    Step 3: Entropy analysis
    Step 4: Embedded file scan
    Step 5: Auto-decode all findings
    Returns merged ranked results.
    """
    _validate_image(file)
    image_bytes = await file.read()
    if len(image_bytes) > MAX_SIZE:
        raise HTTPException(413, "Image too large. Max 10MB.")

    bits = max(1, min(8, bits))

    # Run all analyses
    meta_result = full_metadata_pipeline(image_bytes)
    lsb_result = extract_lsb(image_bytes, bits=bits, channels=channels, password=password or None)
    entropy_result = analyze_entropy(image_bytes)

    # Auto-decode LSB text
    lsb_decode = None
    lsb_text = lsb_result.get("ascii_text", "")
    if lsb_text and len(lsb_text) >= 4:
        try:
            dr = auto_decode(lsb_text)
            lsb_decode = {
                "final_output": dr.final_output,
                "path_description": dr.path_description,
                "total_score": round(dr.total_score, 3),
                "is_ctf_flag": dr.is_ctf_flag,
                "steps": [
                    {
                        "step_number": s.step_number,
                        "encoding_type": s.encoding_type,
                        "confidence": s.confidence,
                        "output_text": s.output_text[:200],
                        "score": round(s.score, 3),
                    }
                    for s in dr.steps
                ],
            }
        except Exception:
            pass

    # Collect all flags from all sources
    all_flags = list(set(
        meta_result["analysis"]["flags_found"] +
        ([lsb_decode["final_output"]] if lsb_decode and lsb_decode.get("is_ctf_flag") else [])
    ))

    return {
        "filename": file.filename,
        "metadata": meta_result,
        "lsb": lsb_result,
        "lsb_decode": lsb_decode,
        "entropy": {
            "global_entropy": entropy_result["global_entropy"],
            "channel_entropy": entropy_result["channel_entropy"],
            "lsb_entropy": entropy_result["lsb_entropy"],
            "stego_likelihood": entropy_result["stego_likelihood"],
            "chi_square_score": entropy_result["chi_square_score"],
            "suspicious": entropy_result["suspicious"],
        },
        "all_flags": all_flags,
        "summary": {
            **meta_result["summary"],
            "lsb_suspicious": entropy_result["suspicious"],
            "total_flags": len(all_flags),
        },
    }
