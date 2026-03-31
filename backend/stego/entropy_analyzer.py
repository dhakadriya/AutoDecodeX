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
    pairs = [(flat[i] & ~1, flat[i] | 1) for i in range(0, len(flat) - 1, 2)]

    chi = 0.0
    total = len(pairs)
    if total == 0:
        return 0.0

    for even, odd in pairs:
        count_even = int(np.sum(flat == even))
        count_odd = int(np.sum(flat == odd))
        expected = (count_even + count_odd) / 2
        if expected > 0:
            chi += ((count_even - expected) ** 2) / expected

    # Normalize to 0-1
    return min(1.0, chi / (total * 10))
