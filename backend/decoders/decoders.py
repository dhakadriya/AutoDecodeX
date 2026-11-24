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
import string
from typing import Optional, List, Dict, Any
from .base_decoder import BaseDecoder


def normalize_base64_padding(text: str) -> str:
    """
    Ensure a Base64 string has proper padding characters ('=').
    Calculates and appends required '=' padding.
    """
    padding = 4 - len(text) % 4
    if padding != 4:
        return text + ('=' * padding)
    return text


class Base64Decoder(BaseDecoder):
    """
    Base64 decoder with automatic padding correction.
    
    Handles standard Base64, Base64URL, and variants with/without padding.
    """
    name = "base64"
    category = "encoding"
    description = "Standard Base64 and Base64URL decoder with automatic padding"

    def decode(self, text: str) -> Optional[str]:
        try:
            cleaned = text.strip()
            if len(cleaned) < 4:
                return None

            padded = normalize_base64_padding(cleaned)

            # Reject if contains non-base64 characters
            if not re.fullmatch(r'[A-Za-z0-9+/=_\-]+', padded):
                return None

            # Try standard Base64 first
            try:
                raw_bytes = base64.b64decode(padded, validate=True)
            except Exception:
                # Try Base64URL variant
                raw_bytes = base64.urlsafe_b64decode(padded)

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


def clean_hex_string(text: str) -> str:
    """
    Remove standard hexadecimal prefixes (0x, \\x) and delimiters (space, colon, hyphen, comma).
    """
    cleaned = text.strip().replace('0x', '').replace('0X', '').replace('\\x', '').replace('\\X', '')
    cleaned = re.sub(r'[\s:\-,]+', '', cleaned)
    return cleaned


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
    category = "encoding"
    description = "Hexadecimal byte stream decoder with prefix/delimiter stripping"

    def decode(self, text: str) -> Optional[str]:
        try:
            cleaned = clean_hex_string(text)
            
            # Must be even length
            if not cleaned or len(cleaned) % 2 != 0:
                return None
                
            raw_bytes = bytes.fromhex(cleaned)
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


def parse_binary_bitstream(text: str) -> Optional[bytearray]:
    """
    Parse space-separated or continuous 8-bit binary sequences into bytes.
    """
    cleaned = text.strip()
    if not cleaned:
        return None

    parts = cleaned.split()
    if parts and all(re.fullmatch(r'[01]{8}', p) for p in parts):
        return bytearray(int(p, 2) for p in parts)

    continuous = "".join(parts)
    if re.fullmatch(r'[01]+', continuous) and len(continuous) % 8 == 0:
        return bytearray(int(continuous[i:i+8], 2) for i in range(0, len(continuous), 8))

    return None


class BinaryDecoder(BaseDecoder):
    name = "binary"
    category = "encoding"
    description = "8-bit binary representation decoder (space-separated or continuous)"

    def decode(self, text: str) -> Optional[str]:
        try:
            raw_bytes = parse_binary_bitstream(text)
            if raw_bytes is None:
                return None
            try:
                return raw_bytes.decode('utf-8')
            except UnicodeDecodeError:
                return raw_bytes.decode('latin-1')
        except Exception:
            return None


class DecimalAsciiDecoder(BaseDecoder):
    """
    Decimal ASCII code sequence decoder.
    Converts decimal integer byte values (0-255) into decoded text.
    Supports space, comma, semicolon, and hyphen delimiters.
    """
    name = "decimal_ascii"
    category = "encoding"
    description = "Decimal ASCII byte code sequence decoder"

    def decode(self, text: str) -> Optional[str]:
        if not text:
            return None
        try:
            clean = text.strip()
            parts = [p.strip() for p in re.split(r'[,;\s\-]+', clean) if p.strip()]
            if not parts:
                return None
            nums = [int(p) for p in parts]
            if not all(0 <= n <= 255 for n in nums):
                return None
            raw_bytes = bytes(nums)
            try:
                return raw_bytes.decode('utf-8')
            except UnicodeDecodeError:
                return raw_bytes.decode('latin-1')
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


