"""
Scoring module: evaluates how "readable" or "plaintext-like" a string is.

Returns a confidence score between 0.0 and 1.0 based on multiple signals:
- English letter frequency analysis
- Printable character ratio
- Word structure and spacing
- Common word detection
- CTF flag pattern matching
- Non-printable character penalties

This scoring is crucial for determining when recursive decoding should stop.
"""
import re
import string
from typing import Set

# Common English letter frequencies (approximate %)
ENGLISH_FREQ = {
    'e': 12.7, 't': 9.1, 'a': 8.2, 'o': 7.5, 'i': 7.0,
    'n': 6.7, 's': 6.3, 'h': 6.1, 'r': 6.0, 'd': 4.3,
    'l': 4.0, 'c': 2.8, 'u': 2.8, 'm': 2.4, 'w': 2.4,
    'f': 2.2, 'g': 2.0, 'y': 2.0, 'p': 1.9, 'b': 1.5,
    'v': 1.0, 'k': 0.8, 'j': 0.2, 'x': 0.2, 'q': 0.1, 'z': 0.1,
}

# Common English words for validation
COMMON_WORDS: Set[str] = {
    'the', 'be', 'to', 'of', 'and', 'a', 'in', 'that', 'have', 'i',
    'it', 'for', 'not', 'on', 'with', 'he', 'as', 'you', 'do', 'at',
    'this', 'but', 'his', 'by', 'from', 'they', 'we', 'say', 'her', 'she',
    'or', 'an', 'will', 'my', 'one', 'all', 'would', 'there', 'their', 'what',
    'flag', 'ctf', 'key', 'password', 'secret', 'hidden', 'code', 'message',
}

CTF_FLAG_PATTERNS = [
    r'flag\{[^}]+\}',
    r'ctf\{[^}]+\}',
    r'[a-z]{2,6}\{[^}]+\}',  # generic flag format
    r'HTB\{[^}]+\}',
    r'picoCTF\{[^}]+\}',
    r'THM\{[^}]+\}',
    r'DUCTF\{[^}]+\}',
]


def score_text(text: str) -> float:
    """
    Returns a confidence score (0.0 - 1.0) for how likely the text is plaintext.
    
    Uses multiple heuristics:
    1. CTF flag pattern matching (instant high score)
    2. Printable character ratio
    3. English letter frequency correlation
    4. Word structure and spacing
    5. Common word detection
    6. Non-printable character penalties
    """
    if not text or len(text) == 0:
        return 0.0

    score = 0.0

    # 1. CTF flag pattern match → instant high score
    for pattern in CTF_FLAG_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return 0.99

    # 2. Printable character ratio (30% weight)
    printable = sum(1 for c in text if c in string.printable)
    printable_ratio = printable / len(text)
    score += printable_ratio * 0.30

    # 3. English letter frequency correlation (30% weight)
    letters = [c.lower() for c in text if c.isalpha()]
    if letters:
        total_letters = len(letters)
        freq_score = 0.0
        for char, expected_freq in ENGLISH_FREQ.items():
            actual_freq = (letters.count(char) / total_letters) * 100
            # Penalize large deviations from expected frequency
            diff = abs(actual_freq - expected_freq)
            freq_score += max(0, 1 - diff / 15)
        freq_score = freq_score / len(ENGLISH_FREQ)
        score += freq_score * 0.30
    else:
        # No letters at all — might be valid (numbers/symbols) but moderate
        score += 0.05

    # 4. Word structure and spacing (20% weight)
    words = text.split()
    has_spaces = ' ' in text
    
    if len(words) > 1:
        avg_word_len = sum(len(w) for w in words) / len(words)
        if 2 <= avg_word_len <= 10:
            score += 0.18
        else:
            score += 0.05
    elif len(words) == 1 and len(text) >= 3:
        # Single word with no spaces
        # Check if it looks like encoding (has padding =, oronly hex chars, etc.)
        if '=' in text:  # Base64 padding
            score += 0.02
        elif re.fullmatch(r'[0-9a-fA-F]+', text) and len(text) % 2 == 0:  # Hex string
            score += 0.03
        elif re.fullmatch(r'[01]+', text):  # Binary string
            score += 0.02
        else:
            score += 0.10  # Regular single word
    
    # Penalty for no spaces in long mixed-case alphanumeric strings (likely encoded like Base64)
    if len(text) > 12 and not has_spaces:
        # Check if it's alphanumeric mix (typical of Base64)
        has_upper = any(c.isupper() for c in text)
        has_lower = any(c.islower() for c in text)
        has_digit = any(c.isdigit() for c in text)
        
        # Mixed case + digits = likely Base64
        if has_upper and has_lower and has_digit:
            score -= 0.15
        # All hex chars = likely hex encoding, mild penalty
        elif re.fullmatch(r'[0-9a-fA-F]+', text):
            score -= 0.05

    # 5. Common word detection (15% weight)
    lower_words = [w.lower().strip(string.punctuation) for w in words]
    common_found = sum(1 for w in lower_words if w in COMMON_WORDS)
    if lower_words:
        common_ratio = common_found / len(lower_words)
        score += common_ratio * 0.15

    # 6. Penalty for high ratio of non-printable or control chars (up to -0.3)
    non_printable = len(text) - printable
    if non_printable > 0:
        penalty = (non_printable / len(text)) * 0.30
        score -= penalty

    # 7. Bonus for reasonable text length and structure
    if 5 <= len(text) <= 10000:
        score += 0.05

    return max(0.0, min(1.0, score))


def is_likely_encoded(text: str) -> bool:
    """Heuristic: returns True if the text still looks encoded (not human-readable)."""
    return score_text(text) < 0.45
