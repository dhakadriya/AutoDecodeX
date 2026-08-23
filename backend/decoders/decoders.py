"""
All decoder implementations.

This module contains all supported encoding/decoding implementations.
Each decoder must inherit from BaseDecoder and implement the decode() method.

Supported encodings:
- Base64, Base32, Base85
- Hexadecimal (with multiple format support)
- Binary (8-bit groups)
- Decimal ASCII
- ROT13
- Caesar cipher (26 shifts with brute force)
- Morse Code
- URL Encoding
- HTML Entity Encoding
- Unicode Escape Sequences
- Single-byte XOR (brute force)
"""
import base64
import binascii
import urllib.parse
import html
import re
import codecs
import zlib
import gzip
from typing import Optional, List, Dict, Any
from .base_decoder import BaseDecoder


class Base64Decoder(BaseDecoder):
    """
    Base64 decoder with automatic padding correction.
    
    Handles standard Base64, Base64URL, and variants with/without padding.
    """
    name = "base64"

    def decode(self, text: str) -> Optional[str]:
        try:
            text = text.strip()
            
            # Skip if too short
            if len(text) < 4:
                return None
                
            # Add padding if needed
            padding = 4 - len(text) % 4
            if padding != 4:
                text += '=' * padding
                
            # Try standard Base64 first
            try:
                raw_bytes = base64.b64decode(text, validate=True)
            except Exception:
                # Try Base64URL variant
                raw_bytes = base64.urlsafe_b64decode(text)
                
            try:
                decoded = raw_bytes.decode('utf-8')
            except Exception:
                decoded = raw_bytes.decode('latin-1')
                
            # Reject if output is just whitespace
            if not decoded.strip():
                return None
                
            return decoded
        except Exception:
            return None


class Base32Decoder(BaseDecoder):
    name = "base32"

    def decode(self, text: str) -> Optional[str]:
        try:
            text = text.strip().upper()
            padding = 8 - len(text) % 8
            if padding != 8:
                text += '=' * padding
            raw_bytes = base64.b32decode(text)
            try:
                decoded = raw_bytes.decode('utf-8')
            except Exception:
                decoded = raw_bytes.decode('latin-1')
            return decoded
        except Exception:
            return None


class Base85Decoder(BaseDecoder):
    name = "base85"

    def decode(self, text: str) -> Optional[str]:
        try:
            raw_bytes = base64.b85decode(text.strip())
            try:
                decoded = raw_bytes.decode('utf-8')
            except Exception:
                decoded = raw_bytes.decode('latin-1')
            return decoded
        except Exception:
            return None


class HexDecoder(BaseDecoder):
    """
    Hexadecimal decoder with multiple format support.
    
    Supports:
    - Plain hex: 48656c6c6f
    - 0x prefix: 0x48656c6c6f
    - \\x prefix: \\x48\\x65\\x6c\\x6c\\x6f
    - Space/colon/dash separated: 48:65:6c:6c:6f
    """
    name = "hex"

    def decode(self, text: str) -> Optional[str]:
        try:
            text = text.strip().replace(' ', '').replace('0x', '').replace('\\x', '')
            text = text.replace(':', '').replace('-', '').replace(',', '')
            
            # Must be even length
            if not text or len(text) % 2 != 0:
                return None
                
            raw_bytes = bytes.fromhex(text)
            try:
                decoded = raw_bytes.decode('utf-8')
            except Exception:
                decoded = raw_bytes.decode('latin-1')
                
            # Reject if empty
            if not decoded.strip():
                return None
                
            return decoded
        except Exception:
            return None


class BinaryDecoder(BaseDecoder):
    name = "binary"

    def decode(self, text: str) -> Optional[str]:
        try:
            text = text.strip()
            parts = text.split()
            if not parts:
                return None
            # Handle space-separated bytes
            if all(re.fullmatch(r'[01]{8}', p) for p in parts):
                chars = [chr(int(p, 2)) for p in parts]
                return ''.join(chars)
            # Handle continuous binary string
            if re.fullmatch(r'[01]+', text) and len(text) % 8 == 0:
                chars = [chr(int(text[i:i+8], 2)) for i in range(0, len(text), 8)]
                return ''.join(chars)
            return None
        except Exception:
            return None


