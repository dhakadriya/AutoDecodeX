"""
Scoring module: evaluates how "readable" or "plaintext-like" a string is.
Returns a confidence score between 0.0 and 1.0.
"""
import re
import string

# Common English letter frequencies (approximate)
ENGLISH_FREQ = {
    'e': 12.7, 't': 9.1, 'a': 8.2, 'o': 7.5, 'i': 7.0,
    'n': 6.7, 's': 6.3, 'h': 6.1, 'r': 6.0, 'd': 4.3,
    'l': 4.0, 'c': 2.8, 'u': 2.8, 'm': 2.4, 'w': 2.4,
    'f': 2.2, 'g': 2.0, 'y': 2.0, 'p': 1.9, 'b': 1.5,
    'v': 1.0, 'k': 0.8, 'j': 0.2, 'x': 0.2, 'q': 0.1, 'z': 0.1,
}

CTF_FLAG_PATTERNS = [
    r'flag\{[^}]+\}',
    r'ctf\{[^}]+\}',
    r'[a-z]{2,6}\{[^}]+\}',  # generic flag format
    r'HTB\{[^}]+\}',
    r'picoCTF\{[^}]+\}',
]


def score_text(text: str) -> float:
    """
    Returns a confidence score (0.0 - 1.0) for how likely the text is plaintext.
    """
    if not text or len(text) == 0:
        return 0.0

    score = 0.0

    # 1. CTF flag pattern match → instant high score
    for pattern in CTF_FLAG_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return 0.99

    # 2. Printable character ratio
    printable = sum(1 for c in text if c in string.printable)
    printable_ratio = printable / len(text)
    score += printable_ratio * 0.4

    # 3. English letter frequency correlation
    letters = [c.lower() for c in text if c.isalpha()]
    if letters:
        total_letters = len(letters)
        freq_score = 0.0
        for char, expected_freq in ENGLISH_FREQ.items():
            actual_freq = (letters.count(char) / total_letters) * 100
            # Penalize large deviations from expected frequency
            diff = abs(actual_freq - expected_freq)
            freq_score += max(0, 1 - diff / 10)
        freq_score = freq_score / len(ENGLISH_FREQ)
        score += freq_score * 0.35
    else:
        # No letters at all — lower score unless it's all digits/symbols
        score += 0.05

    # 4. Space and word structure
    words = text.split()
    if len(words) > 1:
        avg_word_len = sum(len(w) for w in words) / len(words)
        if 2 <= avg_word_len <= 10:
            score += 0.15
        else:
            score += 0.05
    else:
        score += 0.05

    # 5. Penalty for high ratio of non-printable or weird chars
    non_printable = len(text) - printable
    if non_printable > 0:
        score -= (non_printable / len(text)) * 0.3

    return max(0.0, min(1.0, score))


def is_likely_encoded(text: str) -> bool:
    """Heuristic: returns True if the text still looks encoded (not human-readable)."""
    return score_text(text) < 0.45
