"""
Text-based steganography detection and extraction.
Handles: zero-width characters, whitespace encoding, Unicode tricks.
"""
from __future__ import annotations
import re


# Zero-width Unicode characters used in text stego
ZERO_WIDTH = {
    "\u200b": "0",  # Zero-width space → 0
    "\u200c": "1",  # Zero-width non-joiner → 1
    "\u200d": "1",  # Zero-width joiner → 1
    "\u2060": "0",  # Word joiner → 0
    "\ufeff": "0",  # BOM / zero-width no-break space → 0
    "\u00ad": "1",  # Soft hyphen → 1
}

ZW_SPACE = "\u200b"
ZW_NON_JOINER = "\u200c"
ZW_JOINER = "\u200d"
ZW_WORD_JOINER = "\u2060"
ZW_BOM = "\ufeff"

WHITESPACE_MAP = {
    " ": "0",   # space → 0
    "\t": "1",  # tab → 1
}


def detect_zero_width_stego(text: str) -> float:
    """
    Detect presence of zero-width steganographic characters.
    Returns a confidence score between 0.0 and 1.0.
    """
    count = _count_invisible(text)
    if count >= 8:
        return 0.95
    elif count > 0:
        return 0.70
    return 0.0


def encode_zero_width(cover_text: str, secret: str) -> str:
    """
    Encode secret message into cover text using zero-width binary characters.
    Inserts payload near the midpoint of the cover text.
    """
    bits = "".join(f"{ord(c):08b}" for c in secret)
    zw_payload = "".join(ZW_NON_JOINER if b == "1" else ZW_SPACE for b in bits)
    insert_pos = len(cover_text) // 2
    return cover_text[:insert_pos] + zw_payload + cover_text[insert_pos:]


def extract_zero_width_payload(text: str) -> dict:
    """
    Extract and decode binary data encoded in zero-width characters.
    Evaluates both standard and inverted zero-width bit polarity.
    """
    chars = [c for c in text if c in ZERO_WIDTH]
    if not chars:
        return {"found": False, "bit_count": 0, "bits": "", "decoded": "", "scheme": "none"}

    bits_std = "".join(ZERO_WIDTH[c] for c in chars)
    decoded_std = _bits_to_text(bits_std)

    inv_map = {"0": "1", "1": "0"}
    bits_inv = "".join(inv_map[ZERO_WIDTH[c]] for c in chars)
    decoded_inv = _bits_to_text(bits_inv)

    from backend.scoring.scorer import score_text
    score_std = score_text(decoded_std) if decoded_std else 0.0
    score_inv = score_text(decoded_inv) if decoded_inv else 0.0

    if score_inv > score_std:
        best_bits, best_decoded, scheme = bits_inv, decoded_inv, "inverted"
    else:
        best_bits, best_decoded, scheme = bits_std, decoded_std, "standard"

    return {
        "found": True,
        "bit_count": len(chars),
        "bits": best_bits[:64] + ("..." if len(best_bits) > 64 else ""),
        "decoded": best_decoded,
        "scheme": scheme,
    }


def extract_text_stego(text: str) -> dict:
    """
    Attempt all text steganography extraction methods.
    Returns dict with findings from each method.
    """
    results = {
        "zero_width": _extract_zero_width(text),
        "whitespace": _extract_whitespace(text),
        "first_letters": _extract_acrostic(text),
        "unicode_hidden": _find_unicode_anomalies(text),
        "invisible_chars_found": _count_invisible(text),
    }
    return results


def _extract_zero_width(text: str) -> dict:
    """Extract binary data encoded in zero-width characters."""
    return extract_zero_width_payload(text)


def _extract_whitespace(text: str) -> dict:
    """Extract binary data from trailing whitespace patterns."""
    lines = text.split("\n")
    bits = []
    for line in lines:
        trailing = line[len(line.rstrip()):]
        for ch in trailing:
            if ch in WHITESPACE_MAP:
                bits.append(WHITESPACE_MAP[ch])

    # Also check space/tab patterns at line start
    for line in lines:
        for ch in line:
            if ch == "\t":
                bits.append("1")
            elif ch == " " and bits:
                bits.append("0")
            else:
                break

    if not bits:
        return {"found": False, "decoded": ""}

    bit_str = "".join(bits)
    decoded = _bits_to_text(bit_str)
    return {
        "found": len(bits) > 0,
        "bit_count": len(bits),
        "decoded": decoded,
    }


def _extract_acrostic(text: str) -> dict:
    """Extract first letter of each line/word (acrostic)."""
    lines = text.strip().split("\n")
    first_letters = "".join(line[0] for line in lines if line.strip())
    first_words = "".join(
        line.split()[0][0] for line in lines if line.strip() and line.split()
    )
    return {
        "first_letter_each_line": first_letters,
        "first_letter_each_word": first_words[:100],
    }


def _find_unicode_anomalies(text: str) -> list[dict]:
    """Find suspicious Unicode characters that may hide data."""
    anomalies = []
    for i, ch in enumerate(text):
        cp = ord(ch)
        # Homoglyphs, unusual Unicode ranges
        if (0x2000 <= cp <= 0x206F) or (0xFE00 <= cp <= 0xFE0F) or cp == 0xFEFF:
            anomalies.append({
                "position": i,
                "char": repr(ch),
                "codepoint": hex(cp),
            })
    return anomalies[:20]


def _count_invisible(text: str) -> int:
    """Count total invisible/zero-width characters."""
    return sum(1 for c in text if ord(c) in (
        0x200B, 0x200C, 0x200D, 0x2060, 0xFEFF, 0x00AD,
        0x2028, 0x2029, 0x180E,
    ))


def _bits_to_text(bit_str: str) -> str:
    """Convert binary string to ASCII text."""
    if len(bit_str) < 8:
        return ""
    chars = []
    for i in range(0, len(bit_str) - 7, 8):
        byte = int(bit_str[i:i+8], 2)
        if 32 <= byte <= 126:
            chars.append(chr(byte))
        elif byte == 0:
            break
        else:
            chars.append(".")
    return "".join(chars).strip(".")