class AtbashDecoder(BaseDecoder):
    """
    Atbash substitution cipher decoder (A <-> Z, B <-> Y, etc.).
    Preserves casing and non-alphabetic characters.
    """
    name = "atbash"
    category = "cipher"
    description = "Atbash reciprocal alphabet substitution cipher"

    def decode(self, text: str) -> Optional[str]:
        if not text:
            return None
        if not any(c.isalpha() for c in text):
            return None
        trans = []
        for ch in text:
            if 'a' <= ch <= 'z':
                trans.append(chr(ord('z') - (ord(ch) - ord('a'))))
            elif 'A' <= ch <= 'Z':
                trans.append(chr(ord('Z') - (ord(ch) - ord('A'))))
            else:
                trans.append(ch)
        decoded = "".join(trans)
        return decoded if decoded != text else None


class BaconianDecoder(BaseDecoder):
    """
    Bacon's cipher decoder.
    Decodes 5-character sequences of A/B into Latin alphabet characters.
    Supports both space-separated and continuous representations.
    """
    name = "baconian"
    category = "cipher"
    description = "Bacon 5-bit binary alphabet cipher"

    BACON_DICT = {
        'AAAAA': 'A', 'AAAAB': 'B', 'AAABA': 'C', 'AAABB': 'D', 'AABAA': 'E',
        'AABAB': 'F', 'AABBA': 'G', 'AABBB': 'H', 'ABAAA': 'I', 'ABAAB': 'J',
        'ABABA': 'K', 'ABABB': 'L', 'ABBAA': 'M', 'ABBAB': 'N', 'ABBBA': 'O',
        'ABBBB': 'P', 'BAAAA': 'Q', 'BAAAB': 'R', 'BAABA': 'S', 'BAABB': 'T',
        'BABAA': 'U', 'BABAB': 'V', 'BABBA': 'W', 'BABBB': 'X', 'BBAAA': 'Y',
        'BBAAB': 'Z'
    }

    def decode(self, text: str) -> Optional[str]:
        if not text:
            return None
        clean = text.strip()
        tokens = clean.split()
        # Case 1: Space-separated 5-letter blocks
        if tokens and all(len(t) == 5 and set(t.upper()).issubset({'A', 'B'}) for t in tokens):
            decoded = "".join(self.BACON_DICT.get(t.upper(), "?") for t in tokens)
            return decoded if "?" not in decoded else None

        # Case 2: Continuous stream of A/B characters
        no_spaces = "".join(clean.split()).upper()
        if len(no_spaces) >= 5 and len(no_spaces) % 5 == 0 and set(no_spaces).issubset({'A', 'B'}):
            chunks = [no_spaces[i:i+5] for i in range(0, len(no_spaces), 5)]
            decoded = "".join(self.BACON_DICT.get(c, "?") for c in chunks)
            return decoded if "?" not in decoded else None

        return None


class A1Z26Decoder(BaseDecoder):
    """
    A1Z26 letter-number substitution decoder.
    Converts numbers 1-26 (separated by hyphens, spaces, or commas) to letters.
    """
    name = "a1z26"
    category = "cipher"
    description = "A1Z26 numerical alphabet position substitution"

    def decode(self, text: str) -> Optional[str]:
        if not text:
            return None
        clean = text.strip()
        tokens = [t for t in re.split(r'[\s\-,]+', clean) if t]
        if not tokens or len(tokens) < 2:
            return None
        chars = []
        for t in tokens:
            if not t.isdigit():
                return None
            val = int(t)
            if not (1 <= val <= 26):
                return None
            chars.append(chr(ord('A') + val - 1))
        return "".join(chars)


class OctalDecoder(BaseDecoder):
    """
    Octal byte representation decoder.
    Converts space-separated, backslash-prefixed, or 0o-prefixed octal numbers into text.
    """
    name = "octal"
    category = "encoding"
    description = "Base-8 octal byte representation decoder"

    def decode(self, text: str) -> Optional[str]:
        if not text:
            return None
        clean = text.strip()
        if clean.startswith("\\"):
            tokens = [t for t in clean.split("\\") if t]
        else:
            tokens = [t.lower().replace("0o", "") for t in clean.split() if t]

        if not tokens or len(tokens) < 2:
            return None

        decoded_bytes = bytearray()
        for t in tokens:
            if not re.fullmatch(r'[0-7]{1,3}', t):
                return None
            val = int(t, 8)
            if val > 255:
                return None
            decoded_bytes.append(val)

        try:
            return decoded_bytes.decode('utf-8')
        except UnicodeDecodeError:
            return decoded_bytes.decode('latin-1')


