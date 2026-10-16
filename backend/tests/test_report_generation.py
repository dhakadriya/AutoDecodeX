"""
Tests for JSON and PDF report generation.
"""
from __future__ import annotations

import hashlib
import json

import pytest

from backend.engine.analysis_orchestrator import run_full_analysis, build_report
from backend.engine.report_generator import report_to_json, report_to_pdf
from backend.tests.demo_dataset import generate_test_image


@pytest.fixture
def simple_case():
    return run_full_analysis("report_test.txt", b"Hello World! AutoDecodeX forensics report test.")


@pytest.fixture
def image_case():
    return run_full_analysis("report_image.png", generate_test_image())


class TestJSONReport:
    def test_json_is_valid(self, simple_case):
        report = build_report(simple_case)
        json_str = report_to_json(report)
        data = json.loads(json_str)
        assert isinstance(data, dict)

    def test_json_contains_required_fields(self, simple_case):
        report = build_report(simple_case)
        data = json.loads(report_to_json(report))
        required = [
            "report_id", "case_id", "generated_at_utc",
            "original_filename", "sha256", "md5",
            "app_version", "engine_version",
            "modules_run", "findings",
            "scope_statement", "limitations", "final_summary",
        ]
        for f in required:
            assert f in data, f"Missing: {f}"

    def test_sha256_in_report_matches_case(self, simple_case):
        report = build_report(simple_case)
        data = json.loads(report_to_json(report))
        assert data["sha256"] == simple_case.sha256

    def test_json_does_not_contain_traceback(self, simple_case):
        report = build_report(simple_case)
        json_str = report_to_json(report)
        assert "Traceback" not in json_str
        assert "File \"/" not in json_str

    def test_findings_in_report_match_case(self, simple_case):
        report = build_report(simple_case)
        data = json.loads(report_to_json(report))
        assert len(data["findings"]) == len(simple_case.findings)

    def test_long_values_are_truncated(self, simple_case):
        report = build_report(simple_case)
        json_str = report_to_json(report)
        # No single string value should exceed _MAX_VALUE_CHARS + truncation suffix
        data = json.loads(json_str)
        def check_lengths(obj):
            if isinstance(obj, str):
                assert len(obj) <= 550, f"Value too long: {len(obj)} chars"
            elif isinstance(obj, dict):
                for v in obj.values():
                    check_lengths(v)
            elif isinstance(obj, list):
                for item in obj:
                    check_lengths(item)
        check_lengths(data)

    def test_scope_statement_present(self, simple_case):
        report = build_report(simple_case)
        data = json.loads(report_to_json(report))
        assert "scope_statement" in data
        assert len(data["scope_statement"]) > 50

    def test_limitations_list_not_empty(self, simple_case):
        report = build_report(simple_case)
        data = json.loads(report_to_json(report))
        assert isinstance(data["limitations"], list)
        assert len(data["limitations"]) > 0

    def test_failed_modules_reported(self, simple_case):
        report = build_report(simple_case)
        data = json.loads(report_to_json(report))
        assert "modules_failed" in data
        assert isinstance(data["modules_failed"], list)

    def test_image_case_has_stego_findings(self, image_case):
        report = build_report(image_case)
        data = json.loads(report_to_json(report))
        stego = [f for f in data["findings"] if f["category"] == "steganalysis"]
        assert len(stego) > 0


class TestPDFReport:
    def test_pdf_generation_or_error(self, simple_case):
        """PDF generation either succeeds or raises ImportError (fpdf2 not installed)."""
        report = build_report(simple_case)
        try:
            pdf_bytes = report_to_pdf(report)
            assert isinstance(pdf_bytes, bytes)
            assert len(pdf_bytes) > 100
            assert pdf_bytes[:4] == b"%PDF"
        except ImportError:
            pytest.skip("fpdf2 not installed — PDF generation not tested")

    def test_pdf_contains_case_id(self, simple_case):
        report = build_report(simple_case)
        try:
            pdf_bytes = report_to_pdf(report)
            # Case ID should appear in PDF text
            content = pdf_bytes.decode("latin-1", errors="replace")
            assert simple_case.case_id[:8] in content
        except ImportError:
            pytest.skip("fpdf2 not installed")

    def test_pdf_and_json_agree_on_sha256(self, simple_case):
        report = build_report(simple_case)
        json_data = json.loads(report_to_json(report))
        try:
            pdf_bytes = report_to_pdf(report)
            content = pdf_bytes.decode("latin-1", errors="replace")
            assert json_data["sha256"][:16] in content
        except ImportError:
            pytest.skip("fpdf2 not installed")
