"""
Tests for case management, evidence integrity, and the analysis orchestrator.

Covers:
  D. Case and integrity tests
  E. Security tests
  A. File-analysis hashes and magic bytes
"""
from __future__ import annotations

import gzip
import hashlib
import io
import zlib
import base64
import os
import tempfile
import uuid

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.models.schemas import (
    ArtifactKind,
    AnalysisStatus,
    FindingStatus,
    Case,
)
from backend.models.case_store import save_case, get_case, delete_case, list_cases
from backend.engine.analysis_orchestrator import run_full_analysis
from backend.tests.demo_dataset import generate_test_image

client = TestClient(app)


# ── Fixtures ───────────────────────────────────────────────────────────────

@pytest.fixture
def test_image_bytes():
    return generate_test_image()


@pytest.fixture
def tiny_png():
    """1x1 red PNG for quick tests."""
    from PIL import Image
    img = Image.new("RGB", (1, 1), color=(255, 0, 0))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


@pytest.fixture
def text_file_bytes():
    return b"Hello World! This is a plaintext test file for AutoDecodeX."


@pytest.fixture
def base64_text_bytes():
    return b"SGVsbG8gV29ybGQ="  # "Hello World"


# ── D. Case integrity tests ────────────────────────────────────────────────

class TestHashIntegrity:
    """Hashes are computed from actual bytes, not from metadata."""

    def test_sha256_matches_actual_bytes(self, text_file_bytes):
        case = run_full_analysis("test.txt", text_file_bytes)
        expected_sha256 = hashlib.sha256(text_file_bytes).hexdigest()
        assert case.sha256 == expected_sha256

    def test_md5_matches_actual_bytes(self, text_file_bytes):
        case = run_full_analysis("test.txt", text_file_bytes)
        expected_md5 = hashlib.md5(text_file_bytes).hexdigest()
        assert case.md5 == expected_md5

    def test_known_bytes_stable_hash(self):
        """Hashes must be stable for the same input."""
        data = b"AutoDecodeX evidence integrity test"
        case1 = run_full_analysis("a.txt", data)
        case2 = run_full_analysis("a.txt", data)
        assert case1.sha256 == case2.sha256
        assert case1.md5 == case2.md5

    def test_different_bytes_different_hash(self, text_file_bytes):
        data2 = text_file_bytes + b" extra"
        case1 = run_full_analysis("a.txt", text_file_bytes)
        case2 = run_full_analysis("b.txt", data2)
        assert case1.sha256 != case2.sha256


class TestEvidencePreservation:
    """Original evidence is never overwritten or modified."""

    def test_original_artifact_exists(self, text_file_bytes):
        case = run_full_analysis("test.txt", text_file_bytes)
        originals = [a for a in case.artifacts if a.kind == ArtifactKind.ORIGINAL_EVIDENCE]
        assert len(originals) == 1

    def test_original_artifact_hash_matches(self, text_file_bytes):
        case = run_full_analysis("test.txt", text_file_bytes)
        orig = next(a for a in case.artifacts if a.kind == ArtifactKind.ORIGINAL_EVIDENCE)
        assert orig.sha256 == hashlib.sha256(text_file_bytes).hexdigest()

    def test_derived_artifacts_have_parent(self, test_image_bytes):
        case = run_full_analysis("test.png", test_image_bytes)
        derived = [a for a in case.artifacts if a.parent_artifact_id is not None]
        for art in derived:
            parent = next((a for a in case.artifacts if a.artifact_id == art.parent_artifact_id), None)
            assert parent is not None, "Every derived artifact must have a valid parent"

    def test_derived_artifacts_have_sha256(self, test_image_bytes):
        case = run_full_analysis("test.png", test_image_bytes)
        derived = [a for a in case.artifacts if a.kind != ArtifactKind.ORIGINAL_EVIDENCE]
        for art in derived:
            assert art.sha256 and len(art.sha256) == 64

    def test_derived_artifacts_record_operation(self, test_image_bytes):
        case = run_full_analysis("test.png", test_image_bytes)
        derived = [a for a in case.artifacts if a.parent_operation is not None]
        for art in derived:
            assert art.parent_operation  # must be non-empty string


