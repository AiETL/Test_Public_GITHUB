"""Least-Significant-Bit (LSB) steganography engine for WAV audio.

The payload layout written into the audio is identical to the image engine:

    [ 32-bit big-endian length header ][ message bytes ]

Each bit of this payload is stored in the least-significant bit of the
least-significant byte of successive PCM samples, scanning samples in the
order the ``wave`` module yields them (frame by frame, channel by channel).
WAV sample data is little-endian, so the least-significant byte of the
sample at index ``i`` lives at byte offset ``i * sampwidth`` in the frame
buffer.
"""

from __future__ import annotations

import wave

from .core import _bytes_to_bits, _bits_to_bytes, _HEADER_BITS, _HEADER_BYTES


def encode_message(audio_path: str, message_bytes: bytes, output_path: str) -> str:
    """Hide ``message_bytes`` inside the WAV audio and save the result.

    A 32-bit big-endian length header is prepended to the message, then the
    whole payload is written bit by bit into the LSBs of the PCM samples.

    Only 8-bit and 16-bit PCM (sample widths 1 or 2) are supported.

    Raises:
        ValueError: if the sample width is unsupported, or if the payload
            does not fit in the audio's capacity.

    Returns:
        The ``output_path`` that was written.
    """
    if len(message_bytes) >= (1 << _HEADER_BITS):
        raise ValueError("message too large to encode its length in 32 bits")

    with wave.open(audio_path, "rb") as reader:
        nchannels = reader.getnchannels()
        sampwidth = reader.getsampwidth()
        framerate = reader.getframerate()
        nframes = reader.getnframes()
        frames = bytearray(reader.readframes(nframes))

    if sampwidth not in (1, 2):
        raise ValueError(
            "unsupported sample width: {} bytes (only 8-bit and 16-bit PCM "
            "are supported)".format(sampwidth)
        )

    capacity_bits = nframes * nchannels

    header = len(message_bytes).to_bytes(_HEADER_BYTES, "big")
    payload = header + message_bytes
    bits = _bytes_to_bits(payload)

    if len(bits) > capacity_bits:
        raise ValueError(
            "payload does not fit in audio: need {} bits but only {} "
            "available ({} frames x {} channels)".format(
                len(bits), capacity_bits, nframes, nchannels
            )
        )

    for i, bit in enumerate(bits):
        index = i * sampwidth
        frames[index] = (frames[index] & 0xFE) | bit

    with wave.open(output_path, "wb") as writer:
        writer.setnchannels(nchannels)
        writer.setsampwidth(sampwidth)
        writer.setframerate(framerate)
        writer.writeframes(bytes(frames))
    return output_path


def decode_message(audio_path: str) -> bytes:
    """Recover the hidden byte payload from audio produced by ``encode_message``.

    Raises:
        ValueError: if the sample width is unsupported, or if the embedded
            length header is larger than the audio could actually hold
            (corrupt or non-stego audio).
    """
    with wave.open(audio_path, "rb") as reader:
        nchannels = reader.getnchannels()
        sampwidth = reader.getsampwidth()
        nframes = reader.getnframes()
        frames = reader.readframes(nframes)

    if sampwidth not in (1, 2):
        raise ValueError(
            "unsupported sample width: {} bytes (only 8-bit and 16-bit PCM "
            "are supported)".format(sampwidth)
        )

    capacity_bits = nframes * nchannels

    lsb = [frames[i * sampwidth] & 1 for i in range(capacity_bits)]

    header_bits = lsb[:_HEADER_BITS]
    message_len = int.from_bytes(_bits_to_bytes(header_bits), "big")

    total_bits_needed = _HEADER_BITS + message_len * 8
    if total_bits_needed > capacity_bits:
        raise ValueError(
            "declared message length ({} bytes) exceeds audio capacity; "
            "audio is corrupt or contains no hidden message".format(message_len)
        )

    message_bits = lsb[_HEADER_BITS:total_bits_needed]
    return _bits_to_bytes(message_bits)


def encode_text(audio_path: str, text: str, output_path: str) -> str:
    """Convenience wrapper: hide a UTF-8 string inside WAV audio."""
    return encode_message(audio_path, text.encode("utf-8"), output_path)


def decode_text(audio_path: str) -> str:
    """Convenience wrapper: recover a UTF-8 string from WAV audio."""
    return decode_message(audio_path).decode("utf-8")
