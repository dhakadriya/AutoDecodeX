"""
Detectors: heuristic-based encoding type detection.

Each detector returns a confidence score (0.0 - 1.0) based on multiple heuristics:
- Character set validation
- Length patterns
- Entropy analysis
- Format patterns
- Padding validation
- Expected byte distribution

The detection engine uses multiple signals to avoid false positives.
"""
import re
import math
import html
from collections import Counter


def _entropy(text: str) -> float:
    if not text:
        return 0.0
    counts = Counter(text)
    total = len(text)
    return -sum((c / total) * math.log2(c / total) for c in counts.values())


def detect_base64(text: str) -> float:
    text = text.strip()
    # Base64 charset + optional padding
    if not re.fullmatch(r'[A-Za-z0-9+/=]+=*', text):
        return 0.0
    
    # Must have at least 4 characters
    if len(text) < 4:
        return 0.0
    
    # Remove padding for length check
    text_no_padding = text.rstrip('=')
    padding_count = len(text) - len(text_no_padding)
    
    # Length validation: after removing padding, should be close to multiple of 4
    # Original length should be multiple of 4 with padding
    if len(text) % 4 != 0:
        return 0.3
    
    # Too much padding is suspicious
    if padding_count > 2:
        return 0.2
    
    # Character distribution check: Base64 should have good mix of chars
    char_set = set(text_no_padding)
    if len(char_set) < 4 and len(text_no_padding) > 10:
        return 0.4  # Too few unique chars
    
    # Entropy check: base64 has moderate-high entropy
    e = _entropy(text_no_padding)
    if e < 3.0:
        return 0.4  # Too low entropy
    
    # High confidence scoring based on entropy and structure
    confidence = 0.75
    
    # Boost for good entropy
    if e >= 4.5:
        confidence = 0.95
    elif e >= 4.0:
        confidence = 0.90
    elif e >= 3.5:
        confidence = 0.85
    
    # Boost if length is exactly multiple of 4
    if len(text) % 4 == 0:
        confidence += 0.03
    
    return min(0.98, confidence)


def detect_base32(text: str) -> float:
    text = text.strip().upper()
    if not re.fullmatch(r'[A-Z2-7]+=*', text):
        return 0.0
    if len(text) % 8 != 0:
        return 0.3
    return 0.88


def detect_base85(text: str) -> float:
    text = text.strip()
    if not text:
        return 0.0
    # ASCII85 uses chars 33-117
    if all(33 <= ord(c) <= 117 for c in text):
        return 0.75
    return 0.0


def detect_hex(text: str) -> float:
    text = text.strip().replace(' ', '').replace('0x', '')
    if not re.fullmatch(r'[0-9a-fA-F]+', text):
        return 0.0
    if len(text) % 2 != 0:
        return 0.4
    return 0.90


def detect_binary(text: str) -> float:
    text = text.strip()
    # Binary: groups of 8 bits separated by spaces
    parts = text.split()
    if all(re.fullmatch(r'[01]{8}', p) for p in parts) and len(parts) > 0:
        return 0.95
    # Or a long binary string
    if re.fullmatch(r'[01]+', text) and len(text) % 8 == 0:
        return 0.85
    return 0.0


def detect_decimal_ascii(text: str) -> float:
    text = text.strip()
    parts = text.split()
    if len(parts) < 2:
        return 0.0
    try:
        nums = [int(p) for p in parts]
        if all(32 <= n <= 126 for n in nums):
            return 0.88
        return 0.2
    except ValueError:
        return 0.0