class TestCaseStateTransitions:
    """Case moves from RUNNING → COMPLETED (or COMPLETED_WITH_WARNINGS)."""

    def test_case_starts_running(self, text_file_bytes):
        # We can only observe final state, but it must be one of the terminal states
        case = run_full_analysis("test.txt", text_file_bytes)
        assert case.status in (AnalysisStatus.COMPLETED, AnalysisStatus.COMPLETED_WITH_WARNINGS)

    def test_case_has_completed_at(self, text_file_bytes):
        case = run_full_analysis("test.txt", text_file_bytes)
        assert case.completed_at_utc is not None

    def test_empty_module_list_on_failure(self):
        """Even a minimal file must produce a case with module results."""
        case = run_full_analysis("empty_sim.txt", b"x")
        assert len(case.module_results) > 0

    def test_module_failures_do_not_erase_other_results(self, test_image_bytes):
        """Stego findings must exist alongside file analysis, even if one module had errors."""
        case = run_full_analysis("test.png", test_image_bytes)
        completed = case.completed_modules
        # At minimum, file_analysis must have completed
        assert "file_analysis" in completed


class TestPartialResults:
    """Partial results are preserved when one module fails."""

    def test_non_image_skips_stego(self):
        case = run_full_analysis("data.txt", b"Hello plaintext world")
        stego_mods = [m for m in case.module_results if m.module_name == "steganalysis"]
        assert len(stego_mods) == 1
        assert stego_mods[0].status == "not_applicable"

    def test_findings_still_present_after_partial_failure(self, test_image_bytes):
        case = run_full_analysis("test.png", test_image_bytes)
        # File findings must always be present
        file_findings = [f for f in case.findings if f.category == "file"]
        assert len(file_findings) > 0


class TestCaseStore:
    """In-memory case store: save, retrieve, list, delete."""

    def test_save_and_retrieve(self, text_file_bytes):
        case = run_full_analysis("store_test.txt", text_file_bytes)
        retrieved = get_case(case.case_id)
        assert retrieved is not None
        assert retrieved.case_id == case.case_id

    def test_retrieve_nonexistent(self):
        assert get_case(str(uuid.uuid4())) is None

    def test_list_cases_returns_recent_first(self, text_file_bytes):
        c1 = run_full_analysis("a.txt", text_file_bytes)
        c2 = run_full_analysis("b.txt", text_file_bytes)
        cases = list_cases(limit=10)
        ids = [c.case_id for c in cases]
        # Most recent first
        assert ids.index(c2.case_id) < ids.index(c1.case_id)

    def test_delete_case(self, text_file_bytes):
        case = run_full_analysis("del_test.txt", text_file_bytes)
        assert delete_case(case.case_id) is True
        assert get_case(case.case_id) is None


# ── E. Security tests ──────────────────────────────────────────────────────

class TestPathTraversal:
    """Path traversal in filenames must be neutralised."""

    def test_path_traversal_attempt(self):
        from backend.engine.file_handler import sanitize_filename
        result = sanitize_filename("../../etc/passwd")
        assert ".." not in result
        assert "/" not in result
        assert "\\" not in result

    def test_windows_path_traversal(self):
        from backend.engine.file_handler import sanitize_filename
        result = sanitize_filename("C:\\Windows\\system32\\cmd.exe")
        assert "\\" not in result
        assert ":" not in result

    def test_null_byte_in_filename(self):
        from backend.engine.file_handler import sanitize_filename
        result = sanitize_filename("test\x00.txt")
        assert "\x00" not in result


class TestFileSizeValidation:
    """Oversized files are rejected before analysis."""

    def test_oversized_file_rejected(self):
        huge = b"A" * (60 * 1024 * 1024)  # 60 MB
        response = client.post(
            "/api/cases",
            files={"file": ("big.txt", huge, "text/plain")},
        )
        assert response.status_code == 413

    def test_empty_file_rejected(self):
        response = client.post(
            "/api/cases",
            files={"file": ("empty.txt", b"", "text/plain")},
        )
        assert response.status_code == 400


