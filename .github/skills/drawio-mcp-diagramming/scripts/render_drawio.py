#!/usr/bin/env python3
"""
render_drawio.py — Render a .drawio file to PNG using the draw.io desktop CLI.

Usage:
    python render_drawio.py <input.drawio> [--output output.png] [--scale 2] [--border 20]

Requirements:
    - drawio desktop CLI on PATH  (snap install drawio  OR  download AppImage)
    - xvfb-run on PATH for headless Linux (sudo apt install xvfb)

On success: prints absolute path of the output PNG and exits 0.
On failure: prints error to stderr and exits non-zero.
"""
import argparse
import shutil
import subprocess
import sys
from pathlib import Path


def default_output_path(input_path: Path, explicit: Path = None) -> Path:
    """Return the output PNG path — explicit if given, else <stem>.png beside input."""
    if explicit is not None:
        return explicit
    return input_path.with_suffix(".png")


def build_command(input_path: Path, output_path: Path, xvfb_available: bool,
                  scale: float = 2, border: int = 20) -> list[str]:
    """Build the shell command list to invoke draw.io export."""
    drawio_args = [
        "drawio",
        "--export",
        "--format", "png",
        "--scale", str(scale),
        "--border", str(border),
        "--output", str(output_path),
        str(input_path),
    ]
    if xvfb_available:
        return ["xvfb-run", "-a"] + drawio_args
    return drawio_args


def main() -> int:
    parser = argparse.ArgumentParser(description="Render a .drawio file to PNG.")
    parser.add_argument("input", type=Path, help="Path to the .drawio input file")
    parser.add_argument("--output", type=Path, default=None, help="Output PNG path")
    parser.add_argument("--scale", type=float, default=2,
                        help="Export scale factor (default: 2 for crisp rendering)")
    parser.add_argument("--border", type=int, default=20,
                        help="Border padding in pixels (default: 20)")
    args = parser.parse_args()

    input_path: Path = args.input.resolve()

    # Validate input file exists
    if not input_path.exists():
        print(f"Error: input file not found: {input_path}", file=sys.stderr)
        return 1

    # Check drawio binary
    if not shutil.which("drawio"):
        print(
            "Error: 'drawio' not found on PATH.\n"
            "Install options:\n"
            "  snap install drawio\n"
            "  OR download the AppImage from https://github.com/jgraph/drawio-desktop/releases",
            file=sys.stderr,
        )
        return 1

    resolved_output = args.output.resolve() if args.output is not None else None
    output_path = default_output_path(input_path, resolved_output)
    xvfb_available = shutil.which("xvfb-run") is not None

    cmd = build_command(input_path, output_path, xvfb_available,
                        scale=args.scale, border=args.border)

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    except subprocess.TimeoutExpired:
        print("Error: drawio render timed out after 60 seconds.", file=sys.stderr)
        return 1
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    if result.returncode != 0:
        print(f"Error: drawio exited with code {result.returncode}", file=sys.stderr)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        return result.returncode

    print(str(output_path.resolve()))
    return 0


if __name__ == "__main__":
    sys.exit(main())