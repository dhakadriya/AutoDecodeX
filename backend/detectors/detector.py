"""
Detectors: heuristic-based encoding type detection.
Each detector returns a confidence score (0.0 - 1.0).
"""
import re
import math
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
    if not re.fullmatch(r'[A-Za-z0-9+/]+=*', text):
        return 0.0
    # Length must be multiple of 4 (with padding) or close to it
    if len(text) % 4 != 0:
        return 0.3
    # Entropy check: base64 has moderate-high entropy
    e = _entropy(text)
    if e < 3.5:
        return 0.4
    return 0.92


def detect_base32(text: str) -> float:
    text = text.strip().upper()
    if not re.fullmatch(r'[A-Z2-7]+=*', text):
        return 0.0
    if len(text) % 8 != 0:
        return 0.3
    return 0.88


def detect_base85(text: str) -> float:
    text = text.strip()
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
    # Hard to detect without scoring — give moderate confidence if mostly alpha
    alpha_ratio = sum(1 for c in text if c.isalpha()) / max(len(text), 1)
    if alpha_ratio > 0.6:
        return 0.55  # moderate — needs scoring to confirm
    return 0.0


def detect_caesar(text: str) -> float:
    alpha_ratio = sum(1 for c in text if c.isalpha()) / max(len(text), 1)
    if alpha_ratio > 0.5:
        return 0.50
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
