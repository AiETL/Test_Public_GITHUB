# stego — LSB Image Steganography

A small, dependency-light toolkit for hiding messages inside images and
recovering them again, with an optional password-based encryption layer.

## What is steganography?

Where cryptography makes a message *unreadable*, steganography makes a
message *unnoticeable* — it hides the very existence of the message by
tucking it inside something ordinary, like a photo. An observer sees only a
normal-looking picture and has no obvious reason to suspect it carries a
hidden payload. Combining the two (encrypt, then hide) gives you both
properties: the message is hard to find, and useless even if found.

## The LSB technique

Each pixel in an RGB image is three bytes — one each for red, green and
blue — and every byte is a value from 0 to 255. Changing the
**least-significant bit** (LSB) of a channel shifts its value by at most 1
(e.g. 200 → 201), a change far too small for the human eye to detect.

This tool walks the image's pixels in order and overwrites the LSB of each
R, G and B value with one bit of the payload. The payload is laid out as:

```
[ 32-bit big-endian length header ][ message bytes ]
```

The decoder reads the LSBs back in the same order: the first 32 bits give
the message length *N*, and the next *N* × 8 bits are the message itself.

The capacity of an image is `width × height × 3` bits. If a message
(including its 32-bit header) does not fit, encoding raises a `ValueError`
reporting the bits needed versus available.

## PNG only

Output is always written as **PNG**. PNG is a *lossless* format, so the
exact pixel values — and therefore the hidden bits — survive being saved and
reopened. Lossy formats such as JPEG recompress the image and would
scramble the LSBs, destroying the payload. Any input format Pillow can read
is accepted (it is converted to RGB), but the carrier you share must be the
PNG this tool produces.

## Install

```bash
pip install -r requirements.txt
```

This installs [Pillow](https://python-pillow.org/) for image handling and
[cryptography](https://cryptography.io/) for the optional password layer.

## Usage

### Command line

Hide a message:

```bash
python -m stego.cli encode input.png "meet me at noon" output.png
```

Recover it:

```bash
python -m stego.cli decode output.png
# -> meet me at noon
```

With a password, the message is encrypted before it is hidden and decrypted
after it is extracted:

```bash
python -m stego.cli encode input.png "meet me at noon" output.png --password hunter2
python -m stego.cli decode output.png --password hunter2
# -> meet me at noon
```

Decoding with the wrong password (or no password) fails cleanly rather than
printing garbage.

### Python API

```python
from stego import encode_text, decode_text, encode_message, decode_message
from stego.crypto import encrypt, decrypt

# Plain text round-trip
encode_text("input.png", "hello", "output.png")
print(decode_text("output.png"))            # "hello"

# Raw bytes
encode_message("input.png", b"\x00\x01\x02", "output.png")
print(decode_message("output.png"))          # b"\x00\x01\x02"

# Encrypt, then hide
token = encrypt(b"secret", "password")
encode_message("input.png", token, "output.png")
recovered = decrypt(decode_message("output.png"), "password")
print(recovered)                             # b"secret"
```

## How the encryption works

When a password is supplied, a 32-byte key is derived from it with
PBKDF2-HMAC-SHA256 over a random 16-byte salt, and the data is sealed with
[Fernet](https://cryptography.io/en/latest/fernet/) (AES-128-CBC with HMAC
authentication). The random salt is prepended to the token so decryption can
rederive the key. Because the token is authenticated, a wrong password is
detected and raises an error instead of returning corrupt data.

## Running the tests

```bash
pip install pytest
python -m pytest tests/ -q
```

The suite covers plain ASCII, Unicode/emoji and near-capacity round-trips,
the over-capacity error, and the full encrypt-hide-extract-decrypt cycle
including wrong-password handling.
