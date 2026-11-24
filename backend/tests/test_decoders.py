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
    HexDecoder, BinaryDecoder, DecimalAsciiDecoder, OctalDecoder,
    ROT13Decoder, CaesarDecoder, AtbashDecoder, BaconianDecoder, A1Z26Decoder, BrailleDecoder, ReverseDecoder, NATOPhoneticDecoder, VigenereDecoder, AffineDecoder, MorseDecoder,
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


class TestAtbashDecoder:
    """Test Atbash cipher decoder."""

    def test_atbash_basic(self):
        decoder = AtbashDecoder()
        assert decoder.decode("Svool Dliow") == "Hello World"

    def test_atbash_case_and_symbols(self):
        decoder = AtbashDecoder()
        assert decoder.decode("Svool, Dliow! 123") == "Hello, World! 123"

    def test_atbash_no_alpha_returns_none(self):
        decoder = AtbashDecoder()
        assert decoder.decode("12345!@#") is None

    def test_atbash_empty_returns_none(self):
        decoder = AtbashDecoder()
        assert decoder.decode("") is None


class TestBaconianDecoder:
    """Test Bacon's cipher decoder."""

    def test_baconian_space_separated(self):
        decoder = BaconianDecoder()
        # "AABAA" -> E, "ABBAB" -> N, "AAABB" -> D
        assert decoder.decode("AABAA ABBAB AAABB") == "END"

    def test_baconian_continuous(self):
        decoder = BaconianDecoder()
        assert decoder.decode("AABAAABBABAAABB") == "END"

    def test_baconian_lowercase(self):
        decoder = BaconianDecoder()
        assert decoder.decode("aabaa abbab aaabb") == "END"

    def test_baconian_invalid_length(self):
        decoder = BaconianDecoder()
        assert decoder.decode("AABA") is None

    def test_baconian_invalid_chars(self):
        decoder = BaconianDecoder()
        assert decoder.decode("AACAA") is None


class TestA1Z26Decoder:
    """Test A1Z26 numerical alphabet position substitution decoder."""

    def test_a1z26_hyphen_separated(self):
        decoder = A1Z26Decoder()
        assert decoder.decode("8-5-12-12-15") == "HELLO"

    def test_a1z26_space_separated(self):
        decoder = A1Z26Decoder()
        assert decoder.decode("8 5 12 12 15") == "HELLO"

    def test_a1z26_comma_separated(self):
        decoder = A1Z26Decoder()
        assert decoder.decode("8, 5, 12, 12, 15") == "HELLO"

    def test_a1z26_invalid_number_out_of_range(self):
        decoder = A1Z26Decoder()
        assert decoder.decode("8-5-27") is None

    def test_a1z26_non_digits(self):
        decoder = A1Z26Decoder()
        assert decoder.decode("8-five-12") is None

    def test_a1z26_empty(self):
        decoder = A1Z26Decoder()
        assert decoder.decode("") is None


class TestOctalDecoder:
    """Test Octal representation decoder."""

    def test_octal_space_separated(self):
        decoder = OctalDecoder()
        assert decoder.decode("110 145 154 154 157") == "Hello"

    def test_octal_backslash_prefixed(self):
        decoder = OctalDecoder()
        assert decoder.decode(r"\110\145\154\154\157") == "Hello"

    def test_octal_0o_prefixed(self):
        decoder = OctalDecoder()
        assert decoder.decode("0o110 0o145 0o154 0o154 0o157") == "Hello"

    def test_octal_invalid_digits(self):
        decoder = OctalDecoder()
        assert decoder.decode("118 145") is None

    def test_octal_out_of_range(self):
        decoder = OctalDecoder()
        assert decoder.decode("400 145") is None

    def test_octal_empty(self):
        decoder = OctalDecoder()
        assert decoder.decode("") is None


class TestBrailleDecoder:
    """Test Braille Unicode transcript decoder."""

    def test_braille_basic(self):
        decoder = BrailleDecoder()
        assert decoder.decode("⠓⠑⠇⠇⠕") == "hello"

    def test_braille_with_space(self):
        decoder = BrailleDecoder()
        assert decoder.decode("⠓⠑⠇⠇⠕⠀⠺⠕⠗⠇⠙") == "hello world"

    def test_braille_with_punctuation(self):
        decoder = BrailleDecoder()
        assert decoder.decode("⠓⠑⠇⠇⠕⠂⠀⠺⠕⠗⠇⠙⠖") == "hello, world!"

    def test_braille_non_braille_returns_none(self):
        decoder = BrailleDecoder()
        assert decoder.decode("plain text") is None

    def test_braille_empty_returns_none(self):
        decoder = BrailleDecoder()
        assert decoder.decode("") is None


