"""Tests for HTML content extraction."""

import pytest
from tapestry.html_extractor import extract_from_html, ContentExtractor


class TestContentExtraction:
    """Test main content extraction."""

    def test_extracts_paragraph_text(self):
        html = "<html><body><p>Hello world</p></body></html>"
        title, content = extract_from_html(html)
        assert "Hello world" in content

    def test_extracts_multiple_paragraphs(self):
        html = """<html><body>
            <p>First paragraph</p>
            <p>Second paragraph</p>
        </body></html>"""
        title, content = extract_from_html(html)
        assert "First paragraph" in content
        assert "Second paragraph" in content

    def test_extracts_article_content(self):
        html = """<html><body>
            <article>
                <p>Article content here</p>
            </article>
        </body></html>"""
        title, content = extract_from_html(html)
        assert "Article content here" in content

    def test_extracts_main_content(self):
        html = """<html><body>
            <main>
                <p>Main content here</p>
            </main>
        </body></html>"""
        title, content = extract_from_html(html)
        assert "Main content here" in content


class TestTitleExtraction:
    """Test page title extraction."""

    def test_extracts_title(self):
        html = "<html><head><title>Page Title</title></head><body><p>Content</p></body></html>"
        title, content = extract_from_html(html)
        assert title == "Page Title"

    def test_strips_site_name_dash(self):
        html = "<html><head><title>Article Title - Site Name</title></head><body><p>Content</p></body></html>"
        title, content = extract_from_html(html)
        assert title == "Article Title"

    def test_strips_site_name_pipe(self):
        html = "<html><head><title>Article Title | Site Name</title></head><body><p>Content</p></body></html>"
        title, content = extract_from_html(html)
        assert title == "Article Title"

    def test_no_title(self):
        html = "<html><body><p>Content</p></body></html>"
        title, content = extract_from_html(html)
        assert title == ""


class TestNoiseRemoval:
    """Test removal of non-content elements."""

    def test_skips_script_tags(self):
        html = """<html><body>
            <script>var x = 'malicious code';</script>
            <p>Real content</p>
        </body></html>"""
        title, content = extract_from_html(html)
        assert "malicious" not in content
        assert "Real content" in content

    def test_skips_style_tags(self):
        html = """<html><body>
            <style>body { color: red; }</style>
            <p>Real content</p>
        </body></html>"""
        title, content = extract_from_html(html)
        assert "color" not in content
        assert "Real content" in content

    def test_skips_nav(self):
        html = """<html><body>
            <nav>
                <a href="/">Home</a>
                <a href="/about">About</a>
            </nav>
            <p>Real content</p>
        </body></html>"""
        title, content = extract_from_html(html)
        assert "Home" not in content
        assert "About" not in content
        assert "Real content" in content

    def test_skips_header(self):
        html = """<html><body>
            <header>Site Logo and Menu</header>
            <p>Real content</p>
        </body></html>"""
        title, content = extract_from_html(html)
        assert "Logo" not in content
        assert "Real content" in content

    def test_skips_footer(self):
        html = """<html><body>
            <p>Real content</p>
            <footer>Copyright 2024</footer>
        </body></html>"""
        title, content = extract_from_html(html)
        assert "Copyright" not in content
        assert "Real content" in content

    def test_skips_aside(self):
        html = """<html><body>
            <aside>Related articles sidebar</aside>
            <p>Real content</p>
        </body></html>"""
        title, content = extract_from_html(html)
        assert "Related" not in content
        assert "Real content" in content

    def test_skips_form(self):
        html = """<html><body>
            <form>
                <input type="email" placeholder="Subscribe">
                <button>Submit</button>
            </form>
            <p>Real content</p>
        </body></html>"""
        title, content = extract_from_html(html)
        assert "Subscribe" not in content
        assert "Real content" in content

    def test_skips_noscript(self):
        html = """<html><body>
            <noscript>Please enable JavaScript</noscript>
            <p>Real content</p>
        </body></html>"""
        title, content = extract_from_html(html)
        assert "JavaScript" not in content
        assert "Real content" in content


class TestEdgeCases:
    """Test edge cases."""

    def test_empty_html(self):
        title, content = extract_from_html("")
        assert title == ""
        assert content == ""

    def test_html_no_body(self):
        html = "<html><head><title>Title</title></head></html>"
        title, content = extract_from_html(html)
        assert title == "Title"
        assert content == ""

    def test_nested_tags(self):
        html = """<html><body>
            <article>
                <div>
                    <p>Deeply <strong>nested</strong> content</p>
                </div>
            </article>
        </body></html>"""
        title, content = extract_from_html(html)
        assert "nested" in content

    def test_whitespace_handling(self):
        html = """<html><body>
            <p>   Multiple   spaces   </p>
        </body></html>"""
        title, content = extract_from_html(html)
        # Should normalize whitespace
        assert "Multiple" in content


class TestWithFixture:
    """Test with actual fixture file."""

    def test_sample_html_extraction(self, sample_html_content, expected_html_output):
        """Test extraction of sample HTML produces expected content."""
        title, content = extract_from_html(sample_html_content)

        # Title should be extracted correctly
        assert title == "How to Write Better Code"

        # Main article content should be present
        assert "Writing clean code is essential" in content
        assert "meaningful variable names" in content
        assert "keep functions small" in content
        assert "write tests for your code" in content

        # Navigation and other noise should be absent
        assert "Home" not in content
        assert "Contact" not in content
        assert "Buy our premium" not in content
        assert "Related Articles" not in content
        assert "Copyright" not in content
        assert "Subscribe" not in content
