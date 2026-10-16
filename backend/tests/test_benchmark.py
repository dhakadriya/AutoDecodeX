"""
Tests for the benchmark module.
"""
from __future__ import annotations

import pytest


class TestDatasetGeneration:
    def test_generates_expected_structure(self):
        from backend.benchmark.dataset import generate_dataset
        ds = generate_dataset()
        assert "samples" in ds
        assert "manifest" in ds
        assert "dev_ids" in ds
        assert "eval_ids" in ds

    def test_samples_have_ground_truth(self):
        from backend.benchmark.dataset import generate_dataset
        ds = generate_dataset()
        for s in ds["samples"]:
            assert "ground_truth" in s
            assert isinstance(s["ground_truth"], bool)

    def test_stego_samples_have_payload_info(self):
        from backend.benchmark.dataset import generate_dataset
        ds = generate_dataset()
        stego = [s for s in ds["samples"] if s["label"] == "stego"]
        for s in stego:
            assert s["payload_size_bytes"] is not None
            assert s["embedding_method"] is not None

    def test_cover_samples_have_no_payload(self):
        from backend.benchmark.dataset import generate_dataset
        ds = generate_dataset()
        cover = [s for s in ds["samples"] if s["label"] == "cover"]
        for s in cover:
            assert s["payload_size_bytes"] is None

    def test_dev_eval_no_overlap(self):
        from backend.benchmark.dataset import generate_dataset
        ds = generate_dataset()
        dev_set = set(ds["dev_ids"])
        eval_set = set(ds["eval_ids"])
        assert len(dev_set & eval_set) == 0

    def test_samples_have_sha256(self):
        from backend.benchmark.dataset import generate_dataset
        ds = generate_dataset()
        for s in ds["samples"]:
            assert len(s["sha256"]) == 64

    def test_manifest_has_limitations(self):
        from backend.benchmark.dataset import generate_dataset
        ds = generate_dataset()
        assert "limitations" in ds["manifest"]
        assert len(ds["manifest"]["limitations"]) > 0

    def test_reproducible_with_same_seed(self):
        from backend.benchmark.dataset import generate_dataset
        ds1 = generate_dataset(seed=99)
        ds2 = generate_dataset(seed=99)
        hashes1 = sorted(s["sha256"] for s in ds1["samples"])
        hashes2 = sorted(s["sha256"] for s in ds2["samples"])
        assert hashes1 == hashes2

    def test_different_seed_different_samples(self):
        from backend.benchmark.dataset import generate_dataset
        ds1 = generate_dataset(seed=1)
        ds2 = generate_dataset(seed=2)
        hashes1 = sorted(s["sha256"] for s in ds1["samples"])
        hashes2 = sorted(s["sha256"] for s in ds2["samples"])
        # At least some samples should differ
        assert hashes1 != hashes2


class TestMetricsComputation:
    def test_perfect_classifier(self):
        from backend.benchmark.evaluator import compute_metrics
        y_true = [True, False, True, False]
        y_pred = [True, False, True, False]
        m = compute_metrics(y_true, y_pred)
        assert m["tp"] == 2
        assert m["fp"] == 0
        assert m["tn"] == 2
        assert m["fn"] == 0
        assert m["precision"] == 1.0
        assert m["recall"] == 1.0
        assert m["f1_score"] == 1.0

    def test_all_wrong_classifier(self):
        from backend.benchmark.evaluator import compute_metrics
        y_true = [True, False, True, False]
        y_pred = [False, True, False, True]
        m = compute_metrics(y_true, y_pred)
        assert m["tp"] == 0
        assert m["fn"] == 2
        assert m["recall"] == 0.0

    def test_zero_denominator_precision(self):
        """Precision is None when detector never predicts positive."""
        from backend.benchmark.evaluator import compute_metrics
        y_true = [True, False]
        y_pred = [False, False]
        m = compute_metrics(y_true, y_pred)
        assert m["precision"] is None
        assert "precision" in m["undefined_metrics"]

    def test_zero_denominator_recall(self):
        """Recall is None when there are no positive samples."""
        from backend.benchmark.evaluator import compute_metrics
        y_true = [False, False]
        y_pred = [True, False]
        m = compute_metrics(y_true, y_pred)
        assert m["recall"] is None

    def test_f1_none_when_precision_none(self):
        from backend.benchmark.evaluator import compute_metrics
        y_true = [True, False]
        y_pred = [False, False]
        m = compute_metrics(y_true, y_pred)
        assert m["f1_score"] is None

    def test_confusion_matrix_keys(self):
        from backend.benchmark.evaluator import compute_metrics
        m = compute_metrics([True, False], [True, True])
        cm = m["confusion_matrix"]
        assert all(k in cm for k in ["true_positive", "false_positive", "true_negative", "false_negative"])


class TestBenchmarkRun:
    def test_benchmark_runs_without_error(self):
        from backend.benchmark.evaluator import run_benchmark
        result = run_benchmark(split="all")
        assert "detectors" in result
        assert "dataset_summary" in result

    def test_benchmark_results_have_caveats(self):
        from backend.benchmark.evaluator import run_benchmark
        result = run_benchmark(split="all")
        assert "evaluation_caveats" in result
        assert len(result["evaluation_caveats"]) > 0

    def test_benchmark_results_not_fabricated(self):
        """Results must be computed from actual samples, not hardcoded."""
        from backend.benchmark.evaluator import run_benchmark
        result = run_benchmark(split="all")
        total = result["dataset_summary"]["split_samples"]
        for det_name, det_data in result["detectors"].items():
            m = det_data["metrics"]
            # TP + FP + TN + FN must equal total samples
            assert m["tp"] + m["fp"] + m["tn"] + m["fn"] == total
