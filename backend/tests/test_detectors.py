"""
Unit tests for encoding detectors.

Tests detection accuracy and confidence scoring for all supported encodings.
"""
import pytest
from backend.detectors.detector import (
    detect_base64, detect_hex, detect_binary,
    detect_rot13, detect_morse, detect_url_encoding,
    detect_html_entity, detect_unicode_escape,
    detect_uuencoding, detect_zlib, detect_gzip,
    detect_md5, detect_sha1, detect_sha224, detect_sha256,
    detect_sha384, detect_sha512,
    detect_all, DETECTORS
)


class TestBase64Detection:
    """Test Base64 detection accuracy."""
    
    def test_detect_valid_base64(self):
        # "Hello World" in Base64
        confidence = detect_base64("SGVsbG8gV29ybGQ=")
        assert confidence > 0.75
    
    def test_detect_base64_no_padding(self):
        confidence = detect_base64("SGVsbG8gV29ybGQ")
        assert confidence > 0.2  # Lower but still detected
    
    def test_reject_non_base64(self):
        confidence = detect_base64("This is not Base64!!!")
        assert confidence == 0.0
    
    def test_reject_wrong_length(self):
        confidence = detect_base64("ABC")  # Wrong length
        assert confidence < 0.5


class TestHexDetection:
    """Test hexadecimal detection accuracy."""
    
    def test_detect_valid_hex(self):
        confidence = detect_hex("48656c6c6f")
        assert confidence > 0.8
    
    def test_detect_hex_with_prefix(self):
        confidence = detect_hex("0x48656c6c6f")
        assert confidence > 0.8
    
    def test_reject_non_hex(self):
        confidence = detect_hex("Not hex at all")
        assert confidence == 0.0
    
    def test_reject_odd_length(self):
        confidence = detect_hex("48656c6c6")
        assert confidence < 0.5


class TestBinaryDetection:
    """Test binary detection accuracy."""
    
    def test_detect_space_separated(self):
        confidence = detect_binary("01001000 01101001")
        assert confidence > 0.9
    
    def test_detect_continuous(self):
        confidence = detect_binary("0100100001101001")
        assert confidence > 0.8
    
    def test_reject_non_binary(self):
        confidence = detect_binary("012345")
        assert confidence == 0.0


class TestMorseDetection:
    """Test Morse code detection accuracy."""
    
    def test_detect_morse(self):
        confidence = detect_morse("... --- ...")
        assert confidence > 0.9
    
    def test_reject_non_morse(self):
        confidence = detect_morse("Hello World")
        assert confidence == 0.0


class TestURLDetection:
    """Test URL encoding detection accuracy."""
    
    def test_detect_url_encoding(self):
        confidence = detect_url_encoding("Hello%20World%21")
        assert confidence > 0.6
    
    def test_reject_no_encoding(self):
        confidence = detect_url_encoding("Hello World")
        assert confidence == 0.0


class TestHTMLEntityDetection:
    """Test HTML entity detection accuracy."""
    
    def test_detect_named_entities(self):
        confidence = detect_html_entity("&lt;Hello&gt; &amp; World")
        assert confidence > 0.6
    
    def test_detect_numeric_entities(self):
        confidence = detect_html_entity("&#72;&#101;&#108;&#108;&#111;")
        assert confidence > 0.6
    
    def test_reject_no_entities(self):
        confidence = detect_html_entity("No entities here")
        assert confidence == 0.0


class TestUnicodeEscapeDetection:
    """Test Unicode escape detection accuracy."""
    
    def test_detect_unicode_escapes(self):
        confidence = detect_unicode_escape("\\u0048\\u0065\\u006c\\u006c\\u006f")
        assert confidence > 0.6
    
    def test_reject_no_escapes(self):
        confidence = detect_unicode_escape("No escapes here")
        assert confidence == 0.0


class TestDetectAll:
    """Test the detect_all aggregator function."""
    
    def test_detect_all_base64(self):
        detections = detect_all("SGVsbG8gV29ybGQ=")
        # Should detect Base64 with high confidence
        assert len(detections) > 0
        assert detections[0]['type'] == 'base64'
        assert detections[0]['confidence'] > 0.75
    
    def test_detect_all_hex(self):
        detections = detect_all("48656c6c6f")
        # Should detect hex
        assert any(d['type'] == 'hex' for d in detections)
    
    def test_detect_all_returns_sorted(self):
        detections = detect_all("SGVsbG8gV29ybGQ=")
        # Should return sorted by confidence (descending)
        if len(detections) > 1:
            for i in range(len(detections) - 1):
                assert detections[i]['confidence'] >= detections[i+1]['confidence']
    
    def test_detect_all_filters_zero(self):
        detections = detect_all("Plain text with no encoding")
        # Should only return non-zero confidences
        for detection in detections:
            assert detection['confidence'] > 0.0


class TestDetectorRegistry:
    """Test the detector registry."""
    
    def test_all_detectors_registered(self):
        expected_detectors = [
            'base64', 'base32', 'base85', 'hex', 'binary',
            'decimal_ascii', 'rot13', 'caesar', 'morse',
            'url', 'html_entity', 'unicode_escape', 'uuencoding',
            'zlib', 'gzip', 'md5', 'sha1', 'sha224', 'sha256', 'sha384', 'sha512'
        ]
        for detector in expected_detectors:
            assert detector in DETECTORS
    
    def test_all_detectors_callable(self):
        for name, detector_fn in DETECTORS.items():
            assert callable(detector_fn)
            # Test with sample input
            result = detector_fn("test input")
            assert isinstance(result, float)
            assert 0.0 <= result <= 1.0


class TestNewDetectors:
    """Test cases for the newly implemented detectors."""

    def test_detect_uuencoding(self):
        assert detect_uuencoding("begin 666 dummy.txt\n&2&5L;&\\`\nend") > 0.8
        assert detect_uuencoding("Not UUEncoded text") == 0.0

    def test_detect_zlib(self):
        import zlib
        compressed = zlib.compress(b"Hello World")
        assert detect_zlib(compressed.decode('latin-1')) > 0.8

    def test_detect_gzip(self):
        import gzip
        compressed = gzip.compress(b"Hello World")
        assert detect_gzip(compressed.decode('latin-1')) > 0.8

    def test_detect_hashes(self):
        # MD5 (32 chars)
        assert detect_md5("5d41402abc4b2a76b9719d911017c592") > 0.8
        # SHA-256 (64 chars)
        assert detect_sha256("2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824") > 0.8
        # SHA-1 (40 chars)
        assert detect_sha1("aaf4c61ddcc5e8a2dabede0f3b482cd9aea9434d") > 0.8



class TestDetectorEdgeCases:
    """Test edge cases for detectors."""
    
    @pytest.mark.parametrize("detector_fn", DETECTORS.values())
    def test_empty_input(self, detector_fn):
        result = detector_fn("")
        assert result == 0.0
    
    @pytest.mark.parametrize("detector_fn", DETECTORS.values())
    def test_very_long_input(self, detector_fn):
        long_input = "A" * 10000
        result = detector_fn(long_input)
        # Should not crash
        assert isinstance(result, float)
        assert 0.0 <= result <= 1.0
    
    @pytest.mark.parametrize("detector_fn", DETECTORS.values())
    def test_unicode_input(self, detector_fn):
        unicode_input = "你好世界"
        result = detector_fn(unicode_input)
        # Should not crash
        assert isinstance(result, float)
        assert 0.0 <= result <= 1.0