class DecimalAsciiDecoder(BaseDecoder):
    name = "decimal_ascii"

    def decode(self, text: str) -> Optional[str]:
        try:
            parts = text.strip().split()
            nums = [int(p) for p in parts]
            if not all(0 <= n <= 127 for n in nums):
                return None
            return ''.join(chr(n) for n in nums)
        except Exception:
            return None


class ROT13Decoder(BaseDecoder):
    name = "rot13"

    def decode(self, text: str) -> Optional[str]:
        return text.translate(str.maketrans(
            'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz',
            'NOPQRSTUVWXYZABCDEFGHIJKLMnopqrstuvwxyzabcdefghijklm'
        ))


class CaesarDecoder(BaseDecoder):
    name = "caesar"

    def decode(self, text: str, shift: int = 13) -> Optional[str]:
        result = []
        for c in text:
            if c.isalpha():
                base = ord('A') if c.isupper() else ord('a')
                result.append(chr((ord(c) - base - shift) % 26 + base))
            else:
                result.append(c)
        return ''.join(result)

    def brute_force(self, text: str) -> list[dict]:
        """Return all 26 Caesar shifts with their decoded text."""
        results = []
        for shift in range(26):
            decoded = self.decode(text, shift)
            results.append({'shift': shift, 'decoded': decoded})
        return results


class MorseDecoder(BaseDecoder):
    name = "morse"

    MORSE_TABLE = {
        '.-': 'A', '-...': 'B', '-.-.': 'C', '-..': 'D', '.': 'E',
        '..-.': 'F', '--.': 'G', '....': 'H', '..': 'I', '.---': 'J',
        '-.-': 'K', '.-..': 'L', '--': 'M', '-.': 'N', '---': 'O',
        '.--.': 'P', '--.-': 'Q', '.-.': 'R', '...': 'S', '-': 'T',
        '..-': 'U', '...-': 'V', '.--': 'W', '-..-': 'X', '-.--': 'Y',
        '--..': 'Z', '-----': '0', '.----': '1', '..---': '2',
        '...--': '3', '....-': '4', '.....': '5', '-....': '6',
        '--...': '7', '---..': '8', '----.': '9',
    }

    def decode(self, text: str) -> Optional[str]:
        try:
            text = text.strip()
            # Word separator is '/' or '  ' (double space)
            words = re.split(r'\s*/\s*|\s{2,}', text)
            decoded_words = []
            for word in words:
                chars = word.strip().split()
                decoded_chars = []
                for c in chars:
                    if c in self.MORSE_TABLE:
                        decoded_chars.append(self.MORSE_TABLE[c])
                    else:
                        return None  # Unknown morse symbol
                decoded_words.append(''.join(decoded_chars))
            return ' '.join(decoded_words)
        except Exception:
            return None


class URLDecoder(BaseDecoder):
    name = "url"

    def decode(self, text: str) -> Optional[str]:
        try:
            decoded = urllib.parse.unquote(text.strip())
            if decoded == text:
                return None  # Nothing changed
            return decoded
        except Exception:
            return None


class XORDecoder(BaseDecoder):
    name = "xor"

    def decode(self, text: str) -> None:
        # XOR requires a key — use brute_force() instead
        return None

    def brute_force(self, text: str) -> list[dict]:
        """Single-byte XOR brute force over all 256 keys."""
        results = []
        try:
            raw = bytes.fromhex(text.strip().replace(' ', ''))
        except Exception:
            # Try treating as raw bytes
            raw = text.encode('latin-1')

        from backend.scoring.scorer import score_text
        for key in range(256):
            decoded_bytes = bytes(b ^ key for b in raw)
            try:
                decoded = decoded_bytes.decode('utf-8', errors='replace')
                score = score_text(decoded)
                if score > 0.3:
                    results.append({'key': key, 'key_hex': hex(key), 'decoded': decoded, 'score': score})
            except Exception:
                pass
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:10]


