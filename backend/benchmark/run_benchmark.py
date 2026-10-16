"""
CLI entry point for benchmark evaluation.

Usage:
    python -m backend.benchmark.run_benchmark
    python -m backend.benchmark.run_benchmark --output results.json --split eval
    python -m backend.benchmark.run_benchmark --split all --entropy-threshold 0.4

Options:
    --output PATH         Path to write JSON results (default: benchmark_results.json)
    --split SPLIT         Dataset split: dev | eval | all (default: eval)
    --entropy-threshold   Float threshold for entropy detector (default: 0.5)
    --lsb-threshold       Float threshold for LSB readability detector (default: 0.5)
    --seed INT            Random seed for reproducibility (default: 42)
    --no-overwrite        Fail if output file already exists

IMPORTANT: This command does NOT mix benchmark results with ordinary case analysis.
           It uses a separate, labelled synthetic dataset.
"""
from __future__ import annotations

import argparse
import json
import os
import sys


def main():
    parser = argparse.ArgumentParser(description="AutoDecodeX steganalysis benchmark")
    parser.add_argument("--output", default="benchmark_results.json")
    parser.add_argument("--split", choices=["dev", "eval", "all"], default="eval")
    parser.add_argument("--entropy-threshold", type=float, default=0.5)
    parser.add_argument("--lsb-threshold", type=float, default=0.5)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--no-overwrite", action="store_true")
    args = parser.parse_args()

    if args.no_overwrite and os.path.exists(args.output):
        print(f"ERROR: Output file '{args.output}' already exists. Use a different path or remove --no-overwrite.", file=sys.stderr)
        sys.exit(1)

    from backend.benchmark.evaluator import run_benchmark

    print(f"Running benchmark on split='{args.split}'...")
    results = run_benchmark(
        split=args.split,
        entropy_threshold=args.entropy_threshold,
        lsb_score_threshold=args.lsb_threshold,
        seed=args.seed,
    )

    # Remove image bytes from output (too large for a JSON report)
    for s in results.get("manifest", {}).get("samples", []):
        s.pop("image_bytes", None)

    output_path = args.output
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, default=str)

    detectors = results["detectors"]
    print("\n=== Benchmark Results ===")
    print(f"Dataset: {results['dataset_version']}")
    print(f"Split: {results['split_evaluated']} | Samples: {results['dataset_summary']['split_samples']}")
    print(f"  Cover: {results['dataset_summary']['cover_count']} | Stego: {results['dataset_summary']['stego_count']}")
    print()
    for name, det in detectors.items():
        m = det["metrics"]
        print(f"Detector: {name}")
        print(f"  TP={m['tp']} FP={m['fp']} TN={m['tn']} FN={m['fn']}")
        print(f"  Precision={m['precision']} Recall={m['recall']} F1={m['f1_score']} FPR={m['false_positive_rate']}")
        if m["undefined_metrics"]:
            print(f"  Undefined (zero denominator): {', '.join(m['undefined_metrics'])}")
        if det["errors"]:
            print(f"  Errors: {len(det['errors'])}")
        print()
    print("IMPORTANT: These are preliminary synthetic-dataset results only.")
    print(f"Full results written to: {output_path}")


if __name__ == "__main__":
    main()
