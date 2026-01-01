"""Unit tests for the scanner module."""

import pytest

from assert_no_inline_lint_disables.scanner import Finding, scan_file, scan_line


@pytest.mark.unit
class TestScanLineBasic:
    """Basic tests for the scan_line function."""

    def test_no_directives(self) -> None:
        """Line with no directives returns empty list."""
        assert not scan_line("normal code here")

    def test_empty_line(self) -> None:
        """Empty line returns empty list."""
        assert not scan_line("")


@pytest.mark.unit
class TestScanLineYamllint:
    """Tests for yamllint directive detection."""

    def test_yamllint_disable_line(self) -> None:
        """Detects yamllint disable-line directive."""
        result = scan_line("# yamllint disable-line rule:line-length")
        assert result == [("yamllint", "yamllint disable-line")]

    def test_yamllint_disable(self) -> None:
        """Detects yamllint disable directive."""
        result = scan_line("# yamllint disable rule:line-length")
        assert result == [("yamllint", "yamllint disable")]

    def test_yamllint_disable_file(self) -> None:
        """Detects yamllint disable-file directive."""
        result = scan_line("# yamllint disable-file")
        assert result == [("yamllint", "yamllint disable-file")]

    def test_yamllint_enable_not_detected(self) -> None:
        """Does not detect yamllint enable directive."""
        assert not scan_line("# yamllint enable")

    def test_yamllint_enable_line_not_detected(self) -> None:
        """Does not detect yamllint enable-line directive."""
        assert not scan_line("# yamllint enable-line")


@pytest.mark.unit
class TestScanLinePylint:
    """Tests for pylint directive detection."""

    def test_pylint_disable(self) -> None:
        """Detects pylint: disable directive."""
        result = scan_line("# pylint: disable=missing-docstring")
        assert result == [("pylint", "pylint: disable")]

    def test_pylint_disable_next(self) -> None:
        """Detects pylint: disable-next directive."""
        result = scan_line("# pylint: disable-next=line-too-long")
        assert result == [("pylint", "pylint: disable-next")]

    def test_pylint_disable_line(self) -> None:
        """Detects pylint: disable-line directive."""
        result = scan_line("# pylint: disable-line=invalid-name")
        assert result == [("pylint", "pylint: disable-line")]

    def test_pylint_skip_file(self) -> None:
        """Detects pylint: skip-file directive."""
        result = scan_line("# pylint: skip-file")
        assert result == [("pylint", "pylint: skip-file")]

    def test_pylint_enable_not_detected(self) -> None:
        """Does not detect pylint: enable directive."""
        assert not scan_line("# pylint: enable=missing-docstring")

    def test_pylint_enable_next_not_detected(self) -> None:
        """Does not detect pylint: enable-next directive."""
        assert not scan_line("# pylint: enable-next=line-too-long")


@pytest.mark.unit
class TestScanLineMypy:
    """Tests for mypy directive detection."""

    def test_mypy_type_ignore(self) -> None:
        """Detects type: ignore directive."""
        result = scan_line("x = foo()  # type: ignore")
        assert result == [("mypy", "type: ignore")]

    def test_mypy_type_ignore_bracketed(self) -> None:
        """Detects type: ignore with bracketed error codes."""
        result = scan_line("x = foo()  # type: ignore[attr-defined]")
        assert result == [("mypy", "type: ignore")]

    def test_mypy_ignore_errors(self) -> None:
        """Detects mypy: ignore-errors directive."""
        result = scan_line("# mypy: ignore-errors")
        assert result == [("mypy", "mypy: ignore-errors")]


@pytest.mark.unit
class TestScanLineCaseInsensitivity:
    """Tests for case-insensitive matching."""

    def test_case_insensitive_yamllint(self) -> None:
        """Yamllint detection is case-insensitive."""
        result = scan_line("# YAMLLINT DISABLE-LINE")
        assert result == [("yamllint", "yamllint disable-line")]

    def test_case_insensitive_pylint(self) -> None:
        """Pylint detection is case-insensitive."""
        result = scan_line("# PYLINT: DISABLE=foo")
        assert result == [("pylint", "pylint: disable")]

    def test_case_insensitive_mypy(self) -> None:
        """Mypy detection is case-insensitive."""
        result = scan_line("x = foo()  # TYPE: IGNORE")
        assert result == [("mypy", "type: ignore")]