def detect_rot13(text: str) -> float:
    # ROT13 looks like normal text but with shifted letters
    # Should NOT detect Base64, hex, or other encodings
    
    # Reject if it looks like Base64 (has = padding or too many capital/lowercase/digit mix)
    if '=' in text or re.search(r'[+/]', text):
        return 0.0
    
    # Reject if looks like hex (only hex chars, even length, no spaces)
    clean = text.replace(' ', '')
    if re.fullmatch(r'[0-9a-fA-F]+', clean) and len(clean) % 2 == 0 and len(clean) > 8:
        return 0.0
    
    # ROT13 should have mostly letters
    alpha_ratio = sum(1 for c in text if c.isalpha()) / max(len(text), 1)
    if alpha_ratio < 0.6:
        return 0.0
    
    # Check for common English letter patterns vs ROT13 patterns
    lower = text.lower()
    
    # In ROT13, common English letters (etaoin) become (rgnbva)
    # Count frequency of typical ROT13-shifted letters
    rot13_indicators = sum(lower.count(c) for c in 'rgnbva')
    plain_indicators = sum(lower.count(c) for c in 'etaoin')
    
    total_letters = sum(1 for c in lower if c.isalpha())
    if total_letters == 0:
        return 0.0
    
    rot13_ratio = rot13_indicators / total_letters
    plain_ratio = plain_indicators / total_letters
    
    # If we have reasonable letter distribution and looks text-like with spaces
    if ' ' in text and alpha_ratio > 0.75:
        # Check if it has unusual letter patterns (might be ROT13)
        # Common words that would appear in ROT13: uryyb (hello), jbeyq (world)
        rot13_words = ['uryyb', 'jbeyq', 'gur', 'naq', 'gb', 'bs']
        has_rot13_word = any(word in lower for word in rot13_words)
        
        if has_rot13_word:
            return 0.85  # High confidence if we see known ROT13 words
        elif rot13_ratio > plain_ratio:
            return 0.65
        else:
            return 0.45
    
    # Single word, mostly letters
    if alpha_ratio > 0.9:
        return 0.50
    
    return 0.35


def detect_caesar(text: str) -> float:
    # Reject if it looks like Base64 (has = padding or +/)
    if '=' in text or re.search(r'[+/]', text):
        return 0.0
    
    # Reject if looks like hex
    clean = text.replace(' ', '')
    if re.fullmatch(r'[0-9a-fA-F]+', clean) and len(clean) % 2 == 0:
        return 0.0
    
    alpha_ratio = sum(1 for c in text if c.isalpha()) / max(len(text), 1)
    if alpha_ratio > 0.5:
        return 0.45
    return 0.0


def detect_morse(text: str) -> float:
    text = text.strip()
    # Morse uses dots, dashes, spaces, slashes
    if re.fullmatch(r'[.\-/ ]+', text):
        return 0.93
    return 0.0


def detect_url_encoding(text: str) -> float:
    if '%' in text and re.search(r'%[0-9a-fA-F]{2}', text):
        ratio = len(re.findall(r'%[0-9a-fA-F]{2}', text)) / max(len(text) / 3, 1)
        return min(0.95, 0.6 + ratio * 0.35)
    return 0.0


def detect_html_entity(text: str) -> float:
    """
    Detect HTML entity encoding.
    Looks for &name; or &#digits; or &#xhex; patterns.
    """
    if '&' not in text or ';' not in text:
        return 0.0
    
    # Count named entities (&amp;, &lt;, etc.)
    named_entities = len(re.findall(r'&[a-zA-Z]{2,10};', text))
    
    # Count numeric entities (&#65; &#x41;)
    numeric_entities = len(re.findall(r'&#x?[0-9a-fA-F]+;', text))
    
    total_entities = named_entities + numeric_entities
    
    if total_entities == 0:
        return 0.0
    
    # Check if unescaping would change the text
    unescaped = html.unescape(text)
    if unescaped == text:
        return 0.0
    
    # Higher confidence if many entities
    entity_ratio = total_entities / (len(text) / 5)  # Assume ~5 chars per entity
    confidence = min(0.94, 0.6 + entity_ratio * 0.3)
    
    return confidence


def detect_unicode_escape(text: str) -> float:
    """
    Detect Unicode escape sequences.
    Looks for \\uXXXX or \\UXXXXXXXX patterns.
    """
    if '\\u' not in text and '\\U' not in text:
        return 0.0
    
    # Count valid unicode escapes
    u4_escapes = len(re.findall(r'\\u[0-9a-fA-F]{4}', text))
    u8_escapes = len(re.findall(r'\\U[0-9a-fA-F]{8}', text))
    
    total_escapes = u4_escapes + u8_escapes
    
    if total_escapes == 0:
        return 0.0
    
    # Higher confidence if many escapes
    escape_ratio = total_escapes / (len(text) / 6)  # Assume ~6 chars per escape
    confidence = min(0.92, 0.65 + escape_ratio * 0.25)
    
    return confidence


