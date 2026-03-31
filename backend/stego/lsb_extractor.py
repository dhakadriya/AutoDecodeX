"""
LSB (Least Significant Bit) steganography extractor.
Supports PNG, JPEG, BMP. Extracts hidden data from RGB channels.
"""
from __future__ import annotations
import io
import math
from typing import Optional
from PIL import Image
import numpy as np


def _load_image(image_bytes: bytes) -> Image.Image:
    img = Image.open(io.BytesIO(image_bytes))
    if img.mode not in ("RGB", "RGBA"):
        img = img.convert("RGB")
    return img


def extract_lsb(
    image_bytes: bytes,
    bits: int = 1,
    channels: str = "RGB",
    password: Optional[str] = None,
) -> dict:
    """
    Extract LSB-encoded data from an image.

    Args:
        image_bytes: Raw image file bytes
        bits: Number of LSBs to extract per channel (1-8)
        channels: Which channels to use: 'R', 'G', 'B', 'RGB'
        password: Optional password for key-based extraction offset

    Returns:
        dict with raw_bits, raw_bytes, ascii_text, hex_text, possible_b64
    """
    img = _load_image(image_bytes)
    arr = np.array(img)

    channel_map = {"R": 0, "G": 1, "B": 2}
    selected = [channel_map[c] for c in channels if c in channel_map]

    # Flatten pixels for selected channels
    pixel_data = arr[:, :, selected].flatten().astype(np.uint8)

    # Optional password-based offset (simple deterministic shift)
    offset = 0
    if password:
        offset = sum(ord(c) for c in password) % len(pixel_data)
        pixel_data = np.roll(pixel_data, -offset)

    # Extract LSBs
    mask = (1 << bits) - 1
    extracted_bits = []
    for px in pixel_data:
        for b in range(bits - 1, -1, -1):
            extracted_bits.append((int(px) >> b) & 1)

    # Convert bits to bytes
    raw_bytes = bytearray()
    for i in range(0, len(extracted_bits) - 7, 8):
        byte_val = 0
        for b in range(8):
            byte_val = (byte_val << 1) | extracted_bits[i + b]
        raw_bytes.append(byte_val)

    # Try to find null-terminated ASCII string
    ascii_text = _extract_ascii(raw_bytes)
    hex_text = raw_bytes[:256].hex()
    possible_b64 = _find_base64_chunks(ascii_text)

    return {
        "raw_bytes_hex": hex_text,
        "ascii_text": ascii_text,
        "possible_b64": possible_b64,
        "bits_used": bits,
        "channels": channels,
        "total_bits_extracted": len(extracted_bits),
    }


def _extract_ascii(raw_bytes: bytearray, max_len: int = 2048) -> str:
    """Extract printable ASCII, stopping at long null runs."""
    result = []
    null_run = 0
    for b in raw_bytes[:max_len]:
        if b == 0:
            null_run += 1
            if null_run > 4:
                break
        elif 32 <= b <= 126:
            null_run = 0
            result.append(chr(b))
        else:
            null_run = 0
            result.append(".")
    return "".join(result).strip(".")


def _find_base64_chunks(text: str) -> list[str]:
    """Find potential Base64 substrings in extracted text."""
    import re
    chunks = re.findall(r'[A-Za-z0-9+/]{16,}={0,2}', text)
    return chunks[:5]


def analyze_lsb(image_bytes: bytes) -> dict:
    """
    Run full LSB analysis: try all channel combos and bit depths 1-4.
    Returns ranked results by readability score.
    """
    from backend.scoring.scorer import score_text

    results = []
    combos = ["R", "G", "B", "RGB"]
    for bits in range(1, 5):
        for ch in combos:
            try:
                extracted = extract_lsb(image_bytes, bits=bits, channels=ch)
                text = extracted["ascii_text"]
                score = score_text(text) if text else 0.0
                results.append({
                    "bits": bits,
                    "channels": ch,
                    "ascii_text": text[:500],
                    "possible_b64": extracted["possible_b64"],
                    "raw_bytes_hex": extracted["raw_bytes_hex"][:128],
                    "score": round(score, 3),
                })
            except Exception:
                pass

    results.sort(key=lambda x: x["score"], reverse=True)
    return {"results": results[:8]}


def get_bit_planes(image_bytes: bytes) -> dict:
    """
    Extract all 8 bit-planes for R, G, B channels.
    Returns base64-encoded PNG images for each plane.
    """
    import base64

    img = _load_image(image_bytes)
    arr = np.array(img)
    planes = {}

    channel_names = ["R", "G", "B"]
    for ci, cname in enumerate(channel_names):
        channel = arr[:, :, ci]
        planes[cname] = {}
        for bit in range(8):
            plane = ((channel >> bit) & 1) * 255
            plane_img = Image.fromarray(plane.astype(np.uint8), mode="L")
            buf = io.BytesIO()
            plane_img.save(buf, format="PNG")
            planes[cname][f"bit{bit}"] = base64.b64encode(buf.getvalue()).decode()

    return planes


def get_pixel_diff_map(image_bytes: bytes) -> str:
    """
    Generate a pixel difference map highlighting LSB anomalies.
    Returns base64-encoded PNG.
    """
    import base64

    img = _load_image(image_bytes)
    arr = np.array(img).astype(np.int16)

    # Highlight pixels where LSB differs from neighbor
    diff = np.zeros(arr.shape[:2], dtype=np.uint8)
    for c in range(3):
        lsb = arr[:, :, c] & 1
        shifted = np.roll(lsb, 1, axis=1)
        diff += (np.abs(lsb - shifted) * 85).astype(np.uint8)

    diff_img = Image.fromarray(diff, mode="L")
    buf = io.BytesIO()
    diff_img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()
