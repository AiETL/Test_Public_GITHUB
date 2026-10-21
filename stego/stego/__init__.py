"""LSB steganography toolkit.

Hide and recover arbitrary byte payloads inside the least-significant bits
of a PNG image or WAV audio file, with an optional password-based
encryption layer. The image engine is exposed at the top level; the audio
engine lives in the :mod:`stego.audio` submodule.
"""

from . import audio
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
    "audio",
]

__version__ = "0.2.0"