class BrailleDecoder(BaseDecoder):
    """
    Braille Unicode transcript decoder.
    Converts Unicode Braille patterns (U+2800..U+28FF) into Latin alphabet characters.
    """
    name = "braille"
    category = "cipher"
    description = "Unicode Braille patterns to Latin alphabet decoder"

    BRAILLE_MAP = {
        '⠁': 'a', '⠃': 'b', '⠉': 'c', '⠙': 'd', '⠑': 'e', '⠋': 'f', '⠛': 'g',
        '⠓': 'h', '⠊': 'i', '⠚': 'j', '⠅': 'k', '⠇': 'l', '⠍': 'm', '⠝': 'n',
        '⠕': 'o', '⠏': 'p', '⠟': 'q', '⠗': 'r', '⠎': 's', '⠞': 't', '⠥': 'u',
        '⠧': 'v', '⠺': 'w', '⠭': 'x', '⠽': 'y', '⠵': 'z', '⠀': ' ',
        '⠂': ',', '⠲': '.', '⠦': '?', '⠖': '!', '⠤': '-', '⠒': ':',
    }

    def decode(self, text: str) -> Optional[str]:
        if not text:
            return None
        clean = text.strip()
        braille_chars = [c for c in clean if '\u2800' <= c <= '\u28ff']
        if not braille_chars or len(braille_chars) < len(clean) * 0.5:
            return None
        decoded = []
        for ch in clean:
            if ch in self.BRAILLE_MAP:
                decoded.append(self.BRAILLE_MAP[ch])
            elif ch in (' ', '\n', '\t'):
                decoded.append(ch)
            else:
                decoded.append(ch)
        res = "".join(decoded)
        return res if res != clean else None


class ReverseDecoder(BaseDecoder):
    """
    Reverse string decoder (mirror text).
    Reverses the character sequence of the input string.
    """
    name = "reverse"
    category = "cipher"
    description = "Reverses input character sequence"

    def decode(self, text: str) -> Optional[str]:
        if not text:
            return None
        clean = text.strip()
        if len(clean) < 2:
            return None
        reversed_text = clean[::-1]
        return reversed_text if reversed_text != clean else None


class NATOPhoneticDecoder(BaseDecoder):
    """
    NATO phonetic spelling alphabet transcript decoder.
    Converts phonetic words (Alfa/Alpha, Bravo, Charlie...) into spelled letters/digits.
    """
    name = "nato"
    category = "cipher"
    description = "NATO phonetic spelling alphabet transcript decoder"

    NATO_MAP = {
        'ALFA': 'A', 'ALPHA': 'A', 'BRAVO': 'B', 'CHARLIE': 'C', 'DELTA': 'D',
        'ECHO': 'E', 'FOXTROT': 'F', 'GOLF': 'G', 'HOTEL': 'H', 'INDIA': 'I',
        'JULIETT': 'J', 'JULIET': 'J', 'KILO': 'K', 'LIMA': 'L', 'MIKE': 'M',
        'NOVEMBER': 'N', 'OSCAR': 'O', 'PAPA': 'P', 'QUEBEC': 'Q', 'ROMEO': 'R',
        'SIERRA': 'S', 'TANGO': 'T', 'UNIFORM': 'U', 'VICTOR': 'V', 'WHISKEY': 'W',
        'XRAY': 'X', 'X-RAY': 'X', 'YANKEE': 'Y', 'ZULU': 'Z',
        'ZERO': '0', 'ONE': '1', 'TWO': '2', 'THREE': '3', 'FOUR': '4',
        'FIVE': '5', 'SIX': '6', 'SEVEN': '7', 'EIGHT': '8', 'NINE': '9'
    }

    def decode(self, text: str) -> Optional[str]:
        if not text:
            return None
        clean = text.strip()
        tokens = [t.strip(",.;:-").upper() for t in clean.split() if t.strip(",.;:-")]
        if not tokens or len(tokens) < 2:
            return None

        matched = [self.NATO_MAP[t] for t in tokens if t in self.NATO_MAP]
        if len(matched) < len(tokens) * 0.7 or len(matched) < 2:
            return None

        return "".join(self.NATO_MAP.get(t, t) for t in tokens)


