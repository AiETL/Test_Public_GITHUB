# stego — LSB Image & Audio Steganography

A small, dependency-light toolkit for hiding messages inside images and WAV
audio and recovering them again, with an optional password-based encryption
layer.

## What is steganography?

Where cryptography makes a message *unreadable*, steganography makes a
message *unnoticeable* — it hides the very existence of the message by
tucking it inside something ordinary, like a photo or an audio clip. An
observer sees only a normal-looking picture — or hears only an
ordinary-sounding recording — and has no obvious reason to suspect it
carries a hidden payload. Combining the two (encrypt, then hide) gives you
both
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
Pillow is only needed for the image engine; the audio engine needs no extra
dependencies — it uses the Python standard-library `wave` module (the
password layer still uses `cryptography`).

## Usage

There are two engines: the image commands (`encode`/`decode`, shown below)
and the audio commands (`encode-audio`/`decode-audio`, see the
[Audio (WAV) steganography](#audio-wav-steganography) section).

### Command line (image)

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

### Python API (image)

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

## Audio (WAV) steganography

The same LSB technique works on **WAV** PCM audio. A WAV file is a stream of
integer samples; overwriting the **least-significant bit** of a sample
shifts its amplitude by at most one step, an inaudible change. The audio
engine lives in the `stego.audio` submodule and mirrors the image API, using
only the Python standard library `wave` module (no extra dependencies).

Each payload bit is stored in the LSB of the least-significant byte of each
successive PCM sample (WAV sample data is little-endian). The payload layout
is identical to the image engine:

```
[ 32-bit big-endian length header ][ message bytes ]
```

The capacity of a WAV file is `nframes × nchannels` bits — one bit per
sample. Both 8-bit and 16-bit PCM (sample widths 1 and 2) are supported; any
other sample width raises a `ValueError`, as does a payload that does not
fit. The output WAV preserves the original channels, sample width and frame
rate.

### Why WAV only

LSB hiding requires a **lossless** container so the exact sample values —
and therefore the hidden bits — survive being saved and reopened. **WAV** is
lossless and is the recommended carrier (it is ideal for voice recordings).
**MP3 is lossy**: re-encoding quantises and reshapes the samples and would
destroy the hidden bits. **MIDI** stores event and structural data (notes,
timing, instruments) rather than audio samples, so there are no sample LSBs
to hide in. Both MP3 and MIDI are therefore out of scope for this
sample-LSB approach.

### Command line

```bash
python -m stego.cli encode-audio input.wav "meet me at noon" output.wav
python -m stego.cli decode-audio output.wav
# -> meet me at noon
```

With a password, the message is encrypted before it is hidden and decrypted
after it is extracted:

```bash
python -m stego.cli encode-audio input.wav "meet me at noon" output.wav --password hunter2
python -m stego.cli decode-audio output.wav --password hunter2
# -> meet me at noon
```

### Python API

```python
from stego import audio
from stego.crypto import encrypt, decrypt

# Plain text round-trip
audio.encode_text("input.wav", "hello", "output.wav")
print(audio.decode_text("output.wav"))            # "hello"

# Raw bytes
audio.encode_message("input.wav", b"\x00\x01\x02", "output.wav")
print(audio.decode_message("output.wav"))          # b"\x00\x01\x02"

# Encrypt, then hide
token = encrypt(b"secret", "password")
audio.encode_message("input.wav", token, "output.wav")
recovered = decrypt(audio.decode_message("output.wav"), "password")
print(recovered)                                   # b"secret"
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