class HTMLEntityDecoder(BaseDecoder):
    """
    HTML entity decoder.
    
    Decodes both named entities (&amp;) and numeric entities (&#65; &#x41;).
    """
    name = "html_entity"

    def decode(self, text: str) -> Optional[str]:
        try:
            # Check if there are any entities at all
            if '&' not in text or ';' not in text:
                return None
                
            decoded = html.unescape(text)
            
            # Only return if something changed
            if decoded == text:
                return None
                
            return decoded
        except Exception:
            return None


class UnicodeEscapeDecoder(BaseDecoder):
    """
    Unicode escape sequence decoder.
    
    Supports:
    - \\uXXXX format: \\u0048\\u0065\\u006c\\u006c\\u006f
    - \\UXXXXXXXX format: \\U00000048
    - Python string format: u'\\u0048\\u0065'
    """
    name = "unicode_escape"

    def decode(self, text: str) -> Optional[str]:
        try:
            # Check if text contains unicode escapes
            if '\\u' not in text and '\\U' not in text:
                return None
                
            # Try decoding as unicode escape
            decoded = text.encode('utf-8').decode('unicode-escape')
            
            # Only return if something changed
            if decoded == text:
                return None
                
            # Reject if too many replacement chars
            if decoded.count('\ufffd') > len(decoded) * 0.1:
                return None
                
            return decoded
        except Exception:
            return None


class UUDecoder(BaseDecoder):
    name = "uuencoding"

    def decode(self, text: str) -> Optional[str]:
        try:
            text = text.strip()
            if not text:
                return None
            
            lines = text.splitlines()
            decoded_bytes = bytearray()
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                if line.startswith("begin ") or line == "end" or line == "`":
                    continue
                
                if len(line) < 1:
                    continue
                    
                first_char = ord(line[0])
                if first_char == 96:
                    line = chr(32) + line[1:]
                elif not (32 <= first_char <= 95):
                    continue
                    
                try:
                    import binascii
                    decoded_bytes.extend(binascii.a2b_uu(line))
                except Exception:
                    pass
            
            if not decoded_bytes:
                return None
                
            # Strip trailing nulls often added as padding in uuencoding
            return decoded_bytes.decode('utf-8', errors='replace').rstrip('\x00')
        except Exception:
            return None


class ZlibDecoder(BaseDecoder):
    name = "zlib"

    def decode(self, text: str) -> Optional[str]:
        try:
            raw = text.encode('latin-1')
            decompressed = zlib.decompress(raw)
            return decompressed.decode('utf-8', errors='replace')
        except Exception:
            return None


class GzipDecoder(BaseDecoder):
    name = "gzip"

    def decode(self, text: str) -> Optional[str]:
        try:
            raw = text.encode('latin-1')
            decompressed = gzip.decompress(raw)
            return decompressed.decode('utf-8', errors='replace')
        except Exception:
            return None


# Registry
DECODERS: dict[str, BaseDecoder] = {
    'base64': Base64Decoder(),
    'base32': Base32Decoder(),
    'base85': Base85Decoder(),
    'hex': HexDecoder(),
    'binary': BinaryDecoder(),
    'decimal_ascii': DecimalAsciiDecoder(),
    'rot13': ROT13Decoder(),
    'caesar': CaesarDecoder(),
    'morse': MorseDecoder(),
    'url': URLDecoder(),
    'html_entity': HTMLEntityDecoder(),
    'unicode_escape': UnicodeEscapeDecoder(),
    'uuencoding': UUDecoder(),
    'zlib': ZlibDecoder(),
    'gzip': GzipDecoder(),
    'xor': XORDecoder(),
}