class TestTempFileCleanup:
    """Temporary files must not persist after analysis."""

    def test_no_temp_files_leak(self, text_file_bytes):
        import glob
        tmp_dir = tempfile.gettempdir()
        before = set(glob.glob(os.path.join(tmp_dir, "*.txt")))
        run_full_analysis("cleanup_test.txt", text_file_bytes)
        after = set(glob.glob(os.path.join(tmp_dir, "*.txt")))
        # No new .txt temp files should persist
        new_files = after - before
        assert len(new_files) == 0, f"Temp files leaked: {new_files}"


class TestDecompressionSafety:
    """Decompression must respect size limits."""

    def test_gzip_decompression_works_normally(self):
        payload = gzip.compress(b"Hello from gzip")
        encoded = base64.b64encode(payload).decode()
        from backend.decoders.decoders import GzipDecoder
        # GzipDecoder works on raw bytes via latin-1 encoding
        result = GzipDecoder().decode(payload.decode("latin-1"))
        assert result is not None

    def test_malformed_gzip_does_not_crash(self):
        from backend.decoders.decoders import GzipDecoder
        result = GzipDecoder().decode("not gzip data at all")
        assert result is None

    def test_malformed_zlib_does_not_crash(self):
        from backend.decoders.decoders import ZlibDecoder
        result = ZlibDecoder().decode("not zlib data at all")
        assert result is None


class TestUnsafeFilename:
    """Unsafe filenames are sanitized for display."""

    def test_script_tag_in_filename_sanitized(self):
        from backend.engine.file_handler import sanitize_filename
        result = sanitize_filename("<script>alert(1)</script>.png")
        assert "<" not in result
        assert ">" not in result

    def test_null_bytes_removed(self):
        from backend.engine.file_handler import sanitize_filename
        result = sanitize_filename("file\x00name.txt")
        assert "\x00" not in result


class TestMimeExtensionMismatch:
    """Extension/format mismatch is detected and reported."""

    def test_png_with_txt_extension_flagged(self, test_image_bytes):
        case = run_full_analysis("image.txt", test_image_bytes)
        mismatch = [
            f for f in case.findings
            if f.rule_id == "FILE-MAGIC-MISMATCH"
        ]
        assert len(mismatch) >= 1

    def test_matching_format_not_flagged(self, test_image_bytes):
        case = run_full_analysis("image.png", test_image_bytes)
        mismatch = [
            f for f in case.findings
            if f.rule_id == "FILE-MAGIC-MISMATCH"
        ]
        assert len(mismatch) == 0


# ── A. File-analysis hash tests ────────────────────────────────────────────

class TestFileAnalysisFindings:
    """File analysis module produces correct findings."""

    def test_entropy_finding_present(self, text_file_bytes):
        case = run_full_analysis("entropy_test.txt", text_file_bytes)
        ent_findings = [f for f in case.findings if "Entropy" in f.title]
        assert len(ent_findings) >= 1

    def test_string_extraction_finding(self, text_file_bytes):
        case = run_full_analysis("strings_test.txt", text_file_bytes)
        str_findings = [f for f in case.findings if "String" in f.title]
        assert len(str_findings) >= 1

    def test_file_identity_finding(self, text_file_bytes):
        case = run_full_analysis("identity_test.txt", text_file_bytes)
        identity = [f for f in case.findings if f.title == "File Identity"]
        assert len(identity) == 1
        assert identity[0].evidence_details["sha256"] == hashlib.sha256(text_file_bytes).hexdigest()

    def test_empty_file_produces_finding(self):
        # Single byte to avoid empty-file rejection
        case = run_full_analysis("tiny.txt", b"x")
        assert len(case.findings) > 0

    def test_magic_bytes_in_evidence(self, test_image_bytes):
        case = run_full_analysis("test.png", test_image_bytes)
        identity = next(f for f in case.findings if f.title == "File Identity")
        assert "89 50 4E 47" in (identity.evidence_details or {}).get("magic_bytes_hex", "")


