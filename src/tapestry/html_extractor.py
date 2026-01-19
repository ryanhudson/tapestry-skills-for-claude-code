#!/usr/bin/env python3
"""Extract main content from HTML pages (fallback extractor).

Usage:
    tapestry-extract-html <url_or_file> [--output=<file>]

This is a fallback extractor for when reader/trafilatura aren't available.
It uses Python's built-in HTMLParser to extract text from semantic elements.
"""

import argparse
import html
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import URLError

# Elements to skip entirely (don't capture any text inside)
# Note: Don't include void elements (input) as they don't have closing tags
# and would cause skip_depth to never decrement
SKIP_ELEMENTS = {
    "script", "style", "nav", "header", "footer", "aside",
    "form", "noscript", "iframe", "svg", "canvas", "template",
}

# Elements that contain main content
CONTENT_ELEMENTS = {
    "p", "article", "main", "section", "div",
    "h1", "h2", "h3", "h4", "h5", "h6",
    "li", "blockquote", "pre", "code",
    "td", "th", "figcaption",
}

# Elements that should add line breaks
BLOCK_ELEMENTS = {
    "p", "div", "article", "section", "main",
    "h1", "h2", "h3", "h4", "h5", "h6",
    "li", "br", "hr", "blockquote", "pre",
    "tr", "table",
}

USER_AGENT = "Mozilla/5.0 (compatible; Tapestry/1.0)"


class ContentExtractor(HTMLParser):
    """HTML parser that extracts main text content."""

    def __init__(self):
        super().__init__()
        self.content: list[str] = []
        self.title: str = ""
        self.skip_depth: int = 0
        self.in_title: bool = False
        self.current_text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()

        # Track skip depth for nested skip elements
        if tag in SKIP_ELEMENTS:
            self.skip_depth += 1
            return

        if tag == "title":
            self.in_title = True
            return

        # Add line break before block elements
        if tag in BLOCK_ELEMENTS and self.current_text:
            self._flush_text()

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()

        if tag in SKIP_ELEMENTS:
            self.skip_depth = max(0, self.skip_depth - 1)
            return

        if tag == "title":
            self.in_title = False
            return

        # Add line break after block elements
        if tag in BLOCK_ELEMENTS:
            self._flush_text()

    def handle_data(self, data: str) -> None:
        if self.skip_depth > 0:
            return

        if self.in_title:
            self.title = data.strip()
            return

        text = data.strip()
        if text:
            self.current_text.append(text)

    def _flush_text(self) -> None:
        """Flush accumulated text as a paragraph."""
        if self.current_text:
            paragraph = " ".join(self.current_text)
            paragraph = re.sub(r"\s+", " ", paragraph).strip()
            if paragraph:
                self.content.append(paragraph)
            self.current_text = []

    def get_content(self) -> str:
        """Get extracted content as text."""
        self._flush_text()  # Flush any remaining text
        return "\n\n".join(self.content)

    def get_title(self) -> str:
        """Get page title."""
        # Clean common suffixes
        title = self.title
        for sep in [" - ", " | ", " – ", " — ", " :: "]:
            if sep in title:
                title = title.split(sep)[0]
        return title.strip()


def extract_from_html(html_content: str) -> tuple[str, str]:
    """Extract title and main content from HTML.

    Args:
        html_content: Raw HTML string

    Returns:
        Tuple of (title, content)
    """
    parser = ContentExtractor()
    parser.feed(html_content)
    return parser.get_title(), parser.get_content()


def fetch_url(url: str, timeout: int = 30) -> str:
    """Fetch HTML content from URL.

    Args:
        url: URL to fetch
        timeout: Request timeout

    Returns:
        HTML content as string
    """
    request = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=timeout) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(charset, errors="replace")


def main() -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Extract main content from HTML (fallback extractor)"
    )
    parser.add_argument(
        "source",
        help="URL or path to HTML file"
    )
    parser.add_argument(
        "--output", "-o",
        help="Output file (default: stdout)"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=30,
        help="Request timeout in seconds (default: 30)"
    )

    args = parser.parse_args()

    try:
        # Determine if source is URL or file
        if args.source.startswith(("http://", "https://")):
            html_content = fetch_url(args.source, timeout=args.timeout)
        else:
            path = Path(args.source)
            if not path.exists():
                print(f"Error: File not found: {path}", file=sys.stderr)
                return 1
            html_content = path.read_text(encoding="utf-8", errors="replace")

        title, content = extract_from_html(html_content)

        if not content:
            print("Warning: No content extracted", file=sys.stderr)

        # Format output
        output_text = f"# {title}\n\n{content}" if title else content

        if args.output:
            Path(args.output).write_text(output_text, encoding="utf-8")
            word_count = len(content.split())
            print(f"Extracted: {title or 'Untitled'} ({word_count} words)")
        else:
            print(output_text)

        return 0

    except URLError as e:
        print(f"Error fetching URL: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
