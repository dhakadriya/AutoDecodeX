"""
All decoder implementations.
"""
import base64
import binascii
import urllib.parse
import re
from typing import Optional
from .base_decoder import BaseDecoder


class Base64Decoder(BaseDecoder):
    name = "base64"

    def decode(self, text: str) -> Optional[str]:
        try:
            text = text.strip()
            # Add padding if needed
            padding = 4 - len(text) % 4
            if padding != 4:
                text += '=' * padding
            decoded = base64.b64decode(text).decode('utf-8', errors='replace')
            # Reject if too many replacement chars
            if decoded.count('\ufffd') > len(decoded) * 0.1:
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
            decoded = base64.b32decode(text).decode('utf-8', errors='replace')
            if decoded.count('\ufffd') > len(decoded) * 0.1:
                return None
            return decoded
        except Exception:
            return None


class Base85Decoder(BaseDecoder):
    name = "base85"

    def decode(self, text: str) -> Optional[str]:
        try:
            decoded = base64.b85decode(text.strip()).decode('utf-8', errors='replace')
            if decoded.count('\ufffd') > len(decoded) * 0.1:
                return None
            return decoded
        except Exception:
            return None


class HexDecoder(BaseDecoder):
    name = "hex"

    def decode(self, text: str) -> Optional[str]:
        try:
            text = text.strip().replace(' ', '').replace('0x', '').replace('\\x', '')
            decoded = bytes.fromhex(text).decode('utf-8', errors='replace')
            if decoded.count('\ufffd') > len(decoded) * 0.1:
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
    'xor': XORDecoder(),
}
