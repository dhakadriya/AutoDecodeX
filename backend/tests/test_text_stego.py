"""
Unit tests for text steganography detection, extraction, and encoding.
"""
import pytest
from backend.stego.text_stego import (
    extract_text_stego,
    detect_zero_width_stego,
    encode_zero_width,
    extract_zero_width_payload,
)


class TestZeroWidthSteganography:
    """Test Zero-Width Character (ZWC) steganography routines."""

    def test_encode_and_decode_roundtrip(self):
        cover = "Official announcement regarding forensic analysis protocols."
        secret = "flag{hidden_zwc_payload}"
        stego_text = encode_zero_width(cover, secret)

        assert len(stego_text) > len(cover)
        # Verify the visible text is preserved
        assert cover[:len(cover)//2] in stego_text
        assert cover[len(cover)//2:] in stego_text

        extracted = extract_zero_width_payload(stego_text)
        assert extracted["found"] is True
        assert extracted["decoded"] == secret
        assert extracted["bit_count"] == len(secret) * 8

    def test_detect_zero_width_stego_positive(self):
        cover = "Important briefing document."
        stego_text = encode_zero_width(cover, "secret")
        confidence = detect_zero_width_stego(stego_text)
        assert confidence >= 0.90

    def test_detect_zero_width_stego_negative(self):
        clean_text = "This is a clean text with standard ASCII and no hidden characters."
        assert detect_zero_width_stego(clean_text) == 0.0

    def test_detect_zero_width_empty(self):
        assert detect_zero_width_stego("") == 0.0

    def test_extract_from_clean_text_returns_not_found(self):
        result = extract_zero_width_payload("Just normal text here.")
        assert result["found"] is False
        assert result["decoded"] == ""


class TestTextStegoPipeline:
    """Test full text steganography pipeline."""

    def test_pipeline_on_embedded_text(self):
        cover = "Alpha line\nBravo line\nCharlie line"
        stego_text = encode_zero_width(cover, "flag{test}")
        results = extract_text_stego(stego_text)

        assert "zero_width" in results
        assert results["zero_width"]["found"] is True
        assert results["zero_width"]["decoded"] == "flag{test}"
        assert results["invisible_chars_found"] > 0

    def test_pipeline_acrostic_extraction(self):
        poem = "First line here\nLine two follows\nAll lines align\nGreat work done"
        results = extract_text_stego(poem)
        assert results["first_letters"]["first_letter_each_line"] == "FLAG"

    def test_pipeline_empty_string(self):
        results = extract_text_stego("")
        assert results["zero_width"]["found"] is False
        assert results["invisible_chars_found"] == 0