class VigenereDecoder(BaseDecoder):
    """
    Vigenere polyalphabetic substitution cipher decoder.
    Decrypts ciphertext using a repeating keyword.
    Preserves case and non-alphabetic characters.
    """
    name = "vigenere"
    category = "cipher"
    description = "Vigenere polyalphabetic substitution cipher decoder"

    DEFAULT_KEYS = ["KEY", "SECRET", "FLAG", "CIPHER", "PASS", "PASSWORD", "CRYPTO", "ADMIN"]

    @staticmethod
    def decrypt_with_key(text: str, key: str) -> str:
        """Decrypts ciphertext using the specified alphabetic key."""
        clean_key = [c.upper() for c in key if c.isalpha()]
        if not clean_key:
            return text

        result = []
        key_idx = 0
        key_len = len(clean_key)

        for char in text:
            if char.isalpha():
                shift = ord(clean_key[key_idx % key_len]) - ord('A')
                base = ord('A') if char.isupper() else ord('a')
                decrypted_char = chr((ord(char) - base - shift) % 26 + base)
                result.append(decrypted_char)
                key_idx += 1
            else:
                result.append(char)
        return "".join(result)

    def decode(self, text: str, key: Optional[str] = None) -> Optional[str]:
        if not text or not any(c.isalpha() for c in text):
            return None

        if key:
            decrypted = self.decrypt_with_key(text, key)
            return decrypted if decrypted != text else None

        from backend.scoring.scorer import score_text
        best_candidate = None
        best_score = 0.55

        for cand_key in self.DEFAULT_KEYS:
            decrypted = self.decrypt_with_key(text, cand_key)
            cand_score = score_text(decrypted)
            if cand_score > best_score:
                best_score = cand_score
                best_candidate = decrypted

        return best_candidate


class AffineDecoder(BaseDecoder):
    """
    Affine cipher decoder.
    Monoalphabetic substitution: E(x) = (a*x + b) mod 26, D(y) = a_inv*(y - b) mod 26.
    Supports explicit (a, b) parameters or brute-force search over all 312 coprime keys.
    """
    name = "affine"
    category = "cipher"
    description = "Affine substitution cipher decoder with modular inverse search"

    COPRIME_A = [1, 3, 5, 7, 9, 11, 15, 17, 19, 21, 23, 25]

    @staticmethod
    def decrypt(text: str, a: int, b: int) -> str:
        """Decrypts text with Affine key parameters a and b."""
        try:
            a_inv = pow(a, -1, 26)
        except ValueError:
            return text
        result = []
        for char in text:
            if char.isalpha():
                base = ord('A') if char.isupper() else ord('a')
                dec = (a_inv * (ord(char) - base - b)) % 26
                result.append(chr(dec + base))
            else:
                result.append(char)
        return "".join(result)

    def decode(self, text: str, a: Optional[int] = None, b: Optional[int] = None) -> Optional[str]:
        if not text or not any(c.isalpha() for c in text):
            return None

        if a is not None and b is not None:
            decrypted = self.decrypt(text, a, b)
            return decrypted if decrypted != text else None

        from backend.scoring.scorer import score_text
        best_candidate = None
        best_score = 0.65

        for cand_a in self.COPRIME_A:
            for cand_b in range(26):
                if cand_a == 1 and cand_b == 0:
                    continue
                decrypted = self.decrypt(text, cand_a, cand_b)
                cand_score = score_text(decrypted)
                if cand_score > best_score:
                    best_score = cand_score
                    best_candidate = decrypted

        return best_candidate


