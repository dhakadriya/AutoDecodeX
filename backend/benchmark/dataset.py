"""
Reproducible benchmark dataset for AutoDecodeX steganalysis detectors.

Dataset design:
  - All images are self-generated (no third-party assets, no licensing issues).
  - Cover images: uniform-colour and gradient PNG images (no natural photos).
  - Stego images: same covers with known LSB payloads embedded at specified depths.
  - Ground-truth labels are recorded alongside each sample.
  - Dataset version and manifest are exported as JSON.
  - Development and held-out evaluation sets are explicitly separated.
  - Near-duplicate images are prevented by using distinct seeds/colours.

Limitations:
  - This is a preliminary synthetic dataset. Results on synthetic images
    should NOT be reported as accuracy on real-world photographs.
  - Uniform/gradient images have predictably low or high LSB entropy;
    a detector trained or tuned on this data may not generalise.
  - Sample count is small (configurable). Results should be labelled
    "preliminary synthetic benchmark" in any report.

Documented metrics:
  - True Positives (TP), False Positives (FP), True Negatives (TN), False Negatives (FN)
  - Precision = TP / (TP + FP)   [undefined when TP+FP = 0 → None]
  - Recall    = TP / (TP + FN)   [undefined when TP+FN = 0 → None]
  - F1        = 2 * P * R / (P + R) [undefined when P or R is None → None]
  - False-Positive Rate = FP / (FP + TN) [undefined when FP+TN = 0 → None]
  - Confusion matrix

Zero-denominator handling: undefined metrics are returned as None, NOT as 0.
"""
from __future__ import annotations

import hashlib
import io
import json
import math
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

import numpy as np
from PIL import Image
from PIL.PngImagePlugin import PngInfo

DATASET_VERSION = "1.0.0-preliminary-synthetic"


# ── Sample generation ──────────────────────────────────────────────────────

