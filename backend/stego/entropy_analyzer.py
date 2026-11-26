"""
Entropy analysis for steganography detection.
Detects abnormal randomness patterns in image regions.
"""
from __future__ import annotations
import io
import math
from collections import Counter
from PIL import Image
import numpy as np


def _shannon_entropy(data: bytes | np.ndarray) -> float:
    if isinstance(data, np.ndarray):
        data = data.flatten().tobytes()
    if not data:
        return 0.0
    counts = Counter(data)
    total = len(data)
    return -sum((c / total) * math.log2(c / total) for c in counts.values())


def analyze_entropy(image_bytes: bytes) -> dict:
    """
    Full entropy analysis of an image.
    Returns global entropy, per-channel entropy, block entropy map,
    and a stego_likelihood score.
    """
    img = Image.open(io.BytesIO(image_bytes))
    if img.mode not in ("RGB", "RGBA"):
        img = img.convert("RGB")
    arr = np.array(img)

    # Global entropy
    global_entropy = _shannon_entropy(arr.tobytes())

    # Per-channel entropy
    channel_entropy = {
        "R": round(_shannon_entropy(arr[:, :, 0].tobytes()), 4),
        "G": round(_shannon_entropy(arr[:, :, 1].tobytes()), 4),
        "B": round(_shannon_entropy(arr[:, :, 2].tobytes()), 4),
    }

    # LSB-only entropy (suspicious if high)
    lsb_entropy = {
        "R": round(_shannon_entropy((arr[:, :, 0] & 1).tobytes()), 4),
        "G": round(_shannon_entropy((arr[:, :, 1] & 1).tobytes()), 4),
        "B": round(_shannon_entropy((arr[:, :, 2] & 1).tobytes()), 4),
    }

    # Block entropy map (8x8 blocks)
    block_map = _block_entropy_map(arr)

    # Stego likelihood heuristic
    # Natural images have LSB entropy ~0.9-1.0 (near random)
    # Stego images often have LSB entropy very close to 1.0 (perfectly random)
    avg_lsb = sum(lsb_entropy.values()) / 3
    stego_likelihood = round(min(1.0, max(0.0, (avg_lsb - 0.85) / 0.15)), 3)

    # Chi-square test on LSB distribution
    chi_score = _chi_square_lsb(arr)

    return {
        "global_entropy": round(global_entropy, 4),
        "channel_entropy": channel_entropy,
        "lsb_entropy": lsb_entropy,
        "avg_lsb_entropy": round(avg_lsb, 4),
        "stego_likelihood": stego_likelihood,
        "chi_square_score": round(chi_score, 4),
        "block_entropy_map": block_map,
        "suspicious": stego_likelihood > 0.5 or chi_score > 0.7,
    }


def _block_entropy_map(arr: np.ndarray, block_size: int = 32) -> list[list[float]]:
    """Compute entropy for each block_size x block_size region."""
    h, w = arr.shape[:2]
    rows = []
    for y in range(0, h, block_size):
        row = []
        for x in range(0, w, block_size):
            block = arr[y:y+block_size, x:x+block_size]
            e = _shannon_entropy(block.tobytes())
            row.append(round(e, 3))
        rows.append(row)
    return rows


def _chi_square_lsb(arr: np.ndarray) -> float:
    """
    Chi-square test: in natural images, pairs of values (2k, 2k+1)
    should have similar frequencies. Stego disturbs this.
    Returns a score 0-1 where higher = more suspicious.
    """
    flat = arr[:, :, :3].flatten()
    if len(flat) < 2:
        return 0.0

    counts = np.bincount(flat.astype(np.int64), minlength=256)
    chi = 0.0
    degrees_of_freedom = 0

    for k in range(128):
        count_even = float(counts[2 * k])
        count_odd = float(counts[2 * k + 1])
        expected = (count_even + count_odd) / 2.0
        if expected > 0:
            chi += ((count_even - expected) ** 2) / expected
            degrees_of_freedom += 1

    if degrees_of_freedom == 0:
        return 0.0

    # Normalize to 0-1 range
    normalized = chi / (degrees_of_freedom * 2.0 + 1e-6)
    return float(min(1.0, max(0.0, normalized)))


def compute_sliding_window_entropy(data: bytes, window_size: int = 1024, step_size: int = 512) -> list[dict]:
    """
    Computes Shannon entropy across fixed-size sliding windows over a raw byte stream.
    Used for locating encrypted blobs, compressed sections, or hidden payload injections.
    Returns list of dicts with offset, length, and entropy.
    """
    if not data:
        return []

    # If data is smaller than window, calculate entropy for entire byte sequence
    if len(data) <= window_size:
        return [{"offset": 0, "length": len(data), "entropy": round(_shannon_entropy(data), 4)}]

    results = []
    effective_step = max(1, step_size)
    for offset in range(0, len(data) - window_size + 1, effective_step):
        chunk = data[offset:offset+window_size]
        e = _shannon_entropy(chunk)
        results.append({
            "offset": offset,
            "length": len(chunk),
            "entropy": round(e, 4)
        })
    return results


def detect_entropy_anomalies(windows: list[dict], threshold: float = 7.0) -> list[dict]:
    """
    Identifies contiguous sliding windows where entropy meets or exceeds the threshold.
    Returns list of anomalous regions with start_offset, end_offset, length, and peak_entropy.
    """
    anomalies = []
    in_anomaly = False
    start = 0
    peak = 0.0
    end = 0

    for w in windows:
        if w["entropy"] >= threshold:
            if not in_anomaly:
                in_anomaly = True
                start = w["offset"]
                peak = w["entropy"]
            else:
                peak = max(peak, w["entropy"])
            end = w["offset"] + w["length"]
        else:
            if in_anomaly:
                anomalies.append({
                    "start_offset": start,
                    "end_offset": end,
                    "length": end - start,
                    "peak_entropy": round(peak, 4),
                })
                in_anomaly = False

    if in_anomaly:
        anomalies.append({
            "start_offset": start,
            "end_offset": end,
            "length": end - start,
            "peak_entropy": round(peak, 4),
        })

    return anomalies