class RailFenceDecoder(BaseDecoder):
    """
    Rail Fence transposition cipher decoder.
    Reconstructs plaintext from zigzag rail lines.
    Supports explicit rails parameter or automatic rail depth search.
    """
    name = "rail_fence"
    category = "cipher"
    description = "Rail Fence transposition cipher decoder with rail depth search"

    @staticmethod
    def decrypt(ciphertext: str, rails: int) -> str:
        """Decrypts ciphertext using the specified number of rails."""
        if rails <= 1 or rails >= len(ciphertext):
            return ciphertext

        grid = [[None] * len(ciphertext) for _ in range(rails)]
        row, step = 0, 1
        for col in range(len(ciphertext)):
            grid[row][col] = '*'
            if row == 0:
                step = 1
            elif row == rails - 1:
                step = -1
            row += step

        idx = 0
        for r in range(rails):
            for c in range(len(ciphertext)):
                if grid[r][c] == '*' and idx < len(ciphertext):
                    grid[r][c] = ciphertext[idx]
                    idx += 1

        result = []
        row, step = 0, 1
        for col in range(len(ciphertext)):
            result.append(grid[row][col])
            if row == 0:
                step = 1
            elif row == rails - 1:
                step = -1
            row += step

        return "".join(result)

    def decode(self, text: str, rails: Optional[int] = None) -> Optional[str]:
        if not text or len(text) < 4:
            return None

        clean = text.strip()
        if rails is not None:
            decrypted = self.decrypt(clean, rails)
            return decrypted if decrypted != clean else None

        from backend.scoring.scorer import score_text
        best_candidate = None
        best_score = 0.60
        max_rails = min(12, len(clean) // 2 + 1)

        for cand_rails in range(2, max_rails):
            decrypted = self.decrypt(clean, cand_rails)
            cand_score = score_text(decrypted)
            if cand_score > best_score:
                best_score = cand_score
                best_candidate = decrypted

        return best_candidate


class PolybiusDecoder(BaseDecoder):
    """
    Polybius square 5x5 coordinate cipher decoder.
    Decodes coordinate pairs (1-5 or 0-4) into letters (A-Z, with I/J mapped to I).
    Supports space, hyphen, comma, slash delimited tokens and continuous digit streams.
    """
    name = "polybius"
    category = "cipher"
    description = "Polybius square 5x5 coordinate cipher decoder"

    POLYBIUS_1 = {
        '11': 'A', '12': 'B', '13': 'C', '14': 'D', '15': 'E',
        '21': 'F', '22': 'G', '23': 'H', '24': 'I', '25': 'K',
        '31': 'L', '32': 'M', '33': 'N', '34': 'O', '35': 'P',
        '41': 'Q', '42': 'R', '43': 'S', '44': 'T', '45': 'U',
        '51': 'V', '52': 'W', '53': 'X', '54': 'Y', '55': 'Z',
    }

    POLYBIUS_0 = {
        '00': 'A', '01': 'B', '02': 'C', '03': 'D', '04': 'E',
        '10': 'F', '11': 'G', '12': 'H', '13': 'I', '14': 'K',
        '20': 'L', '21': 'M', '22': 'N', '23': 'O', '24': 'P',
        '30': 'Q', '31': 'R', '32': 'S', '33': 'T', '34': 'U',
        '40': 'V', '41': 'W', '42': 'X', '43': 'Y', '44': 'Z',
    }

    def decode(self, text: str) -> Optional[str]:
        if not text:
            return None

        clean = text.strip()
        words = re.split(r'\s*/\s*|\s{2,}', clean) if ('/' in clean or '  ' in clean) else [clean]
        decoded_words = []

        for word in words:
            tokens = [t.strip() for t in re.split(r'[\s,\-]+', word.strip()) if t.strip()]
            if len(tokens) >= 2 and all(len(t) == 2 and t.isdigit() for t in tokens):
                if all(t in self.POLYBIUS_1 for t in tokens):
                    decoded_words.append("".join(self.POLYBIUS_1[t] for t in tokens))
                elif all(t in self.POLYBIUS_0 for t in tokens):
                    decoded_words.append("".join(self.POLYBIUS_0[t] for t in tokens))
                else:
                    return None
            else:
                digits = re.sub(r'\s+', '', word)
                if len(digits) >= 4 and len(digits) % 2 == 0 and digits.isdigit():
                    pairs = [digits[i:i+2] for i in range(0, len(digits), 2)]
                    if all(p in self.POLYBIUS_1 for p in pairs):
                        decoded_words.append("".join(self.POLYBIUS_1[p] for p in pairs))
                    elif all(p in self.POLYBIUS_0 for p in pairs):
                        decoded_words.append("".join(self.POLYBIUS_0[p] for p in pairs))
                    else:
                        return None
                else:
                    return None

        return " ".join(decoded_words) if decoded_words else None


class BrainfuckDecoder(BaseDecoder):
    """
    Brainfuck esoteric programming language decoder.
    Executes valid Brainfuck programs within a safe step-limited virtual machine.
    """
    name = "brainfuck"
    category = "esoteric"
    description = "Brainfuck esoteric programming language interpreter with execution limits"

    MAX_STEPS = 100000
    TAPE_SIZE = 3000

    def decode(self, text: str) -> Optional[str]:
        if not text:
            return None

        bf_chars = set('><+-.,[]')
        clean = ''.join(c for c in text if c in bf_chars)
        non_space = re.sub(r'\s+', '', text)
        if not non_space or len(clean) < 8 or '.' not in clean:
            return None
        if len(clean) / len(non_space) < 0.60:
            return None

        brackets = {}
        stack = []
        for i, c in enumerate(clean):
            if c == '[':
                stack.append(i)
            elif c == ']':
                if not stack:
                    return None
                start = stack.pop()
                brackets[start] = i
                brackets[i] = start
        if stack:
            return None

        tape = [0] * self.TAPE_SIZE
        ptr = 0
        pc = 0
        steps = 0
        output = []

        while pc < len(clean) and steps < self.MAX_STEPS:
            steps += 1
            cmd = clean[pc]
            if cmd == '>':
                ptr = (ptr + 1) % self.TAPE_SIZE
            elif cmd == '<':
                ptr = (ptr - 1) % self.TAPE_SIZE
            elif cmd == '+':
                tape[ptr] = (tape[ptr] + 1) % 256
            elif cmd == '-':
                tape[ptr] = (tape[ptr] - 1) % 256
            elif cmd == '.':
                output.append(chr(tape[ptr]))
            elif cmd == '[':
                if tape[ptr] == 0:
                    pc = brackets[pc]
            elif cmd == ']':
                if tape[ptr] != 0:
                    pc = brackets[pc]
            pc += 1

        if not output:
            return None

        result = "".join(output)
        if any(c in string.printable for c in result):
            return result
        return None


# Registry
DECODERS: dict[str, BaseDecoder] = {
    'base64': Base64Decoder(),
    'base32': Base32Decoder(),
    'base85': Base85Decoder(),
    'hex': HexDecoder(),
    'binary': BinaryDecoder(),
    'decimal_ascii': DecimalAsciiDecoder(),
    'octal': OctalDecoder(),
    'rot13': ROT13Decoder(),
    'caesar': CaesarDecoder(),
    'atbash': AtbashDecoder(),
    'baconian': BaconianDecoder(),
    'a1z26': A1Z26Decoder(),
    'braille': BrailleDecoder(),
    'reverse': ReverseDecoder(),
    'nato': NATOPhoneticDecoder(),
    'vigenere': VigenereDecoder(),
    'affine': AffineDecoder(),
    'rail_fence': RailFenceDecoder(),
    'polybius': PolybiusDecoder(),
    'brainfuck': BrainfuckDecoder(),
    'morse': MorseDecoder(),
    'url': URLDecoder(),
    'html_entity': HTMLEntityDecoder(),
    'unicode_escape': UnicodeEscapeDecoder(),
    'uuencoding': UUDecoder(),
    'zlib': ZlibDecoder(),
    'gzip': GzipDecoder(),
    'xor': XORDecoder(),
}