@pytest.mark.unit
class TestScanLineWhitespace:
    """Tests for whitespace tolerance."""

    def test_extra_whitespace_pylint(self) -> None:
        """Tolerates extra whitespace in pylint directive."""
        result = scan_line("# pylint:   disable=foo")
        assert result == [("pylint", "pylint: disable")]

    def test_extra_whitespace_mypy(self) -> None:
        """Tolerates extra whitespace in mypy directive."""
        result = scan_line("x = foo()  # type:    ignore")
        assert result == [("mypy", "type: ignore")]

    def test_extra_whitespace_yamllint(self) -> None:
        """Tolerates extra whitespace in yamllint directive."""
        result = scan_line("# yamllint   disable-line")
        assert result == [("yamllint", "yamllint disable-line")]


@pytest.mark.unit
class TestScanLineMultiple:
    """Tests for multiple directives."""

    def test_multiple_directives_same_line(self) -> None:
        """Detects multiple different tool directives on same line."""
        result = scan_line("# pylint: disable=foo  # type: ignore")
        assert len(result) == 2
        assert ("pylint", "pylint: disable") in result
        assert ("mypy", "type: ignore") in result

    def test_multiple_same_tool_directives(self) -> None:
        """Only reports one finding per tool per line."""
        result = scan_line("# pylint: disable=foo pylint: disable-next=bar")
        assert result == [("pylint", "pylint: disable-next")]

    def test_directive_mid_line(self) -> None:
        """Detects directive in middle of line."""
        result = scan_line("code here  # pylint: disable=foo  # more")
        assert result == [("pylint", "pylint: disable")]


@pytest.mark.unit
class TestScanFile:
    """Tests for the scan_file function."""

    def test_empty_file(self) -> None:
        """Empty file returns no findings."""
        assert not scan_file("test.py", "")

    def test_file_with_no_directives(self) -> None:
        """File with no directives returns no findings."""
        content = "def foo():\n    return 42\n"
        assert not scan_file("test.py", content)

    def test_single_finding(self) -> None:
        """File with one directive returns one finding."""
        content = "x = 1  # type: ignore\n"
        findings = scan_file("test.py", content)
        assert len(findings) == 1
        assert findings[0] == Finding(
            path="test.py",
            line_number=1,
            tool="mypy",
            directive="type: ignore",
        )

    def test_multiple_findings_different_lines(self) -> None:
        """File with directives on different lines returns all findings."""
        content = (
            "# pylint: disable=foo\n"
            "x = 1\n"
            "y = 2  # type: ignore\n"
        )
        findings = scan_file("test.py", content)
        assert len(findings) == 2
        assert findings[0].line_number == 1
        assert findings[0].tool == "pylint"
        assert findings[1].line_number == 3
        assert findings[1].tool == "mypy"

    def test_multiple_findings_same_line(self) -> None:
        """File with multiple directives on same line returns all."""
        content = "x = 1  # pylint: disable=foo  # type: ignore\n"
        findings = scan_file("test.py", content)
        assert len(findings) == 2

    def test_finding_str_format(self) -> None:
        """Finding string format is correct."""
        finding = Finding(
            path="src/foo.py",
            line_number=42,
            tool="pylint",
            directive="pylint: disable",
        )
        assert str(finding) == "src/foo.py:42:pylint:pylint: disable"


@pytest.mark.unit
class TestEnableDirectivesNotDetected:
    """Verify that enable directives are NOT detected."""

    def test_yamllint_enable(self) -> None:
        """Yamllint enable is not detected."""
        content = "# yamllint enable\n# yamllint enable-line\n"
        assert not scan_file("test.yaml", content)

    def test_pylint_enable(self) -> None:
        """Pylint enable is not detected."""
        content = "# pylint: enable=foo\n# pylint: enable-next=bar\n"
        assert not scan_file("test.py", content)
