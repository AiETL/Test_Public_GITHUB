"""Command-line interface for the LSB steganography toolkit.

Examples:
    python -m stego.cli encode in.png "secret text" out.png
    python -m stego.cli encode in.png "secret text" out.png --password hunter2
    python -m stego.cli decode out.png
    python -m stego.cli decode out.png --password hunter2
    python -m stego.cli encode-audio in.wav "secret text" out.wav
    python -m stego.cli encode-audio in.wav "secret text" out.wav --password hunter2
    python -m stego.cli decode-audio out.wav
    python -m stego.cli decode-audio out.wav --password hunter2
"""

from __future__ import annotations

import argparse
import sys

from . import audio
from .core import encode_message, decode_message
from .crypto import encrypt, decrypt, DecryptionError


def _cmd_encode(args: argparse.Namespace) -> int:
    data = args.message.encode("utf-8")
    if args.password:
        data = encrypt(data, args.password)
    try:
        encode_message(args.in_image, data, args.out_image)
    except ValueError as exc:
        print("error: {}".format(exc), file=sys.stderr)
        return 1
    print("Encoded message into {}".format(args.out_image))
    return 0


def _cmd_decode(args: argparse.Namespace) -> int:
    try:
        data = decode_message(args.in_image)
    except ValueError as exc:
        print("error: {}".format(exc), file=sys.stderr)
        return 1

    if args.password:
        try:
            data = decrypt(data, args.password)
        except DecryptionError as exc:
            print("error: {}".format(exc), file=sys.stderr)
            return 1

    try:
        print(data.decode("utf-8"))
    except UnicodeDecodeError:
        # Fall back to raw bytes repr if the payload is not UTF-8 text
        # (e.g. encrypted data decoded without the right password).
        sys.stdout.buffer.write(data)
    return 0


def _cmd_encode_audio(args: argparse.Namespace) -> int:
    data = args.message.encode("utf-8")
    if args.password:
        data = encrypt(data, args.password)
    try:
        audio.encode_message(args.in_audio, data, args.out_audio)
    except ValueError as exc:
        print("error: {}".format(exc), file=sys.stderr)
        return 1
    print("Encoded message into {}".format(args.out_audio))
    return 0


def _cmd_decode_audio(args: argparse.Namespace) -> int:
    try:
        data = audio.decode_message(args.in_audio)
    except ValueError as exc:
        print("error: {}".format(exc), file=sys.stderr)
        return 1

    if args.password:
        try:
            data = decrypt(data, args.password)
        except DecryptionError as exc:
            print("error: {}".format(exc), file=sys.stderr)
            return 1

    try:
        print(data.decode("utf-8"))
    except UnicodeDecodeError:
        # Fall back to raw bytes repr if the payload is not UTF-8 text
        # (e.g. encrypted data decoded without the right password).
        sys.stdout.buffer.write(data)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="stego.cli",
        description="Hide and recover messages inside PNG images or WAV audio "
        "using LSB steganography.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    enc = sub.add_parser("encode", help="hide a message inside an image")
    enc.add_argument("in_image", help="path to the source image")
    enc.add_argument("message", help="the message text to hide")
    enc.add_argument("out_image", help="path to write the output PNG")
    enc.add_argument(
        "--password",
        help="encrypt the message with this password before hiding it",
    )
    enc.set_defaults(func=_cmd_encode)

    dec = sub.add_parser("decode", help="recover a message from an image")
    dec.add_argument("in_image", help="path to the stego image")
    dec.add_argument(
        "--password",
        help="decrypt the recovered message with this password",
    )
    dec.set_defaults(func=_cmd_decode)

    enc_audio = sub.add_parser(
        "encode-audio", help="hide a message inside a WAV audio file"
    )
    enc_audio.add_argument("in_audio", help="path to the source WAV audio")
    enc_audio.add_argument("message", help="the message text to hide")
    enc_audio.add_argument("out_audio", help="path to write the output WAV")
    enc_audio.add_argument(
        "--password",
        help="encrypt the message with this password before hiding it",
    )
    enc_audio.set_defaults(func=_cmd_encode_audio)

    dec_audio = sub.add_parser(
        "decode-audio", help="recover a message from a WAV audio file"
    )
    dec_audio.add_argument("in_audio", help="path to the stego WAV audio")
    dec_audio.add_argument(
        "--password",
        help="decrypt the recovered message with this password",
    )
    dec_audio.set_defaults(func=_cmd_decode_audio)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
