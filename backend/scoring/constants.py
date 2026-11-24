"""
Constants and frequency distributions for natural language and cipher scoring.
"""
from typing import Dict, Set, List

# Single letter relative frequencies in the English language (percentages)
ENGLISH_LETTER_FREQ: Dict[str, float] = {
    'e': 12.70, 't': 9.06, 'a': 8.17, 'o': 7.51, 'i': 6.97,
    'n': 6.75, 's': 6.33, 'h': 6.09, 'r': 5.99, 'd': 4.25,
    'l': 4.03, 'c': 2.78, 'u': 2.76, 'm': 2.41, 'w': 2.36,
    'f': 2.23, 'g': 2.02, 'y': 1.97, 'p': 1.93, 'b': 1.49,
    'v': 0.98, 'k': 0.77, 'j': 0.15, 'x': 0.15, 'q': 0.10, 'z': 0.07,
}

# Top 30 most frequent English bigrams
ENGLISH_BIGRAMS: Set[str] = {
    'th', 'he', 'in', 'er', 'an', 're', 'ed', 'on', 'es', 'st',
    'en', 'at', 'to', 'nt', 'ha', 'nd', 'ou', 'ea', 'ng', 'as',
    'or', 'ti', 'is', 'et', 'it', 'ar', 'te', 'se', 'hi', 'of'
}

# Top 20 most frequent English trigrams
ENGLISH_TRIGRAMS: Set[str] = {
    'the', 'and', 'ing', 'ent', 'ion', 'her', 'for', 'tha', 'nth', 'int',
    'ere', 'tio', 'ter', 'est', 'ers', 'ati', 'hat', 'ate', 'all', 'eth'
}

# Common English and CTF challenge words for plaintext validation
COMMON_WORDS: Set[str] = {
    'the', 'be', 'to', 'of', 'and', 'a', 'in', 'that', 'have', 'i',
    'it', 'for', 'not', 'on', 'with', 'he', 'as', 'you', 'do', 'at',
    'this', 'but', 'his', 'by', 'from', 'they', 'we', 'say', 'her', 'she',
    'or', 'an', 'will', 'my', 'one', 'all', 'would', 'there', 'their', 'what',
    'so', 'up', 'out', 'if', 'about', 'who', 'get', 'which', 'go', 'me',
    'when', 'make', 'can', 'like', 'time', 'no', 'just', 'him', 'know', 'take',
    'people', 'into', 'year', 'your', 'good', 'some', 'could', 'them', 'see', 'other',
    'flag', 'ctf', 'key', 'password', 'secret', 'hidden', 'code', 'message',
    'admin', 'token', 'access', 'congratulations', 'solved', 'winner', 'payload',
}

# Known CTF flag format regular expressions
CTF_FLAG_PATTERNS: List[str] = [
    r'flag\{[^}]+\}',
    r'ctf\{[^}]+\}',
    r'[a-z]{2,6}\{[^}]+\}',  # generic flag format
    r'HTB\{[^}]+\}',
    r'picoCTF\{[^}]+\}',
    r'THM\{[^}]+\}',
    r'DUCTF\{[^}]+\}',
    r'sec\{[^}]+\}',
    r'cyber\{[^}]+\}',
]
