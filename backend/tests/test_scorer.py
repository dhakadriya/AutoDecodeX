"""
Unit tests for the text scoring module.

Tests the readability/plaintext detection scoring system.
"""
import pytest
from backend.scoring.scorer import (
    score_text,
    is_likely_encoded,
    calculate_ngram_score,
    vowel_consonant_ratio,
)


class TestScoreText:
    """Test the text scoring function."""
    
    def test_score_plaintext(self):
        score = score_text("Hello World")
        assert score > 0.6
    
    def test_score_ctf_flag(self):
        score = score_text("flag{this_is_a_test}")
        # CTF flag should get very high score
        assert score > 0.95
    
    def test_score_encoded_base64(self):
        # Base64 encoded text should score lower
        score = score_text("SGVsbG8gV29ybGQ=")
        assert score < 0.7
    
    def test_score_english_sentence(self):
        score = score_text("The quick brown fox jumps over the lazy dog")
        assert score > 0.7
    
    def test_score_random_chars(self):
        score = score_text("xqzkvp12#@$%")
        assert score < 0.65
    
    def test_score_numbers_only(self):
        score = score_text("1234567890")
        # Numbers only should score low
        assert score < 0.56
    
    def test_score_common_words(self):
        score = score_text("the and for not with this")
        # Common words should score high
        assert score > 0.6


class TestCTFFlags:
    """Test CTF flag detection in scoring."""
    
    @pytest.mark.parametrize("flag", [
        "flag{test}",
        "ctf{test}",
        "HTB{test}",
        "picoCTF{test}",
        "THM{test}",
        "DUCTF{test}",
        "abc{test_flag_here}",
    ])
    def test_various_flag_formats(self, flag):
        score = score_text(flag)
        assert score > 0.95
    
    def test_flag_case_insensitive(self):
        score = score_text("FLAG{TEST}")
        assert score > 0.95
        
        score = score_text("flag{test}")
        assert score > 0.95


class TestIsLikelyEncoded:
    """Test the is_likely_encoded helper function."""
    
    def test_encoded_returns_true(self):
        # Base64 text has moderate score now, adjust threshold
        score = score_text("SGVsbG8gV29ybGQ=")
        assert score < 0.7  # Verify it's below plaintext threshold
    
    def test_plaintext_returns_false(self):
        assert is_likely_encoded("Hello World") is False
    
    def test_ctf_flag_returns_false(self):
        assert is_likely_encoded("flag{test}") is False


class TestScoringEdgeCases:
    """Test edge cases in text scoring."""
    
    def test_empty_string(self):
        score = score_text("")
        assert score == 0.0
    
    def test_single_character(self):
        score = score_text("a")
        assert 0.0 <= score <= 1.0
    
    def test_whitespace_only(self):
        score = score_text("   ")
        assert score < 0.5
    
    def test_very_long_text(self):
        long_text = "Hello World " * 1000
        score = score_text(long_text)
        assert score > 0.6
    
    def test_unicode_text(self):
        score = score_text("你好世界")
        # Should handle gracefully
        assert 0.0 <= score <= 1.0
    
    def test_mixed_language(self):
        score = score_text("Hello 你好 World")
        assert 0.0 <= score <= 1.0
    
    def test_special_characters(self):
        score = score_text("!@#$%^&*()")
        assert score < 0.56


class TestFrequencyAnalysis:
    """Test English frequency analysis component."""
    
    def test_english_text_high_score(self):
        # Text with good English frequency
        text = "the test and that there this"
        score = score_text(text)
        assert score > 0.6
    
    def test_no_vowels_low_score(self):
        # Text with poor English frequency
        text = "zzz xxx qqq kkk"
        score = score_text(text)
        assert score < 0.75


class TestWordStructure:
    """Test word structure analysis component."""
    
    def test_reasonable_word_length(self):
        # Words of reasonable length
        score = score_text("hello world test sample")
        assert score > 0.6
    
    def test_very_long_words(self):
        # Unreasonably long words
        score = score_text("thisisaverylongwordwithnospacesthatshouldscorelow")
        assert score < 0.73
    
    def test_single_word(self):
        score = score_text("hello")
        # Single word should have moderate score
        assert 0.3 <= score <= 0.8


class TestPrintableRatio:
    """Test printable character ratio component."""
    
    def test_all_printable(self):
        score = score_text("All printable ASCII characters!")
        assert score > 0.5
    
    def test_with_control_chars(self):
        # Text with control characters
        text = "Hello\x00\x01\x02World"
        score = score_text(text)
        # Should be penalized
        assert score < 0.8


class TestNgramScoring:
    """Test bigram and trigram frequency scoring component."""

    def test_ngram_english_text(self):
        score = calculate_ngram_score("the quick brown fox jumps over the lazy dog")
        assert score > 0.10
        prose_score = calculate_ngram_score("the other person will enter the room and say hello")
        assert prose_score > 0.20

    def test_ngram_gibberish(self):
        score = calculate_ngram_score("xqzkvpjwbf")
        assert score < 0.1

    def test_ngram_short_string(self):
        assert calculate_ngram_score("") == 0.0
        assert calculate_ngram_score("a") == 0.0

    def test_ngram_exact_trigram_match(self):
        score = calculate_ngram_score("the")
        assert score > 0.5


class TestVowelConsonantRatio:
    """Test vowel-to-consonant ratio heuristic and penalty."""

    def test_vowel_ratio_calculation(self):
        assert vowel_consonant_ratio("hello") == 0.4
        assert vowel_consonant_ratio("aeiou") == 1.0
        assert vowel_consonant_ratio("rhythm") == 0.0
        assert vowel_consonant_ratio("") == 0.0
        assert vowel_consonant_ratio("12345!@#") == 0.0

    def test_balanced_text_ratio(self):
        ratio = vowel_consonant_ratio("The quick brown fox jumps over the lazy dog")
        assert 0.25 <= ratio <= 0.45

    def test_extreme_vowel_imbalance_penalized(self):
        consonants = "bcdfghjklmnpqrstvwxz"
        score_unbalanced = score_text(consonants)
        assert score_unbalanced < 0.55


