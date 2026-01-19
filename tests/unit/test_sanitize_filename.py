"""Tests for filename sanitization."""

import pytest
from tapestry.sanitize_filename import sanitize_filename


class TestBasicSanitization:
    """Test basic character replacement."""

    def test_normal_string(self):
        assert sanitize_filename("Hello World") == "Hello World"

    def test_colon_replacement(self):
        assert sanitize_filename("File: Name") == "File- Name"

    def test_slash_replacement(self):
        assert sanitize_filename("Path/To/File") == "Path_To_File"

    def test_backslash_replacement(self):
        assert sanitize_filename("Windows\\Path") == "Windows_Path"

    def test_pipe_replacement(self):
        assert sanitize_filename("Choice|Option") == "Choice-Option"


class TestDangerousCharacterRemoval:
    """Test removal of dangerous characters."""

    def test_angle_brackets(self):
        result = sanitize_filename("File<script>.txt")
        assert "<" not in result
        assert ">" not in result

    def test_question_mark(self):
        result = sanitize_filename("What?.txt")
        assert "?" not in result

    def test_asterisk(self):
        result = sanitize_filename("Star*.txt")
        assert "*" not in result

    def test_quotes(self):
        result = sanitize_filename('File"Name\'Test')
        assert '"' not in result
        assert "'" not in result

    def test_dollar_sign(self):
        result = sanitize_filename("Price$100")
        assert "$" not in result

    def test_backtick(self):
        result = sanitize_filename("Command`ls`")
        assert "`" not in result

    def test_null_byte(self):
        result = sanitize_filename("File\x00Name")
        assert "\x00" not in result


class TestPathTraversalPrevention:
    """Test path traversal sequence removal."""

    def test_dot_dot_slash(self):
        result = sanitize_filename("../../../etc/passwd")
        assert ".." not in result

    def test_dot_dot_backslash(self):
        result = sanitize_filename("..\\..\\windows\\system32")
        assert ".." not in result

    def test_multiple_dots(self):
        result = sanitize_filename("file....name")
        assert "...." not in result


class TestLengthLimits:
    """Test filename length limiting."""

    def test_default_max_length(self):
        long_name = "A" * 150
        result = sanitize_filename(long_name)
        assert len(result) <= 100

    def test_custom_max_length(self):
        long_name = "A" * 100
        result = sanitize_filename(long_name, max_length=50)
        assert len(result) <= 50

    def test_preserves_extension(self):
        long_name = "A" * 150 + ".txt"
        result = sanitize_filename(long_name)
        assert result.endswith(".txt")
        assert len(result) <= 100


class TestEdgeCases:
    """Test edge cases and special inputs."""

    def test_empty_string(self):
        assert sanitize_filename("") == "unnamed"

    def test_whitespace_only(self):
        assert sanitize_filename("   ") == "unnamed"

    def test_dots_only(self):
        assert sanitize_filename("...") == "unnamed"

    def test_leading_trailing_spaces(self):
        result = sanitize_filename("  File Name  ")
        assert not result.startswith(" ")
        assert not result.endswith(" ")

    def test_leading_trailing_dots(self):
        result = sanitize_filename("..File.Name..")
        assert not result.startswith(".")
        assert not result.endswith(".")

    def test_unicode_normalization(self):
        # Should handle unicode properly
        result = sanitize_filename("Caf\u00e9")
        assert "Caf" in result


class TestWindowsReservedNames:
    """Test handling of Windows reserved filenames."""

    def test_con(self):
        result = sanitize_filename("CON")
        assert result != "CON"
        assert result == "_CON"

    def test_prn(self):
        result = sanitize_filename("PRN")
        assert result != "PRN"

    def test_aux(self):
        result = sanitize_filename("AUX")
        assert result != "AUX"

    def test_nul(self):
        result = sanitize_filename("NUL")
        assert result != "NUL"

    def test_com1(self):
        result = sanitize_filename("COM1")
        assert result != "COM1"

    def test_lpt1(self):
        result = sanitize_filename("LPT1")
        assert result != "LPT1"

    def test_reserved_with_extension(self):
        result = sanitize_filename("CON.txt")
        assert not result.startswith("CON.")


class TestCollapsing:
    """Test collapsing of repeated characters."""

    def test_multiple_dashes(self):
        result = sanitize_filename("File---Name")
        assert "---" not in result

    def test_multiple_underscores(self):
        result = sanitize_filename("File___Name")
        assert "___" not in result

    def test_multiple_spaces(self):
        result = sanitize_filename("File   Name")
        assert "   " not in result
