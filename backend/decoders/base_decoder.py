"""
Base class and contract for all AutoDecodeX decoders.
"""
from abc import ABC, abstractmethod
from typing import Optional


class BaseDecoder(ABC):
    """
    Abstract base decoder interface.

    Subclasses must provide a unique `name` and implement `decode()`.
    """
    name: str = "base"
    category: str = "encoding"
    description: str = ""

    @abstractmethod
    def decode(self, text: str) -> Optional[str]:
        """
        Attempt to decode input text.

        Args:
            text: Input string to decode.

        Returns:
            Decoded string if successful, or None on failure.
        """
        pass

    def clean_input(self, text: str) -> str:
        """Strip surrounding whitespace from input."""
        return text.strip() if text else ""

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name='{self.name}', category='{self.category}')>"

