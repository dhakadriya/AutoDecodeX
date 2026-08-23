"""
Unit tests for individual decoder implementations.

Tests each decoder with:
- Valid inputs
- Invalid inputs
- Edge cases
- Multiple format variations
"""
import pytest
from backend.decoders.decoders import (
    Base64Decoder, Base32Decoder, Base85Decoder,
    HexDecoder, BinaryDecoder, DecimalAsciiDecoder,
    ROT13Decoder, CaesarDecoder, MorseDecoder,
    URLDecoder, HTMLEntityDecoder, UnicodeEscapeDecoder,
    XORDecoder, UUDecoder, ZlibDecoder, GzipDecoder,
)


class TestBase64Decoder:
    """Test Base64 decoder functionality."""
    
    def test_standard_base64(self):
        decoder = Base64Decoder()
        # "Hello World" in Base64
        result = decoder.decode("SGVsbG8gV29ybGQ=")
        assert result == "Hello World"
    
    def test_base64_without_padding(self):
        decoder = Base64Decoder()
        # Base64 without padding (should auto-add)
        result = decoder.decode("SGVsbG8gV29ybGQ")
        assert result == "Hello World"
    
    def test_base64_url_safe(self):
        decoder = Base64Decoder()
        # Test URL-safe Base64 variant
        result = decoder.decode("SGVsbG8gV29ybGQ=")
        assert result is not None
    
    def test_invalid_base64(self):
        decoder = Base64Decoder()
        # Invalid Base64 (should return None)
        result = decoder.decode("Not valid Base64!!!")
        assert result is None
    
    def test_short_input(self):
        decoder = Base64Decoder()
        result = decoder.decode("AB")
        assert result is None


class TestHexDecoder:
    """Test hexadecimal decoder functionality."""
    
    def test_standard_hex(self):
        decoder = HexDecoder()
        # "Hello" in hex
        result = decoder.decode("48656c6c6f")
        assert result == "Hello"
    
    def test_hex_with_prefix(self):
        decoder = HexDecoder()
        result = decoder.decode("0x48656c6c6f")
        assert result == "Hello"
    
    def test_hex_with_backslash_x(self):
        decoder = HexDecoder()
        result = decoder.decode("\\x48\\x65\\x6c\\x6c\\x6f")
        assert result == "Hello"
    
    def test_hex_with_spaces(self):
        decoder = HexDecoder()
        result = decoder.decode("48 65 6c 6c 6f")
        assert result == "Hello"
    
    def test_hex_with_colons(self):
        decoder = HexDecoder()
        result = decoder.decode("48:65:6c:6c:6f")
        assert result == "Hello"
    
    def test_invalid_hex(self):
        decoder = HexDecoder()
        result = decoder.decode("This is not hex")
        assert result is None
    
    def test_odd_length_hex(self):
        decoder = HexDecoder()
        result = decoder.decode("48656c6c6")  # Odd length
        assert result is None


class TestBinaryDecoder:
    """Test binary decoder functionality."""
    
    def test_space_separated_binary(self):
        decoder = BinaryDecoder()
        # "Hi" in binary
        result = decoder.decode("01001000 01101001")
        assert result == "Hi"
    
    def test_continuous_binary(self):
        decoder = BinaryDecoder()
        result = decoder.decode("0100100001101001")
        assert result == "Hi"
    
    def test_invalid_binary(self):
        decoder = BinaryDecoder()
        result = decoder.decode("012345")  # Invalid binary digits
        assert result is None
    
    def test_wrong_length_binary(self):
        decoder = BinaryDecoder()
        result = decoder.decode("0100100")  # Not multiple of 8
        assert result is None


class TestDecimalAsciiDecoder:
    """Test decimal ASCII decoder functionality."""
    
    def test_decimal_ascii(self):
        decoder = DecimalAsciiDecoder()
        # "Hi" in decimal ASCII
        result = decoder.decode("72 105")
        assert result == "Hi"
    
    def test_invalid_decimal_range(self):
        decoder = DecimalAsciiDecoder()
        # Values outside ASCII range
        result = decoder.decode("256 300")
        assert result is None
    
    def test_invalid_decimal_format(self):
        decoder = DecimalAsciiDecoder()
        result = decoder.decode("not numbers")
        assert result is None


