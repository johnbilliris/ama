#!/usr/bin/env python3
"""
embed_icons.py — Replace file:/// icon URIs with inline base64 data URIs.

Makes .drawio files self-contained and portable for sharing.

Usage:
    python embed_icons.py <input.drawio> [--output output.drawio]

If --output is not specified, the file is modified in place (a .bak backup is created).
"""
import argparse
import base64
import mimetypes
import re
import shutil
import sys
import urllib.parse
from pathlib import Path


def embed_match(match: re.Match) -> str:
    """Replace a file:/// URI with an inline data URI safe for draw.io style strings.

    draw.io parses style strings by splitting on ';', so a bare data URI like
    'data:image/png;base64,...' gets truncated at the first semicolon.  Fix:

    - SVG: use URL-encoded text format ('data:image/svg+xml,<urlencoded>') — base64
      SVG fails because '+' in base64 output can be misinterpreted.
    - All other types: use base64 with the ';' before 'base64' percent-encoded
      as '%3B' so the style parser never sees it as a property separator.
    """
    path_str = match.group(1)
    p = Path(path_str)
    if not p.exists():
        print(f"  Warning: icon not found, skipping: {p}", file=sys.stderr)
        return match.group(0)
    mime = mimetypes.guess_type(str(p))[0] or "image/png"

    if mime == "image/svg+xml":
        # URL-encoded text: avoids base64's '+' and the ';base64' separator entirely
        encoded = urllib.parse.quote(p.read_text(encoding="utf-8"), safe="")
        data_uri = f"data:image/svg+xml,{encoded}"
        print(f"  Embedded: {p.name} ({mime}, {len(encoded)} chars, url-encoded)")
    else:
        # Binary: base64 with ';' percent-encoded so draw.io's style parser is not confused
        b64 = base64.b64encode(p.read_bytes()).decode()
        data_uri = f"data:{mime}%3Bbase64,{b64}"
        print(f"  Embedded: {p.name} ({mime}, {len(b64)} chars, base64)")

    return f"image={data_uri}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Embed file:/// icons as base64 in .drawio files.")
    parser.add_argument("input", type=Path, help="Path to the .drawio file")
    parser.add_argument("--output", type=Path, default=None, help="Output path (default: modify in place)")
    args = parser.parse_args()

    input_path: Path = args.input.resolve()

    if not input_path.exists():
        print(f"Error: file not found: {input_path}", file=sys.stderr)
        return 1

    xml = input_path.read_text(encoding="utf-8")

    # Count file:/// icon references
    refs = re.findall(r"image=file:///(/[^;\"]+)", xml)
    if not refs:
        print("No file:/// icon references found — nothing to embed.")
        return 0

    print(f"Found {len(refs)} icon reference(s) to embed:")

    # Replace all file:/// URIs with base64 data URIs
    result = re.sub(r"image=file:///(/[^;\"]+)", embed_match, xml)

    # Write output
    output_path = args.output.resolve() if args.output else input_path
    if output_path == input_path:
        shutil.copy2(input_path, input_path.with_suffix(".drawio.bak"))
        print(f"Backup saved: {input_path.with_suffix('.drawio.bak')}")

    output_path.write_text(result, encoding="utf-8")
    print(f"Done — icons embedded in {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())