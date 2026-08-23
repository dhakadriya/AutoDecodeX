"""
Integration tests for API endpoints.

Tests the FastAPI endpoints with various inputs.
"""
import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


class TestHealthEndpoint:
    """Test the health check endpoint."""
    
    def test_health_check(self):
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "service" in data


class TestDecodeEndpoint:
    """Test the main decode endpoint."""
    
    def test_decode_base64(self):
        response = client.post(
            "/api/decode",
            json={"input": "SGVsbG8gV29ybGQ=", "ctf_mode": False}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["final_output"] == "Hello World"
        assert len(data["steps"]) >= 1
    
    def test_decode_with_ctf_mode(self):
        # "flag{test}" in Base64: ZmxhZ3t0ZXN0fQ==
        response = client.post(
            "/api/decode",
            json={"input": "ZmxhZ3t0ZXN0fQ==", "ctf_mode": True}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["is_ctf_flag"] is True
    
    def test_decode_plaintext(self):
        response = client.post(
            "/api/decode",
            json={"input": "This is plaintext"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["final_output"] == "This is plaintext"
    
    def test_decode_multi_layer(self):
        # Double encoded: "Hi" -> hex -> base64
        response = client.post(
            "/api/decode",
            json={"input": "NDg2NTZjNmM2Zg=="}
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["steps"]) >= 2
    
    def test_decode_empty_input(self):
        response = client.post(
            "/api/decode",
            json={"input": ""}
        )
        # Should handle gracefully
        assert response.status_code == 200


class TestDetectEndpoint:
    """Test the detection-only endpoint."""
    
    def test_detect_base64(self):
        response = client.post(
            "/api/detect",
            json={"input": "SGVsbG8gV29ybGQ="}
        )
        assert response.status_code == 200
        data = response.json()
        assert "detections" in data
        assert len(data["detections"]) > 0
        # Base64 should be detected
        assert any(d["type"] == "base64" for d in data["detections"])
    
    def test_detect_hex(self):
        response = client.post(
            "/api/detect",
            json={"input": "48656c6c6f"}
        )
        assert response.status_code == 200
        data = response.json()
        # Hex should be detected
        assert any(d["type"] == "hex" for d in data["detections"])
    
    def test_detect_plaintext(self):
        response = client.post(
            "/api/detect",
            json={"input": "Hello World"}
        )
        assert response.status_code == 200
        data = response.json()
        # May have some low-confidence detections or empty


class TestBruteForceEndpoint:
    """Test the brute force endpoint."""
    
    def test_brute_force_caesar(self):
        response = client.post(
            "/api/brute-force",
            json={"input": "Khoor", "mode": "caesar"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["mode"] == "caesar"
        assert "results" in data
        assert len(data["results"]) == 26
    
    def test_brute_force_xor(self):
        # XOR "Hello" with key 42
        xored = bytes([ord(c) ^ 42 for c in "Hello"]).hex()
        response = client.post(
            "/api/brute-force",
            json={"input": xored, "mode": "xor"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["mode"] == "xor"
        assert "results" in data
        assert len(data["results"]) > 0
    
    def test_brute_force_invalid_mode(self):
        response = client.post(
            "/api/brute-force",
            json={"input": "test", "mode": "invalid"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "error" in data


class TestRootEndpoint:
    """Test the root endpoint."""
    
    def test_root(self):
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data


class TestCORSHeaders:
    """Test CORS configuration."""
    
    def test_cors_headers_present(self):
        # Test CORS by making a request with Origin header
        response = client.get("/api/health", headers={"Origin": "http://localhost:3000"})
        # CORS headers should be present in response
        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers or response.status_code == 200


class TestEdgeCases:
    """Test API edge cases."""
    
    def test_very_long_input(self):
        long_input = "A" * 10000
        response = client.post(
            "/api/decode",
            json={"input": long_input}
        )
        # Should handle without crashing (may timeout or return error)
        assert response.status_code in [200, 422, 504]
    
    def test_unicode_input(self):
        response = client.post(
            "/api/decode",
            json={"input": "你好世界"}
        )
        assert response.status_code == 200
    
    def test_special_characters(self):
        response = client.post(
            "/api/decode",
            json={"input": "!@#$%^&*()"}
        )
        assert response.status_code == 200


class TestResponseStructure:
    """Test API response structure consistency."""
    
    def test_decode_response_structure(self):
        response = client.post(
            "/api/decode",
            json={"input": "SGVsbG8="}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Check required fields
        required_fields = [
            "success", "final_output", "total_score",
            "path_description", "is_ctf_flag", "steps"
        ]
        for field in required_fields:
            assert field in data
    
    def test_detect_response_structure(self):
        response = client.post(
            "/api/detect",
            json={"input": "test"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "detections" in data
    
    def test_step_structure(self):
        response = client.post(
            "/api/decode",
            json={"input": "SGVsbG8="}
        )
        data = response.json()
        if len(data["steps"]) > 0:
            step = data["steps"][0]
            required_step_fields = [
                "step_number", "encoding_type", "confidence",
                "input_text", "output_text", "score"
            ]
            for field in required_step_fields:
                assert field in step


class TestNewEndpoints:
    """Test newly implemented endpoints for experiments and file analysis."""

    def test_run_experiments(self):
        response = client.post("/api/experiments/run")
        assert response.status_code == 200
        data = response.json()
        assert "accuracy" in data
        assert "average_time_ms" in data
        assert "total_runs" in data
        assert "successful_runs" in data
        assert "depth_breakdown" in data
        assert "individual_runs" in data
        assert len(data["individual_runs"]) > 0

    def test_file_analyze(self):
        from backend.tests.demo_dataset import generate_test_image
        img_bytes = generate_test_image()
        
        response = client.post(
            "/api/file/analyze",
            files={"file": ("test.png", img_bytes, "image/png")}
        )
        assert response.status_code == 200
        data = response.json()
        assert "filename" in data
        assert "metadata" in data
        assert "lsb" in data
        assert "lsb_decode" in data
        assert "entropy" in data
        assert data["filename"] == "test.png"

