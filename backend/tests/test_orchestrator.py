"""
Unit tests for the decoding orchestrator (core engine).

Tests the main decode() function including:
- Single-layer decoding
- Multi-layer recursive decoding
- Loop detection
- CTF mode
- Edge cases
"""
import pytest
from backend.engine.orchestrator import decode, brute_force_caesar, brute_force_xor


class TestSingleLayerDecoding:
    """Test single-layer (non-recursive) decoding."""
    
    def test_decode_base64(self):
        result = decode("SGVsbG8gV29ybGQ=")
        assert result.success is True
        assert result.final_output == "Hello World"
        assert len(result.steps) == 1
        assert result.steps[0].encoding_type == "base64"
    
    def test_decode_hex(self):
        result = decode("48656c6c6f")
        assert result.success is True
        assert result.final_output == "Hello"
        assert len(result.steps) == 1
        assert result.steps[0].encoding_type == "hex"
    
    def test_decode_rot13(self):
        result = decode("Uryyb Jbeyq")
        assert result.success is True
        assert result.final_output == "Hello World"
        assert any(step.encoding_type == "rot13" for step in result.steps)
    
    def test_decode_url_encoding(self):
        result = decode("Hello%20World")
        assert result.success is True
        assert result.final_output == "Hello World"
        assert any(step.encoding_type == "url" for step in result.steps)


class TestMultiLayerDecoding:
    """Test recursive multi-layer decoding."""
    
    def test_base64_then_hex(self):
        # "Hello" -> hex -> base64
        # "Hello" in hex: 48656c6c6f
        # "48656c6c6f" in base64: NDg2NTZjNmM2Zg==
        result = decode("NDg2NTZjNmM2Zg==")
        assert result.success is True
        assert result.final_output == "Hello"
        assert len(result.steps) >= 2
        # Should decode Base64 first, then hex
        assert result.steps[0].encoding_type == "base64"
        assert result.steps[1].encoding_type == "hex"
    
    def test_triple_layer(self):
        # "Hi" -> binary -> hex -> base64
        # "Hi" in binary: 0100100001101001
        # binary as hex string: 30313030313030303031313031303031
        # hex in base64: MzAzMTMwMzAzMTMwMzAzMDMwMzEzMTMwMzEzMDMwMzE=
        result = decode("MzAzMTMwMzAzMTMwMzAzMDMwMzEzMTMwMzEzMDMwMzE=")
        # Should decode correctly through 3 layers
        assert result.final_output == "Hi"
        assert len(result.steps) == 3
        # Note: "Hi" is too short to score as high-confidence plaintext


class TestLoopDetection:
    """Test infinite loop detection and prevention."""
    
    def test_rot13_double_decode(self):
        # ROT13 applied twice returns original
        # "test" -> ROT13 -> "grfg" -> ROT13 -> "test"
        result = decode("grfg")
        # Should stop after detecting loop
        assert len(result.steps) <= 2
    
    def test_max_depth_reached(self):
        # Create a very long chain and ensure it stops at max depth
        text = "A" * 100
        result = decode(text)
        # Should not exceed MAX_DEPTH
        assert len(result.steps) <= 10  # MAX_DEPTH from orchestrator


class TestCTFMode:
    """Test CTF-optimized mode."""
    
    def test_ctf_mode_flag_detection(self):
        # Base64 encoded flag
        # "flag{test}" in base64: ZmxhZ3t0ZXN0fQ==
        result = decode("ZmxhZ3t0ZXN0fQ==", ctf_mode=True)
        assert result.success is True
        assert result.is_ctf_flag is True
        assert "flag{test}" in result.final_output
    
    def test_ctf_mode_prioritizes_common_encodings(self):
        result = decode("SGVsbG8=", ctf_mode=True)
        # Should still decode properly in CTF mode
        assert result.success is True


class TestPlaintextInput:
    """Test handling of already-decoded plaintext."""
    
    def test_plaintext_no_steps(self):
        result = decode("This is already plaintext")
        assert result.success is True
        assert result.final_output == "This is already plaintext"
        assert len(result.steps) == 0
    
    def test_ctf_flag_no_steps(self):
        result = decode("flag{already_decoded}")
        assert result.success is True
        assert result.is_ctf_flag is True
        assert len(result.steps) == 0


class TestInvalidInput:
    """Test handling of invalid or corrupt input."""
    
    def test_empty_input(self):
        result = decode("")
        # Should handle gracefully
        assert result is not None
        assert isinstance(result.success, bool)
    
    def test_whitespace_only(self):
        result = decode("   ")
        assert result is not None
    
    def test_random_garbage(self):
        result = decode("!@#$%^&*()_+")
        # Should not crash
        assert result is not None
    
    def test_very_long_input(self):
        long_input = "A" * 10000
        result = decode(long_input)
        # Should handle without crashing
        assert result is not None