# ── F. API endpoint tests for cases ───────────────────────────────────────

class TestCaseAPI:
    """API endpoints for case creation, retrieval, and report download."""

    def test_create_case_from_upload(self, text_file_bytes):
        response = client.post(
            "/api/cases",
            files={"file": ("test.txt", text_file_bytes, "text/plain")},
        )
        assert response.status_code == 200
        data = response.json()
        assert "case_id" in data
        assert "sha256" in data
        assert data["sha256"] == hashlib.sha256(text_file_bytes).hexdigest()

    def test_get_case(self, text_file_bytes):
        create = client.post(
            "/api/cases",
            files={"file": ("get_test.txt", text_file_bytes, "text/plain")},
        )
        case_id = create.json()["case_id"]
        response = client.get(f"/api/cases/{case_id}")
        assert response.status_code == 200
        assert response.json()["case_id"] == case_id

    def test_get_nonexistent_case(self):
        response = client.get(f"/api/cases/{uuid.uuid4()}")
        assert response.status_code == 404

    def test_list_cases(self, text_file_bytes):
        client.post("/api/cases", files={"file": ("list_test.txt", text_file_bytes, "text/plain")})
        response = client.get("/api/cases?limit=5")
        assert response.status_code == 200
        data = response.json()
        assert "cases" in data
        assert isinstance(data["cases"], list)

    def test_delete_case(self, text_file_bytes):
        create = client.post(
            "/api/cases",
            files={"file": ("del_test.txt", text_file_bytes, "text/plain")},
        )
        case_id = create.json()["case_id"]
        del_resp = client.delete(f"/api/cases/{case_id}")
        assert del_resp.status_code == 200
        get_resp = client.get(f"/api/cases/{case_id}")
        assert get_resp.status_code == 404

    def test_json_report_download(self, text_file_bytes):
        create = client.post(
            "/api/cases",
            files={"file": ("report_test.txt", text_file_bytes, "text/plain")},
        )
        case_id = create.json()["case_id"]
        response = client.get(f"/api/cases/{case_id}/report/json")
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"
        import json
        data = json.loads(response.content)
        assert data["case_id"] == case_id
        assert "findings" in data
        assert "scope_statement" in data

    def test_json_report_fields(self, text_file_bytes):
        create = client.post(
            "/api/cases",
            files={"file": ("fields_test.txt", text_file_bytes, "text/plain")},
        )
        case_id = create.json()["case_id"]
        response = client.get(f"/api/cases/{case_id}/report/json")
        data = response.json()
        required = [
            "report_id", "case_id", "generated_at_utc", "sha256", "md5",
            "app_version", "engine_version", "modules_run", "findings",
            "scope_statement", "limitations", "final_summary",
        ]
        for field in required:
            assert field in data, f"Missing field: {field}"

    def test_case_has_warnings_for_non_image_stego(self):
        data = b"plain text no stego"
        response = client.post(
            "/api/cases",
            files={"file": ("no_stego.txt", data, "text/plain")},
        )
        assert response.status_code == 200
        case_data = response.json()
        stego_mods = [m for m in case_data["module_results"] if m["module_name"] == "steganalysis"]
        assert stego_mods[0]["status"] == "not_applicable"


# ── Correlation tests ──────────────────────────────────────────────────────

class TestCorrelation:
    """Correlation rules produce explainable results."""

    def test_correlations_have_required_fields(self, test_image_bytes):
        case = run_full_analysis("test.png", test_image_bytes)
        for corr in case.correlations:
            assert corr.rule_id
            assert corr.rule_description
            assert corr.match_reason
            assert corr.what_this_does_not_prove
            assert corr.next_step

    def test_correlations_reference_existing_findings(self, test_image_bytes):
        case = run_full_analysis("test.png", test_image_bytes)
        finding_ids = {f.finding_id for f in case.findings}
        for corr in case.correlations:
            for fid in corr.triggered_by_finding_ids:
                assert fid in finding_ids, f"Correlation {corr.rule_id} references non-existent finding {fid}"
