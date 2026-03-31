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

WHITESPACE_MAP = {
    " ": "0",   # space → 0
    "\t": "1",  # tab → 1
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
    bits = []
    for char in text:
        if char in ZERO_WIDTH:
            bits.append(ZERO_WIDTH[char])

    if not bits:
        return {"found": False, "bits": "", "decoded": ""}

    bit_str = "".join(bits)
    decoded = _bits_to_text(bit_str)
    return {
        "found": True,
        "bit_count": len(bits),
        "bits": bit_str[:64] + ("..." if len(bit_str) > 64 else ""),
        "decoded": decoded,
    }


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