class TestBruteForceCaesar:
    """Test Caesar cipher brute force."""
    
    def test_brute_force_caesar(self):
        # "Hello" with shift 3 = "Khoor"
        results = brute_force_caesar("Khoor")
        assert len(results) == 26
        # Should include shift 3
        shift_3 = next((r for r in results if r['shift'] == 3), None)
        assert shift_3 is not None
        assert shift_3['decoded'] == "Hello"
    
    def test_brute_force_caesar_ranked(self):
        results = brute_force_caesar("Uryyb")  # "Hello" in ROT13 (shift 13)
        # Results should be sorted by score
        assert 'score' in results[0]
        # Shift 13 should have high score
        shift_13 = next((r for r in results if r['shift'] == 13), None)
        assert shift_13 is not None
        assert shift_13['score'] > 0.5


class TestBruteForceXOR:
    """Test XOR brute force."""
    
    def test_brute_force_xor(self):
        # XOR "Hello" with key 42
        xored = bytes([ord(c) ^ 42 for c in "Hello"]).hex()
        results = brute_force_xor(xored)
        # Should find key 42
        assert len(results) > 0
        key_42 = next((r for r in results if r['key'] == 42), None)
        assert key_42 is not None
        assert "Hello" in key_42['decoded']
    
    def test_brute_force_xor_ranked(self):
        xored = bytes([ord(c) ^ 42 for c in "Hello"]).hex()
        results = brute_force_xor(xored)
        # Results should be sorted by score
        assert 'score' in results[0]


class TestResultStructure:
    """Test the structure of DecodingResult."""
    
    def test_result_has_required_fields(self):
        result = decode("SGVsbG8=")
        assert hasattr(result, 'success')
        assert hasattr(result, 'final_output')
        assert hasattr(result, 'steps')
        assert hasattr(result, 'total_score')
        assert hasattr(result, 'path_description')
        assert hasattr(result, 'is_ctf_flag')
    
    def test_steps_structure(self):
        result = decode("SGVsbG8=")
        if len(result.steps) > 0:
            step = result.steps[0]
            assert hasattr(step, 'step_number')
            assert hasattr(step, 'encoding_type')
            assert hasattr(step, 'confidence')
            assert hasattr(step, 'input_text')
            assert hasattr(step, 'output_text')
            assert hasattr(step, 'score')
    
    def test_path_description(self):
        result = decode("SGVsbG8=")
        assert isinstance(result.path_description, str)
        assert len(result.path_description) > 0


class TestConfidenceScoring:
    """Test confidence score calculations."""
    
    def test_high_confidence_result(self):
        result = decode("SGVsbG8gV29ybGQ=")  # Clear Base64
        assert result.total_score > 0.6
    
    def test_confidence_per_step(self):
        result = decode("SGVsbG8gV29ybGQ=")
        if len(result.steps) > 0:
            for step in result.steps:
                assert 0.0 <= step.confidence <= 1.0
                assert 0.0 <= step.score <= 1.0


class TestEdgeCases:
    """Test additional edge cases."""
    
    def test_unicode_input(self):
        result = decode("你好世界")
        # Should handle without crashing
        assert result is not None
    
    def test_mixed_encoding_and_plaintext(self):
        result = decode("Hello SGVsbG8=")
        # Should handle gracefully
        assert result is not None
    
    def test_partial_encoding(self):
        # Incomplete Base64
        result = decode("SGVsb")
        assert result is not None
    
    def test_null_bytes(self):
        text = "Hello\x00World"
        result = decode(text)
        # Should not crash
        assert result is not None


class TestMultiLayerCompression:
    """Test multi-layer decoding featuring compression and binary safety."""
    
    def test_base64_zlib(self):
        import zlib
        import base64
        # "Hello World" -> zlib -> base64
        compressed = zlib.compress(b"Hello World")
        b64 = base64.b64encode(compressed).decode()
        result = decode(b64)
        assert result.success is True
        assert result.final_output == "Hello World"
        assert len(result.steps) >= 2
        assert result.steps[0].encoding_type == "base64"
        assert result.steps[1].encoding_type == "zlib"

    def test_base64_gzip(self):
        import gzip
        import base64
        # "Hello World" -> gzip -> base64
        compressed = gzip.compress(b"Hello World")
        b64 = base64.b64encode(compressed).decode()
        result = decode(b64)
        assert result.success is True
        assert result.final_output == "Hello World"
        assert len(result.steps) >= 2
        assert result.steps[0].encoding_type == "base64"
        assert result.steps[1].encoding_type == "gzip"


class TestHashClassification:
    """Test cryptographic hash detection and stop conditions."""

    def test_md5_hash_classification(self):
        # md5 of "hello" is "5d41402abc4b2a76b9719d911017c592"
        result = decode("5d41402abc4b2a76b9719d911017c592")
        assert result.success is True
        assert "[MD5 Hash]" in result.final_output
        assert len(result.steps) == 1
        assert result.steps[0].encoding_type == "md5"