def _make_cover(width: int, height: int, color: tuple, seed: int) -> bytes:
    """Generate a clean cover image with a slight gradient to avoid uniform entropy."""
    rng = np.random.default_rng(seed)
    noise = rng.integers(0, 8, (height, width, 3), dtype=np.uint8)
    base = np.array([[color] * width] * height, dtype=np.uint8)
    arr = np.clip(base.astype(np.int16) + noise - 4, 0, 255).astype(np.uint8)
    img = Image.fromarray(arr, mode="RGB")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _embed_lsb(cover_bytes: bytes, payload: bytes) -> bytes:
    """Embed payload bytes into the LSB of the R channel of a cover image."""
    img = Image.open(io.BytesIO(cover_bytes)).convert("RGB")
    arr = np.array(img)
    bits = []
    for b in payload:
        for i in range(7, -1, -1):
            bits.append((b >> i) & 1)
    flat = arr[:, :, 0].ravel()
    if len(bits) > len(flat):
        raise ValueError(f"Payload too large: {len(bits)} bits, capacity {len(flat)} bits")
    for idx, bit in enumerate(bits):
        flat[idx] = (int(flat[idx]) & ~1) | bit
    stego = Image.fromarray(arr, mode="RGB")
    buf = io.BytesIO()
    stego.save(buf, format="PNG")
    return buf.getvalue()


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def generate_dataset(
    cover_sizes: list[tuple[int, int]] = None,
    payloads: list[bytes] = None,
    dev_fraction: float = 0.6,
    seed: int = 42,
) -> dict:
    """
    Generate a reproducible dataset.
    Returns a dict with 'samples', 'manifest', 'dev_ids', 'eval_ids'.
    Does NOT mix dev/eval: indices are chosen deterministically from the seed.

    cover_sizes: list of (width, height) tuples for cover images
    payloads: list of byte payloads to embed
    dev_fraction: proportion allocated to development set (rest = held-out evaluation)
    """
    if cover_sizes is None:
        cover_sizes = [(32, 32), (64, 64), (128, 128), (64, 64), (128, 64)]
    if payloads is None:
        payloads = [
            b"flag{lsb_payload_short}",
            b"flag{lsb_payload_medium}" * 2,
            b"AutoDecodeX benchmark payload for LSB detection test.",
            b"\x00\x01\x02\x03\x04\x05\x06\x07",
        ]

    colors = [
        (100, 120, 140),
        (200, 180, 160),
        (60, 80, 100),
        (220, 200, 180),
        (140, 160, 120),
    ]

    rng = np.random.default_rng(seed)
    samples: list[dict] = []

    for i, (w, h) in enumerate(cover_sizes):
        color = colors[i % len(colors)]
        cover_seed = seed + i * 17
        cover_bytes = _make_cover(w, h, color, cover_seed)
        cover_hash = _sha256(cover_bytes)

        # Cover (negative) sample
        samples.append({
            "sample_id": str(uuid.UUID(int=rng.integers(0, 2**128))),
            "label": "cover",
            "ground_truth": False,
            "image_bytes": cover_bytes,
            "sha256": cover_hash,
            "width": w,
            "height": h,
            "format": "PNG",
            "embedding_method": None,
            "payload_size_bytes": None,
            "payload_ratio": None,
            "preprocessing": "slight_noise_gradient",
            "dataset_split": None,   # assigned below
        })

        # Stego (positive) samples with each payload
        for j, payload in enumerate(payloads):
            capacity_bits = w * h
            if len(payload) * 8 > capacity_bits:
                continue  # skip if payload won't fit
            try:
                stego_bytes = _embed_lsb(cover_bytes, payload)
                stego_hash = _sha256(stego_bytes)
                samples.append({
                    "sample_id": str(uuid.UUID(int=rng.integers(0, 2**128))),
                    "label": "stego",
                    "ground_truth": True,
                    "image_bytes": stego_bytes,
                    "sha256": stego_hash,
                    "width": w,
                    "height": h,
                    "format": "PNG",
                    "embedding_method": "lsb_r_channel_1bit",
                    "payload_size_bytes": len(payload),
                    "payload_ratio": round(len(payload) * 8 / capacity_bits, 4),
                    "preprocessing": "slight_noise_gradient",
                    "dataset_split": None,
                })
            except ValueError:
                pass

    # Assign dev/eval splits deterministically
    indices = list(range(len(samples)))
    rng.shuffle(indices)
    n_dev = max(1, int(len(indices) * dev_fraction))
    dev_indices = set(indices[:n_dev])
    eval_indices = set(indices[n_dev:])

    dev_ids = []
    eval_ids = []
    for idx, s in enumerate(samples):
        s["dataset_split"] = "dev" if idx in dev_indices else "eval"
        if idx in dev_indices:
            dev_ids.append(s["sample_id"])
        else:
            eval_ids.append(s["sample_id"])

    # Remove image_bytes from the manifest representation (keep in samples)
    manifest = {
        "dataset_version": DATASET_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "seed": seed,
        "total_samples": len(samples),
        "cover_count": sum(1 for s in samples if s["label"] == "cover"),
        "stego_count": sum(1 for s in samples if s["label"] == "stego"),
        "dev_count": len(dev_ids),
        "eval_count": len(eval_ids),
        "cover_sizes": cover_sizes,
        "payloads_count": len(payloads),
        "dev_fraction": dev_fraction,
        "class_distribution": {
            "cover": sum(1 for s in samples if s["label"] == "cover"),
            "stego": sum(1 for s in samples if s["label"] == "stego"),
        },
        "limitations": [
            "All images are self-generated synthetic images, not natural photographs.",
            "Results on this dataset should be labelled 'preliminary synthetic benchmark'.",
            "Detector performance on real-world images may differ significantly.",
            "The dataset is small; confidence intervals are wide.",
        ],
        "samples": [
            {k: v for k, v in s.items() if k != "image_bytes"}
            for s in samples
        ],
    }

    return {"samples": samples, "manifest": manifest, "dev_ids": dev_ids, "eval_ids": eval_ids}
