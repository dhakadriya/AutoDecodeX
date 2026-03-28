"""
Base class for all decoders.
"""
from abc import ABC, abstractmethod
from typing import Optional


class BaseDecoder(ABC):
    name: str = "base"

    @abstractmethod
    def decode(self, text: str) -> Optional[str]:
        """Attempt to decode text. Returns None on failure."""
        pass