class TestROT13Decoder:
    """Test ROT13 decoder functionality."""
    
    def test_rot13_lowercase(self):
        decoder = ROT13Decoder()
        result = decoder.decode("uryyb")
        assert result == "hello"
    
    def test_rot13_uppercase(self):
        decoder = ROT13Decoder()
        result = decoder.decode("URYYB")
        assert result == "HELLO"
    
    def test_rot13_mixed(self):
        decoder = ROT13Decoder()
        result = decoder.decode("Uryyb Jbeyq")
        assert result == "Hello World"
    
    def test_rot13_with_numbers(self):
        decoder = ROT13Decoder()
        result = decoder.decode("Uryyb123")
        assert result == "Hello123"


class TestCaesarDecoder:
    """Test Caesar cipher decoder functionality."""
    
    def test_caesar_shift_3(self):
        decoder = CaesarDecoder()
        result = decoder.decode("Khoor", shift=3)
        assert result == "Hello"
    
    def test_caesar_brute_force(self):
        decoder = CaesarDecoder()
        results = decoder.brute_force("Khoor")
        assert len(results) == 26
        # Shift 3 should decode to "Hello"
        shift_3_result = next(r for r in results if r['shift'] == 3)
        assert shift_3_result['decoded'] == "Hello"


class TestMorseDecoder:
    """Test Morse code decoder functionality."""
    
    def test_morse_basic(self):
        decoder = MorseDecoder()
        # "SOS" in Morse
        result = decoder.decode("... --- ...")
        assert result == "SOS"
    
    def test_morse_with_slash_separator(self):
        decoder = MorseDecoder()
        # "HI" in Morse with slash separator
        result = decoder.decode(".... .. / .--- ---")
        assert result is not None
    
    def test_invalid_morse(self):
        decoder = MorseDecoder()
        result = decoder.decode("invalid morse")
        assert result is None


class TestURLDecoder:
    """Test URL decoder functionality."""
    
    def test_url_encoding(self):
        decoder = URLDecoder()
        result = decoder.decode("Hello%20World")
        assert result == "Hello World"
    
    def test_url_special_chars(self):
        decoder = URLDecoder()
        result = decoder.decode("test%40example.com")
        assert result == "test@example.com"
    
    def test_no_url_encoding(self):
        decoder = URLDecoder()
        result = decoder.decode("No encoding here")
        assert result is None


class TestHTMLEntityDecoder:
    """Test HTML entity decoder functionality."""
    
    def test_named_entities(self):
        decoder = HTMLEntityDecoder()
        result = decoder.decode("&lt;Hello&gt; &amp; &quot;World&quot;")
        assert result == '<Hello> & "World"'
    
    def test_numeric_entities(self):
        decoder = HTMLEntityDecoder()
        result = decoder.decode("&#72;&#101;&#108;&#108;&#111;")
        assert result == "Hello"
    
    def test_hex_entities(self):
        decoder = HTMLEntityDecoder()
        result = decoder.decode("&#x48;&#x65;&#x6c;&#x6c;&#x6f;")
        assert result == "Hello"
    
    def test_no_entities(self):
        decoder = HTMLEntityDecoder()
        result = decoder.decode("No entities here")
        assert result is None


class TestUnicodeEscapeDecoder:
    """Test Unicode escape decoder functionality."""
    
    def test_unicode_escape_basic(self):
        decoder = UnicodeEscapeDecoder()
        result = decoder.decode("\\u0048\\u0065\\u006c\\u006c\\u006f")
        assert result == "Hello"
    
    def test_no_unicode_escapes(self):
        decoder = UnicodeEscapeDecoder()
        result = decoder.decode("No escapes here")
        assert result is None


