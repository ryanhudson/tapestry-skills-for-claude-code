#!/usr/bin/env python3
"""Convert VTT subtitle files to clean plain text.

Usage:
    tapestry-vtt-to-text <vtt_file> [--output=<file>]

Handles YouTube auto-generated captions which have duplicate lines
due to progressive caption display. Removes timestamps, VTT metadata,
HTML tags, and deduplicates content.
"""

import argparse
import html
import re
import sys
from pathlib import Path


def vtt_to_text(vtt_content: str) -> str:
    """Convert VTT subtitle content to clean plain text.

    Operations:
    1. Remove VTT header and metadata
    2. Remove timestamp lines
    3. Remove HTML tags (speaker labels, styling)
    4. Decode HTML entities
    5. Deduplicate lines (YouTube progressive captions)
    6. Join into flowing text

    Args:
        vtt_content: Raw VTT file content

    Returns:
        Clean plain text transcript
    """
    seen_lines: set[str] = set()
    output_lines: list[str] = []

    for line in vtt_content.splitlines():
        line = line.strip()

        # Skip empty lines
        if not line:
            continue

        # Skip VTT header
        if line.startswith("WEBVTT"):
            continue

        # Skip metadata (Kind:, Language:, NOTE, etc.)
        if line.startswith(("Kind:", "Language:", "NOTE", "STYLE", "REGION")):
            continue

        # Skip cue identifiers (numeric or UUID-style)
        if re.match(r"^[\da-f-]+$", line, re.IGNORECASE):
            continue

        # Skip timestamp lines (00:00:00.000 --> 00:00:05.000)
        if "-->" in line:
            continue

        # Remove HTML/VTT tags (speaker labels, styling)
        clean = re.sub(r"<[^>]*>", "", line)

        # Remove VTT positioning tags like <c> </c>
        clean = re.sub(r"</?c[^>]*>", "", clean)

        # Decode HTML entities
        clean = html.unescape(clean)

        # Strip again after processing
        clean = clean.strip()

        # Skip if empty after cleaning
        if not clean:
            continue

        # Deduplicate (YouTube shows progressive captions)
        if clean not in seen_lines:
            seen_lines.add(clean)
            output_lines.append(clean)

    return "\n".join(output_lines)


def main() -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Convert VTT subtitle file to clean plain text"
    )
    parser.add_argument("vtt_file", help="Path to VTT file")
    parser.add_argument(
        "--output", "-o",
        help="Output file (default: stdout)"
    )

    args = parser.parse_args()

    vtt_path = Path(args.vtt_file)

    if not vtt_path.exists():
        print(f"Error: File not found: {vtt_path}", file=sys.stderr)
        return 1

    try:
        # Try UTF-8 first, fall back to latin-1
        try:
            content = vtt_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            content = vtt_path.read_text(encoding="latin-1")

        result = vtt_to_text(content)

        if args.output:
            Path(args.output).write_text(result, encoding="utf-8")
            word_count = len(result.split())
            print(f"Converted: {vtt_path.name} -> {args.output} ({word_count} words)")
        else:
            print(result)

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
