"""
Benchmark evaluator for AutoDecodeX steganalysis detectors.

Usage:
    python -m backend.benchmark.run_benchmark [--output results.json] [--split eval]

Metrics reported:
  TP, FP, TN, FN, Precision, Recall, F1, FPR, Confusion Matrix, Sample Counts.

Zero-denominator handling:
  - Precision is None when TP + FP == 0 (detector never predicted positive).
  - Recall is None when TP + FN == 0 (no positive samples in split).
  - F1 is None when Precision or Recall is None.
  - FPR is None when FP + TN == 0 (no negative samples in split).
  - These are returned as None, NOT as 0 or 1.

Detector configuration is recorded with each run so results are reproducible.
"""
from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from typing import Optional

from backend.models.schemas import ENGINE_VERSION


# ── Detector adapter ───────────────────────────────────────────────────────

def _run_entropy_detector(image_bytes: bytes, threshold: float) -> bool:
    """
    Use the chi-square + stego_likelihood heuristic as a binary classifier.
    Returns True (stego) if stego_likelihood > threshold.
    Threshold is configurable; default 0.5 (documented in config_snapshot).
    """
    from backend.stego.entropy_analyzer import analyze_entropy
    result = analyze_entropy(image_bytes)
    return result.get("stego_likelihood", 0.0) > threshold


def _run_lsb_readability_detector(image_bytes: bytes, score_threshold: float) -> bool:
    """
    Use LSB extraction readability score as a binary classifier.
    Returns True (stego) if the readability score of extracted LSB text > threshold.
    """
    from backend.stego.lsb_extractor import extract_lsb
    from backend.scoring.scorer import score_text
    result = extract_lsb(image_bytes, bits=1, channels="RGB", password=None)
    text = result.get("ascii_text", "")
    score = score_text(text) if text else 0.0
    return score > score_threshold


# ── Metrics ────────────────────────────────────────────────────────────────

def _safe_div(num: float, denom: float) -> Optional[float]:
    """Division with explicit zero-denominator handling. Returns None, not 0."""
    if denom == 0:
        return None
    return round(num / denom, 4)


def compute_metrics(
    y_true: list[bool],
    y_pred: list[bool],
) -> dict:
    """
    Compute classification metrics from ground-truth and predicted labels.
    Returns a dict with all metrics; None for undefined metrics.
    """
    assert len(y_true) == len(y_pred), "Length mismatch"

    tp = sum(1 for t, p in zip(y_true, y_pred) if t and p)
    fp = sum(1 for t, p in zip(y_true, y_pred) if not t and p)
    tn = sum(1 for t, p in zip(y_true, y_pred) if not t and not p)
    fn = sum(1 for t, p in zip(y_true, y_pred) if t and not p)

    precision = _safe_div(tp, tp + fp)
    recall = _safe_div(tp, tp + fn)
    fpr = _safe_div(fp, fp + tn)

    f1: Optional[float] = None
    if precision is not None and recall is not None:
        denom = precision + recall
        f1 = _safe_div(2 * precision * recall, denom) if denom > 0 else None

    return {
        "tp": tp, "fp": fp, "tn": tn, "fn": fn,
        "total_samples": len(y_true),
        "positive_samples": sum(y_true),
        "negative_samples": sum(not t for t in y_true),
        "precision": precision,
        "recall": recall,
        "f1_score": f1,
        "false_positive_rate": fpr,
        "confusion_matrix": {
            "true_positive": tp, "false_positive": fp,
            "true_negative": tn, "false_negative": fn,
        },
        "undefined_metrics": [
            k for k, v in {"precision": precision, "recall": recall,
                            "f1_score": f1, "false_positive_rate": fpr}.items()
            if v is None
        ],
    }


# ── Main evaluator ─────────────────────────────────────────────────────────

def run_benchmark(
    split: str = "eval",
    entropy_threshold: float = 0.5,
    lsb_score_threshold: float = 0.5,
    seed: int = 42,
) -> dict:
    """
    Generate the dataset, run both detectors, compute metrics.

    split: "dev", "eval", or "all" — which samples to evaluate.
    Returns a full benchmark report dict.
    """
    from backend.benchmark.dataset import generate_dataset

    t0 = time.monotonic()
    dataset = generate_dataset(seed=seed)
    samples = dataset["samples"]
    manifest = dataset["manifest"]

    # Filter by split
    if split != "all":
        samples = [s for s in samples if s["dataset_split"] == split]

    y_true = [s["ground_truth"] for s in samples]

    # Entropy detector
    entropy_preds: list[bool] = []
    entropy_errors: list[str] = []
    for s in samples:
        try:
            pred = _run_entropy_detector(s["image_bytes"], entropy_threshold)
            entropy_preds.append(pred)
        except Exception as exc:
            entropy_preds.append(False)
            entropy_errors.append(f"Sample {s['sample_id'][:8]}: {exc}")

    # LSB readability detector
    lsb_preds: list[bool] = []
    lsb_errors: list[str] = []
    for s in samples:
        try:
            pred = _run_lsb_readability_detector(s["image_bytes"], lsb_score_threshold)
            lsb_preds.append(pred)
        except Exception as exc:
            lsb_preds.append(False)
            lsb_errors.append(f"Sample {s['sample_id'][:8]}: {exc}")

    elapsed_ms = round((time.monotonic() - t0) * 1000, 2)

    return {
        "benchmark_id": f"adx-bench-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "engine_version": ENGINE_VERSION,
        "dataset_version": manifest["dataset_version"],
        "split_evaluated": split,
        "total_ms": elapsed_ms,
        "dataset_summary": {
            "total_samples": manifest["total_samples"],
            "split_samples": len(samples),
            "cover_count": sum(1 for s in samples if not s["ground_truth"]),
            "stego_count": sum(1 for s in samples if s["ground_truth"]),
        },
        "detectors": {
            "entropy_chi_square": {
                "description": (
                    "Chi-square + LSB entropy heuristic. Classifies as stego if "
                    "stego_likelihood > threshold. "
                    "stego_likelihood = max(0, min(1, (avg_lsb_entropy - 0.85) / 0.15)). "
                    "This is a HEURISTIC PRIORITY SCORE, not a probability."
                ),
                "config": {
                    "threshold": entropy_threshold,
                    "engine_version": ENGINE_VERSION,
                },
                "metrics": compute_metrics(y_true, entropy_preds),
                "errors": entropy_errors,
            },
            "lsb_readability": {
                "description": (
                    "Extracts 1-bit RGB LSB bytes and scores readability using the "
                    "AutoDecodeX text scorer. Classifies as stego if score > threshold."
                ),
                "config": {
                    "bits": 1,
                    "channels": "RGB",
                    "score_threshold": lsb_score_threshold,
                    "engine_version": ENGINE_VERSION,
                },
                "metrics": compute_metrics(y_true, lsb_preds),
                "errors": lsb_errors,
            },
        },
        "dataset_limitations": manifest["limitations"],
        "evaluation_caveats": [
            "Results are from a preliminary synthetic dataset only.",
            "Synthetic uniform/gradient images do not represent real-world photographs.",
            "Detector thresholds were not tuned on a separate validation set.",
            "Sample counts are small; confidence intervals are wide.",
            "No comparison against external tools has been performed.",
        ],
        "manifest": manifest,
    }
