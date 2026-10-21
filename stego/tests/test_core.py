"""Round-trip and edge-case tests for the LSB steganography engine."""

import os
import sys

import pytest
from PIL import Image

# Make the project root importable so ``import stego`` works regardless of
# where pytest is invoked from.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from stego.core import (  # noqa: E402
    encode_message,
    decode_message,
    encode_text,
    decode_text,
    _bytes_to_bits,
    _bits_to_bytes,
)
from stego.crypto import encrypt, decrypt, DecryptionError  # noqa: E402


def _make_image(path, width=32, height=32):
    """Create a small deterministic RGB test image."""
    img = Image.new("RGB", (width, height))
    img.putdata(
        [((x * 7) % 256, (y * 11) % 256, (x + y) % 256)
         for y in range(height) for x in range(width)]
    )
    img.save(path, format="PNG")
    return path


def test_bits_roundtrip():
    data = b"\x00\x01\x80\xff\x55"
    assert _bits_to_bytes(_bytes_to_bits(data)) == data


def test_roundtrip_ascii(tmp_path):
    src = _make_image(tmp_path / "src.png")
    out = tmp_path / "out.png"
    encode_text(str(src), "Hello, steganography!", str(out))
    assert decode_text(str(out)) == "Hello, steganography!"


def test_roundtrip_unicode_emoji(tmp_path):
    src = _make_image(tmp_path / "src.png")
    out = tmp_path / "out.png"
    message = "héllo 世界 🙂🎉 café"
    encode_text(str(src), message, str(out))
    assert decode_text(str(out)) == message


def test_roundtrip_empty_message(tmp_path):
    src = _make_image(tmp_path / "src.png")
    out = tmp_path / "out.png"
    encode_message(str(src), b"", str(out))
    assert decode_message(str(out)) == b""


def test_near_capacity_roundtrip(tmp_path):
    # Capacity = w*h*3 bits. Reserve 32 bits for the header, fill the rest
    # with as many whole message bytes as fit.
    width, height = 20, 20
    src = _make_image(tmp_path / "src.png", width, height)
    capacity_bits = width * height * 3
    max_message_bytes = (capacity_bits - 32) // 8
    message = bytes((i % 256) for i in range(max_message_bytes))
    out = tmp_path / "out.png"
    encode_message(str(src), message, str(out))
    assert decode_message(str(out)) == message


def test_over_capacity_raises(tmp_path):
    width, height = 8, 8
    src = _make_image(tmp_path / "src.png", width, height)
    capacity_bits = width * height * 3
    too_many_bytes = (capacity_bits // 8) + 10
    message = b"x" * too_many_bytes
    out = tmp_path / "out.png"
    with pytest.raises(ValueError):
        encode_message(str(src), message, str(out))


def test_crypto_roundtrip():
    data = b"top secret payload"
    token = encrypt(data, "correct horse battery staple")
    assert token != data
    assert decrypt(token, "correct horse battery staple") == data


def test_crypto_wrong_password_fails():
    token = encrypt(b"secret", "right-password")
    with pytest.raises(DecryptionError):
        decrypt(token, "wrong-password")


def test_encrypt_then_hide_then_extract_then_decrypt(tmp_path):
    src = _make_image(tmp_path / "src.png")
    out = tmp_path / "out.png"
    password = "s3kr3t!"
    secret = "classified: the mitochondria is the powerhouse of the cell 🔬"

    token = encrypt(secret.encode("utf-8"), password)
    encode_message(str(src), token, str(out))

    recovered_token = decode_message(str(out))
    plaintext = decrypt(recovered_token, password).decode("utf-8")
    assert plaintext == secret


def test_full_stego_wrong_password_fails(tmp_path):
    src = _make_image(tmp_path / "src.png")
    out = tmp_path / "out.png"
    token = encrypt(b"hidden", "alpha")
    encode_message(str(src), token, str(out))
    recovered = decode_message(str(out))
    with pytest.raises(DecryptionError):
        decrypt(recovered, "beta")
