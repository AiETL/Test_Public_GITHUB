"""LSB image steganography toolkit.

Hide and recover arbitrary byte payloads inside the least-significant bits
of a PNG image, with an optional password-based encryption layer.
"""

from .core import (
    encode_message,
    decode_message,
    encode_text,
    decode_text,
)
from .crypto import encrypt, decrypt

__all__ = [
    "encode_message",
    "decode_message",
    "encode_text",
    "decode_text",
    "encrypt",
    "decrypt",
]

__version__ = "0.1.0"