def detect_uuencoding(text: str) -> float:
    text = text.strip()
    if not text:
        return 0.0
    
    lines = text.splitlines()
    has_markers = text.startswith("begin ") and any(line.strip() == "end" for line in lines[-2:])
    if has_markers:
        return 0.92
    
    valid_lines = 0
    total_lines = 0
    for line in lines:
        line = line.strip()
        if not line:
            continue
        total_lines += 1
        if len(line) > 0 and 32 <= ord(line[0]) <= 95:
            if all(32 <= ord(c) <= 96 for c in line):
                valid_lines += 1
                
    if total_lines > 0 and valid_lines / total_lines >= 0.8:
        if total_lines > 2:
            return 0.82
        return 0.60
    return 0.0


def detect_zlib(text: str) -> float:
    try:
        raw = text.encode('latin-1')
        if len(raw) < 4:
            return 0.0
        cmf = raw[0]
        flg = raw[1]
        if (cmf & 0x0F) == 8 and ((cmf >> 4) <= 7):
            if (cmf * 256 + flg) % 31 == 0:
                return 0.95
    except Exception:
        pass
    return 0.0


def detect_gzip(text: str) -> float:
    try:
        raw = text.encode('latin-1')
        if len(raw) < 10:
            return 0.0
        if raw[0] == 0x1F and raw[1] == 0x8B and raw[2] == 8:
            return 0.96
    except Exception:
        pass
    return 0.0


def detect_md5(text: str) -> float:
    text = text.strip()
    if re.fullmatch(r'[0-9a-fA-F]{32}', text):
        return 0.95
    return 0.0


def detect_sha1(text: str) -> float:
    text = text.strip()
    if re.fullmatch(r'[0-9a-fA-F]{40}', text):
        return 0.95
    return 0.0


def detect_sha224(text: str) -> float:
    text = text.strip()
    if re.fullmatch(r'[0-9a-fA-F]{56}', text):
        return 0.95
    return 0.0


def detect_sha256(text: str) -> float:
    text = text.strip()
    if re.fullmatch(r'[0-9a-fA-F]{64}', text):
        return 0.95
    return 0.0


def detect_sha384(text: str) -> float:
    text = text.strip()
    if re.fullmatch(r'[0-9a-fA-F]{96}', text):
        return 0.95
    return 0.0


def detect_sha512(text: str) -> float:
    text = text.strip()
    if re.fullmatch(r'[0-9a-fA-F]{128}', text):
        return 0.95
    return 0.0


# Registry: name → detector function
DETECTORS = {
    'base64': detect_base64,
    'base32': detect_base32,
    'base85': detect_base85,
    'hex': detect_hex,
    'binary': detect_binary,
    'decimal_ascii': detect_decimal_ascii,
    'rot13': detect_rot13,
    'caesar': detect_caesar,
    'morse': detect_morse,
    'url': detect_url_encoding,
    'html_entity': detect_html_entity,
    'unicode_escape': detect_unicode_escape,
    'uuencoding': detect_uuencoding,
    'zlib': detect_zlib,
    'gzip': detect_gzip,
    'md5': detect_md5,
    'sha1': detect_sha1,
    'sha224': detect_sha224,
    'sha256': detect_sha256,
    'sha384': detect_sha384,
    'sha512': detect_sha512,
}


def detect_all(text: str) -> list[dict]:
    """
    Run all detectors and return sorted list of {type, confidence}.
    Only includes results with confidence > 0.
    """
    results = []
    for name, fn in DETECTORS.items():
        conf = fn(text)
        if conf > 0.0:
            results.append({'type': name, 'confidence': round(conf, 3)})
    results.sort(key=lambda x: x['confidence'], reverse=True)
    return results
