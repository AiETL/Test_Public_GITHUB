"""Round-trip and edge-case tests for the WAV audio LSB steganography engine."""

import os
import sys
import wave

import pytest

# Make the project root importable so ``import stego`` works regardless of
# where pytest is invoked from.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from stego.audio import (  # noqa: E402
    encode_message,
    decode_message,
    encode_text,
    decode_text,
)
from stego.core import _bytes_to_bits, _bits_to_bytes  # noqa: E402
from stego.crypto import encrypt, decrypt, DecryptionError  # noqa: E402


def _make_wav(path, nframes=4000, nchannels=1, sampwidth=2, framerate=8000):
    """Create a small deterministic 16-bit PCM mono WAV test file."""
    frames = bytearray()
    for i in range(nframes * nchannels):
        sample = (i * 37) % 65536
        frames += sample.to_bytes(sampwidth, "little")
    with wave.open(str(path), "wb") as writer:
        writer.setnchannels(nchannels)
        writer.setsampwidth(sampwidth)
        writer.setframerate(framerate)
        writer.writeframes(bytes(frames))
    return path


def test_bits_roundtrip():
    data = b"\x00\x01\x80\xff\x55"
    assert _bits_to_bytes(_bytes_to_bits(data)) == data


def test_roundtrip_ascii(tmp_path):
    src = _make_wav(tmp_path / "src.wav")
    out = tmp_path / "out.wav"
    encode_text(str(src), "Hello, steganography!", str(out))
    assert decode_text(str(out)) == "Hello, steganography!"


def test_roundtrip_unicode_emoji(tmp_path):
    src = _make_wav(tmp_path / "src.wav")
    out = tmp_path / "out.wav"
    message = "héllo 世界 🙂🎉 café"
    encode_text(str(src), message, str(out))
    assert decode_text(str(out)) == message


def test_roundtrip_empty_message(tmp_path):
    src = _make_wav(tmp_path / "src.wav")
    out = tmp_path / "out.wav"
    encode_message(str(src), b"", str(out))
    assert decode_message(str(out)) == b""


def test_near_capacity_roundtrip(tmp_path):
    # Capacity = nframes * nchannels bits. Reserve 32 bits for the header,
    # fill the rest with as many whole message bytes as fit.
    nframes, nchannels = 4000, 1
    src = _make_wav(tmp_path / "src.wav", nframes, nchannels)
    capacity_bits = nframes * nchannels
    max_message_bytes = (capacity_bits - 32) // 8
    message = bytes((i % 256) for i in range(max_message_bytes))
    out = tmp_path / "out.wav"
    encode_message(str(src), message, str(out))
    assert decode_message(str(out)) == message


def test_over_capacity_raises(tmp_path):
    nframes, nchannels = 512, 1
    src = _make_wav(tmp_path / "src.wav", nframes, nchannels)
    capacity_bits = nframes * nchannels
    too_many_bytes = (capacity_bits // 8) + 10
    message = b"x" * too_many_bytes
    out = tmp_path / "out.wav"
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
    src = _make_wav(tmp_path / "src.wav")
    out = tmp_path / "out.wav"
    password = "s3kr3t!"
    secret = "classified: the mitochondria is the powerhouse of the cell 🔬"

    token = encrypt(secret.encode("utf-8"), password)
    encode_message(str(src), token, str(out))

    recovered_token = decode_message(str(out))
    plaintext = decrypt(recovered_token, password).decode("utf-8")
    assert plaintext == secret


def test_full_stego_wrong_password_fails(tmp_path):
    src = _make_wav(tmp_path / "src.wav")
    out = tmp_path / "out.wav"
    token = encrypt(b"hidden", "alpha")
    encode_message(str(src), token, str(out))
    recovered = decode_message(str(out))
    with pytest.raises(DecryptionError):
        decrypt(recovered, "beta")
