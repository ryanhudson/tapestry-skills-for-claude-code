"""Tests for VTT to text conversion."""

import pytest
from tapestry.vtt_to_text import vtt_to_text


class TestBasicConversion:
    """Test basic VTT to text conversion."""

    def test_removes_webvtt_header(self):
        vtt = "WEBVTT\n\nHello world"
        result = vtt_to_text(vtt)
        assert "WEBVTT" not in result
        assert "Hello world" in result

    def test_removes_timestamps(self):
        vtt = """WEBVTT

00:00:00.000 --> 00:00:05.000
Hello world"""
        result = vtt_to_text(vtt)
        assert "-->" not in result
        assert "00:00" not in result
        assert "Hello world" in result

    def test_removes_kind_metadata(self):
        vtt = """WEBVTT
Kind: captions

Hello world"""
        result = vtt_to_text(vtt)
        assert "Kind:" not in result

    def test_removes_language_metadata(self):
        vtt = """WEBVTT
Language: en

Hello world"""
        result = vtt_to_text(vtt)
        assert "Language:" not in result


class TestHTMLTagRemoval:
    """Test removal of HTML/VTT tags."""

    def test_removes_c_tags(self):
        vtt = """WEBVTT

00:00:00.000 --> 00:00:05.000
<c>Hello</c> world"""
        result = vtt_to_text(vtt)
        assert "<c>" not in result
        assert "</c>" not in result
        assert "Hello" in result

    def test_removes_b_tags(self):
        vtt = """WEBVTT

00:00:00.000 --> 00:00:05.000
<b>Bold text</b>"""
        result = vtt_to_text(vtt)
        assert "<b>" not in result
        assert "Bold text" in result

    def test_removes_i_tags(self):
        vtt = """WEBVTT

00:00:00.000 --> 00:00:05.000
<i>Italic text</i>"""
        result = vtt_to_text(vtt)
        assert "<i>" not in result
        assert "Italic text" in result


class TestHTMLEntityDecoding:
    """Test HTML entity decoding."""

    def test_decodes_ampersand(self):
        vtt = """WEBVTT

00:00:00.000 --> 00:00:05.000
Tom &amp; Jerry"""
        result = vtt_to_text(vtt)
        assert "&amp;" not in result
        assert "Tom & Jerry" in result

    def test_decodes_greater_than(self):
        vtt = """WEBVTT

00:00:00.000 --> 00:00:05.000
5 &gt; 3"""
        result = vtt_to_text(vtt)
        assert "&gt;" not in result
        assert "5 > 3" in result

    def test_decodes_less_than(self):
        vtt = """WEBVTT

00:00:00.000 --> 00:00:05.000
3 &lt; 5"""
        result = vtt_to_text(vtt)
        assert "&lt;" not in result
        assert "3 < 5" in result


class TestDeduplication:
    """Test deduplication of progressive captions."""

    def test_removes_duplicate_lines(self):
        vtt = """WEBVTT

00:00:00.000 --> 00:00:03.000
Hello

00:00:02.000 --> 00:00:05.000
Hello world

00:00:04.000 --> 00:00:07.000
Hello world today"""
        result = vtt_to_text(vtt)
        lines = result.strip().split("\n")
        # Each unique line should appear only once
        assert len(lines) == len(set(lines))

    def test_preserves_order(self):
        vtt = """WEBVTT

00:00:00.000 --> 00:00:03.000
First line

00:00:02.000 --> 00:00:05.000
Second line

00:00:04.000 --> 00:00:07.000
Third line"""
        result = vtt_to_text(vtt)
        lines = result.strip().split("\n")
        assert lines[0] == "First line"
        assert lines[1] == "Second line"
        assert lines[2] == "Third line"


class TestEdgeCases:
    """Test edge cases."""

    def test_empty_vtt(self):
        result = vtt_to_text("")
        assert result == ""

    def test_vtt_header_only(self):
        result = vtt_to_text("WEBVTT\nKind: captions\nLanguage: en\n")
        assert result.strip() == ""

    def test_empty_lines_in_content(self):
        vtt = """WEBVTT

00:00:00.000 --> 00:00:03.000
Hello



00:00:02.000 --> 00:00:05.000
World"""
        result = vtt_to_text(vtt)
        assert "Hello" in result
        assert "World" in result

    def test_cue_identifiers_removed(self):
        vtt = """WEBVTT

1
00:00:00.000 --> 00:00:03.000
Hello

2
00:00:02.000 --> 00:00:05.000
World"""
        result = vtt_to_text(vtt)
        lines = result.strip().split("\n")
        # Numeric identifiers should not be in output
        assert "1" not in lines
        assert "2" not in lines


class TestWithFixture:
    """Test with actual fixture file."""

    def test_sample_vtt_conversion(self, sample_vtt_content, expected_vtt_output):
        """Test conversion of sample VTT matches expected output."""
        result = vtt_to_text(sample_vtt_content)
        # Compare line by line (ignore trailing whitespace)
        result_lines = [line.strip() for line in result.strip().split("\n")]
        expected_lines = [line.strip() for line in expected_vtt_output.strip().split("\n")]
        assert result_lines == expected_lines