class TestReverseDecoder:
    """Test Reverse / mirror text decoder."""

    def test_reverse_basic(self):
        decoder = ReverseDecoder()
        assert decoder.decode("dlroW olleH") == "Hello World"

    def test_reverse_flag(self):
        decoder = ReverseDecoder()
        assert decoder.decode("}galf_tset{galf") == "flag{test_flag}"

    def test_reverse_palindrome_returns_none(self):
        decoder = ReverseDecoder()
        assert decoder.decode("racecar") is None

    def test_reverse_single_char_returns_none(self):
        decoder = ReverseDecoder()
        assert decoder.decode("A") is None

    def test_reverse_empty(self):
        decoder = ReverseDecoder()
        assert decoder.decode("") is None


class TestNATOPhoneticDecoder:
    """Test NATO phonetic spelling alphabet decoder."""

    def test_nato_basic(self):
        decoder = NATOPhoneticDecoder()
        assert decoder.decode("Hotel Echo Lima Lima Oscar") == "HELLO"

    def test_nato_mixed_with_digits(self):
        decoder = NATOPhoneticDecoder()
        assert decoder.decode("Foxtrot Lima Alfa Golf Seven") == "FLAG7"

    def test_nato_with_punctuation(self):
        decoder = NATOPhoneticDecoder()
        assert decoder.decode("Delta, Echo, Charlie, Oscar, Delta, Echo") == "DECODE"

    def test_nato_unmatched_tokens_returns_none(self):
        decoder = NATOPhoneticDecoder()
        assert decoder.decode("random non phonetic text words") is None

    def test_nato_empty_returns_none(self):
        decoder = NATOPhoneticDecoder()
        assert decoder.decode("") is None


class TestVigenereDecoder:
    """Test Vigenere cipher decoding with explicit keys and candidate keys."""

    def test_vigenere_decrypt_with_key_basic(self):
        # Ciphertext "LXFOPVEFRNHR" encrypted from "ATTACKATDAWN" with key "LEMON"
        result = VigenereDecoder.decrypt_with_key("LXFOPVEFRNHR", "LEMON")
        assert result == "ATTACKATDAWN"

    def test_vigenere_case_and_punctuation(self):
        result = VigenereDecoder.decrypt_with_key("Lxfopv, Efrnhr!", "lemon")
        assert result == "Attack, Atdawn!"

    def test_vigenere_decode_with_explicit_key(self):
        decoder = VigenereDecoder()
        result = decoder.decode("LXFOPVEFRNHR", key="LEMON")
        assert result == "ATTACKATDAWN"

    def test_vigenere_decode_with_default_key(self):
        decoder = VigenereDecoder()
        # Plaintext "the secret key is hidden here" with key "KEY"
        ciphertext = "dlc ciabir uiw sw fshbor fovc"
        result = decoder.decode(ciphertext)
        assert result is not None
        assert "secret" in result.lower()

    def test_vigenere_invalid_inputs(self):
        decoder = VigenereDecoder()
        assert decoder.decode("") is None
        assert decoder.decode("12345!@#$") is None


class TestAffineDecoder:
    """Test Affine cipher decoder with explicit parameters and brute force search."""

    def test_affine_decrypt_explicit(self):
        # E(x) = (5*x + 8) mod 26
        ciphertext = "rclla oaplx zrwu wu i ucspcz hlim"
        result = AffineDecoder.decrypt(ciphertext, 5, 8)
        assert result == "hello world this is a secret flag"

    def test_affine_case_and_punctuation(self):
        result = AffineDecoder.decrypt("Rclla, Oaplx!", 5, 8)
        assert result == "Hello, World!"

    def test_affine_decode_explicit_params(self):
        decoder = AffineDecoder()
        result = decoder.decode("rclla oaplx", a=5, b=8)
        assert result == "hello world"

    def test_affine_decode_brute_force(self):
        decoder = AffineDecoder()
        ciphertext = "rclla oaplx zrwu wu i ucspcz hlim"
        result = decoder.decode(ciphertext)
        assert result is not None
        assert result == "hello world this is a secret flag"

    def test_affine_invalid_inputs(self):
        decoder = AffineDecoder()
        assert decoder.decode("") is None
        assert decoder.decode("12345!@#$") is None










