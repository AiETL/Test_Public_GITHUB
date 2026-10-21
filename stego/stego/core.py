"""Least-Significant-Bit (LSB) steganography engine.

The payload layout written into the image is:

    [ 32-bit big-endian length header ][ message bytes ]

Each bit of this payload is stored in the least-significant bit of the
successive R, G and B channel values of the image's pixels, scanning
pixels in the order Pillow yields them (row-major, left-to-right).
"""

from __future__ import annotations

from PIL import Image

# Number of bits used for the length header prefixed to every payload.
_HEADER_BITS = 32
_HEADER_BYTES = _HEADER_BITS // 8


def _bytes_to_bits(data: bytes) -> list[int]:
    """Expand a byte string into a flat list of bits (MSB first per byte)."""
    bits: list[int] = []
    for byte in data:
        for shift in range(7, -1, -1):
            bits.append((byte >> shift) & 1)
    return bits


def _bits_to_bytes(bits: list[int]) -> bytes:
    """Collapse a flat list of bits (MSB first per byte) back into bytes.

    The number of bits must be a multiple of 8.
    """
    if len(bits) % 8 != 0:
        raise ValueError("bit count must be a multiple of 8 to form bytes")
    out = bytearray()
    for i in range(0, len(bits), 8):
        byte = 0
        for bit in bits[i:i + 8]:
            byte = (byte << 1) | (bit & 1)
        out.append(byte)
    return bytes(out)


def encode_message(image_path: str, message_bytes: bytes, output_path: str) -> str:
    """Hide ``message_bytes`` inside the image and save the result as PNG.

    A 32-bit big-endian length header is prepended to the message, then the
    whole payload is written bit by bit into the LSBs of the R, G, B channels.

    Raises:
        ValueError: if the payload does not fit in the image's capacity.

    Returns:
        The ``output_path`` that was written.
    """
    if len(message_bytes) >= (1 << _HEADER_BITS):
        raise ValueError("message too large to encode its length in 32 bits")

    image = Image.open(image_path).convert("RGB")
    width, height = image.size
    capacity_bits = width * height * 3

    header = len(message_bytes).to_bytes(_HEADER_BYTES, "big")
    payload = header + message_bytes
    bits = _bytes_to_bits(payload)

    if len(bits) > capacity_bits:
        raise ValueError(
            "payload does not fit in image: need {} bits but only {} "
            "available ({}x{} RGB)".format(
                len(bits), capacity_bits, width, height
            )
        )

    pixels = list(image.getdata())
    flat = bytearray()
    for pixel in pixels:
        flat.extend(pixel[:3])

    for i, bit in enumerate(bits):
        flat[i] = (flat[i] & 0xFE) | bit

    new_pixels = [
        (flat[i], flat[i + 1], flat[i + 2]) for i in range(0, len(flat), 3)
    ]
    out_image = Image.new("RGB", (width, height))
    out_image.putdata(new_pixels)
    out_image.save(output_path, format="PNG")
    return output_path


def decode_message(image_path: str) -> bytes:
    """Recover the hidden byte payload from an image produced by ``encode_message``.

    Raises:
        ValueError: if the embedded length header is larger than the image
            could actually hold (corrupt or non-stego image).
    """
    image = Image.open(image_path).convert("RGB")
    width, height = image.size
    capacity_bits = width * height * 3

    flat = bytearray()
    for pixel in image.getdata():
        flat.extend(pixel[:3])

    lsb = [channel & 1 for channel in flat]

    header_bits = lsb[:_HEADER_BITS]
    message_len = int.from_bytes(_bits_to_bytes(header_bits), "big")

    total_bits_needed = _HEADER_BITS + message_len * 8
    if total_bits_needed > capacity_bits:
        raise ValueError(
            "declared message length ({} bytes) exceeds image capacity; "
            "image is corrupt or contains no hidden message".format(message_len)
        )

    message_bits = lsb[_HEADER_BITS:total_bits_needed]
    return _bits_to_bytes(message_bits)


def encode_text(image_path: str, text: str, output_path: str) -> str:
    """Convenience wrapper: hide a UTF-8 string inside an image."""
    return encode_message(image_path, text.encode("utf-8"), output_path)


def decode_text(image_path: str) -> str:
    """Convenience wrapper: recover a UTF-8 string from an image."""
    return decode_message(image_path).decode("utf-8")
