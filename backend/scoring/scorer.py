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

from .constants import (
    ENGLISH_LETTER_FREQ,
    ENGLISH_BIGRAMS,
    ENGLISH_TRIGRAMS,
    COMMON_WORDS,
    CTF_FLAG_PATTERNS,
)

# Backward-compatibility alias
ENGLISH_FREQ = ENGLISH_LETTER_FREQ


def calculate_ngram_score(text: str) -> float:
    """
    Calculates proportion of common English bigrams and trigrams in text.
    Returns a normalized score between 0.0 and 1.0.
    """
    clean = re.sub(r'[^a-z]', '', text.lower())
    if len(clean) < 2:
        return 0.0
    bigrams = [clean[i:i+2] for i in range(len(clean) - 1)]
    bigram_match = sum(1 for bg in bigrams if bg in ENGLISH_BIGRAMS) / len(bigrams) if bigrams else 0.0

    if len(clean) >= 3:
        trigrams = [clean[i:i+3] for i in range(len(clean) - 2)]
        trigram_match = sum(1 for tg in trigrams if tg in ENGLISH_TRIGRAMS) / len(trigrams) if trigrams else 0.0
        return 0.6 * bigram_match + 0.4 * trigram_match
    return bigram_match


def vowel_consonant_ratio(text: str) -> float:
    """
    Returns the vowel ratio (vowels / total letters) for alphabetic characters in text.
    Returns 0.0 if there are no alphabetic characters.
    """
    letters = [c.lower() for c in text if c.isalpha()]
    if not letters:
        return 0.0
    vowels = sum(1 for c in letters if c in 'aeiou')
    return vowels / len(letters)


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
        score += freq_score * 0.25

        # English n-gram frequency bonus (bigrams and trigrams, 5% weight)
        if len(letters) >= 2:
            score += calculate_ngram_score(text) * 0.05
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

    # 5b. Vowel-to-consonant ratio check for natural language balance
    if len(letters) >= 8:
        v_ratio = sum(1 for c in letters if c in 'aeiou') / len(letters)
        if v_ratio < 0.15 or v_ratio > 0.65:
            score -= 0.10

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
