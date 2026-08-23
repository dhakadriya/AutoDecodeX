"""
Pytest configuration and shared fixtures for AutoDecodeX tests.
"""
import pytest
import sys
from pathlib import Path

# Add backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))


@pytest.fixture
def sample_plaintext():
    """Sample plaintext for encoding/decoding tests."""
    return "Hello World"


@pytest.fixture
def sample_ctf_flag():
    """Sample CTF flag for detection tests."""
    return "flag{this_is_a_test_flag}"


@pytest.fixture
def long_plaintext():
    """Longer text for performance and stress testing."""
    return """
    The quick brown fox jumps over the lazy dog.
    This is a longer text sample used for testing the decoder engine.
    It contains multiple sentences and should decode properly.
    """


@pytest.fixture
def edge_case_texts():
    """Edge cases for robust testing."""
    return {
        'empty': '',
        'single_char': 'A',
        'whitespace': '   ',
        'numbers': '12345',
        'special': '!@#$%^&*()',
        'unicode': '你好世界',
        'mixed': 'Test123!@# with spaces',
    }