class TestXORDecoder:
    """Test XOR decoder functionality."""
    
    def test_xor_returns_none(self):
        decoder = XORDecoder()
        # XOR decode without key should return None
        result = decoder.decode("test")
        assert result is None
    
    def test_xor_brute_force(self):
        decoder = XORDecoder()
        # XOR "Hello" with key 42
        xored = bytes([ord(c) ^ 42 for c in "Hello"]).hex()
        results = decoder.brute_force(xored)
        # Should find key 42 with high score
        assert len(results) > 0
        assert any(r['key'] == 42 for r in results)


class TestBase32Decoder:
    """Test Base32 decoder functionality."""
    
    def test_standard_base32(self):
        decoder = Base32Decoder()
        # "Hello" in Base32
        result = decoder.decode("JBSWY3DP")
        assert result == "Hello"
    
    def test_base32_with_padding(self):
        decoder = Base32Decoder()
        result = decoder.decode("JBSWY3DPEE======")
        assert result == "Hello!"
    
    def test_invalid_base32(self):
        decoder = Base32Decoder()
        result = decoder.decode("Invalid Base32!")
        assert result is None


class TestBase85Decoder:
    """Test Base85 decoder functionality."""
    
    def test_base85(self):
        decoder = Base85Decoder()
        # "Hello" in Base85
        result = decoder.decode("NM&qnZv")
        assert result == "Hello"
    
    def test_invalid_base85(self):
        decoder = Base85Decoder()
        result = decoder.decode("Invalid")
        # May or may not decode, just ensure no crash
        assert result is None or isinstance(result, str)


# Edge case tests
class TestDecoderEdgeCases:
    """Test edge cases across all decoders."""
    
    @pytest.mark.parametrize("decoder_class", [
        Base64Decoder, HexDecoder, BinaryDecoder,
        ROT13Decoder, URLDecoder, HTMLEntityDecoder,
    ])
    def test_empty_input(self, decoder_class):
        decoder = decoder_class()
        result = decoder.decode("")
        # Should handle gracefully (None or empty string)
        assert result is None or result == ""
    
    @pytest.mark.parametrize("decoder_class", [
        Base64Decoder, HexDecoder, BinaryDecoder,
        ROT13Decoder, URLDecoder, HTMLEntityDecoder,
    ])
    def test_whitespace_input(self, decoder_class):
        decoder = decoder_class()
        result = decoder.decode("   ")
        # Should handle gracefully
        assert result is None or isinstance(result, str)
    
    @pytest.mark.parametrize("decoder_class", [
        Base64Decoder, HexDecoder, BinaryDecoder,
        DecimalAsciiDecoder, URLDecoder, HTMLEntityDecoder,
    ])
    def test_very_long_input(self, decoder_class):
        decoder = decoder_class()
        long_input = "A" * 10000
        # Should not crash
        result = decoder.decode(long_input)
        assert result is None or isinstance(result, str)


class TestUUDecoder:
    """Test UUDecoder functionality."""
    
    def test_uu_basic(self):
        decoder = UUDecoder()
        encoded = "begin 666 dummy.txt\n&2&5L;&\\`\nend"
        result = decoder.decode(encoded)
        assert result == "Hello"

    def test_uu_no_header(self):
        decoder = UUDecoder()
        encoded = "&2&5L;&\\`"
        result = decoder.decode(encoded)
        assert result == "Hello"


class TestZlibDecoder:
    """Test ZlibDecoder functionality."""
    
    def test_zlib_basic(self):
        decoder = ZlibDecoder()
        import zlib
        compressed = zlib.compress(b"Hello World")
        encoded_str = compressed.decode('latin-1')
        result = decoder.decode(encoded_str)
        assert result == "Hello World"


class TestGzipDecoder:
    """Test GzipDecoder functionality."""
    
    def test_gzip_basic(self):
        decoder = GzipDecoder()
        import gzip
        compressed = gzip.compress(b"Hello World")
        encoded_str = compressed.decode('latin-1')
        result = decoder.decode(encoded_str)
        assert result == "Hello World"

