"""End-to-end tests for the CLI tool."""

from pathlib import Path

import pytest

from test.helpers import run_cli


@pytest.mark.e2e
class TestCliExitCodes:
    """E2E tests for CLI exit codes."""

    def test_exit_0_clean_file(self, tmp_path: Path) -> None:
        """Exit code 0 for a clean file."""
        test_file = tmp_path / "clean.py"
        test_file.write_text("def foo():\n    return 42\n")
        result = run_cli(str(test_file))
        assert result.returncode == 0
        assert result.stdout == ""

    def test_exit_1_with_pylint_disable(self, tmp_path: Path) -> None:
        """Exit code 1 for file with pylint: disable."""
        test_file = tmp_path / "test.py"
        test_file.write_text("# pylint: disable=missing-docstring\nx = 1\n")
        result = run_cli(str(test_file))
        assert result.returncode == 1
        assert "pylint" in result.stdout

    def test_exit_1_with_mypy_ignore(self, tmp_path: Path) -> None:
        """Exit code 1 for file with type: ignore."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = foo()  # type: ignore\n")
        result = run_cli(str(test_file))
        assert result.returncode == 1
        assert "mypy" in result.stdout

    def test_exit_1_with_yamllint_disable(self, tmp_path: Path) -> None:
        """Exit code 1 for file with yamllint disable."""
        test_file = tmp_path / "test.yaml"
        test_file.write_text("key: value  # yamllint disable-line\n")
        result = run_cli(str(test_file))
        assert result.returncode == 1
        assert "yamllint" in result.stdout

    def test_exit_2_missing_file(self) -> None:
        """Exit code 2 for missing file."""
        result = run_cli("/nonexistent/path/file.py")
        assert result.returncode == 2


@pytest.mark.e2e
class TestOutputFormat:
    """E2E tests for output format."""

    def test_output_format_path_line_tool_directive(
        self,
        tmp_path: Path,
    ) -> None:
        """Output format is path:line:tool:directive."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = foo()  # type: ignore\n")
        result = run_cli(str(test_file))
        assert result.returncode == 1
        expected = f"{test_file}:1:mypy:type: ignore\n"
        assert result.stdout == expected

    def test_line_number_is_1_based(self, tmp_path: Path) -> None:
        """Line numbers are 1-based."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = 1\ny = 2\nz = foo()  # type: ignore\n")
        result = run_cli(str(test_file))
        assert ":3:" in result.stdout


@pytest.mark.e2e
class TestAllDirectiveTypes:
    """E2E tests verifying all directive types are detected."""

    def test_yamllint_disable(self, tmp_path: Path) -> None:
        """Detects yamllint disable."""
        test_file = tmp_path / "test.yaml"
        test_file.write_text("# yamllint disable\nkey: value\n")
        result = run_cli(str(test_file))
        assert result.returncode == 1
        assert "yamllint:yamllint disable" in result.stdout

    def test_yamllint_disable_line(self, tmp_path: Path) -> None:
        """Detects yamllint disable-line."""
        test_file = tmp_path / "test.yaml"
        test_file.write_text("key: value  # yamllint disable-line\n")
        result = run_cli(str(test_file))
        assert result.returncode == 1
        assert "yamllint:yamllint disable-line" in result.stdout

    def test_yamllint_disable_file(self, tmp_path: Path) -> None:
        """Detects yamllint disable-file."""
        test_file = tmp_path / "test.yaml"
        test_file.write_text("# yamllint disable-file\nkey: value\n")
        result = run_cli(str(test_file))
        assert result.returncode == 1
        assert "yamllint:yamllint disable-file" in result.stdout

    def test_pylint_disable(self, tmp_path: Path) -> None:
        """Detects pylint: disable."""
        test_file = tmp_path / "test.py"
        test_file.write_text("# pylint: disable=foo\n")
        result = run_cli(str(test_file))
        assert result.returncode == 1
        assert "pylint:pylint: disable" in result.stdout

    def test_pylint_disable_next(self, tmp_path: Path) -> None:
        """Detects pylint: disable-next."""
        test_file = tmp_path / "test.py"
        test_file.write_text("# pylint: disable-next=foo\nx = 1\n")
        result = run_cli(str(test_file))
        assert result.returncode == 1
        assert "pylint:pylint: disable-next" in result.stdout

    def test_pylint_disable_line(self, tmp_path: Path) -> None:
        """Detects pylint: disable-line."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = 1  # pylint: disable-line=foo\n")
        result = run_cli(str(test_file))
        assert result.returncode == 1
        assert "pylint:pylint: disable-line" in result.stdout

    def test_pylint_skip_file(self, tmp_path: Path) -> None:
        """Detects pylint: skip-file."""
        test_file = tmp_path / "test.py"
        test_file.write_text("# pylint: skip-file\nx = 1\n")
        result = run_cli(str(test_file))
        assert result.returncode == 1
        assert "pylint:pylint: skip-file" in result.stdout

    def test_mypy_type_ignore(self, tmp_path: Path) -> None:
        """Detects type: ignore."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = foo()  # type: ignore\n")
        result = run_cli(str(test_file))
        assert result.returncode == 1
        assert "mypy:type: ignore" in result.stdout

    def test_mypy_type_ignore_bracketed(self, tmp_path: Path) -> None:
        """Detects type: ignore[error-code]."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = foo()  # type: ignore[attr-defined]\n")
        result = run_cli(str(test_file))
        assert result.returncode == 1
        assert "mypy:type: ignore" in result.stdout

    def test_mypy_ignore_errors(self, tmp_path: Path) -> None:
        """Detects mypy: ignore-errors."""
        test_file = tmp_path / "test.py"
        test_file.write_text("# mypy: ignore-errors\nx = 1\n")
        result = run_cli(str(test_file))
        assert result.returncode == 1
        assert "mypy:mypy: ignore-errors" in result.stdout


@pytest.mark.e2e
class TestEnableDirectivesNotDetected:
    """E2E tests verifying enable directives are NOT detected."""

    def test_yamllint_enable_not_detected(self, tmp_path: Path) -> None:
        """Yamllint enable is not detected."""
        test_file = tmp_path / "test.yaml"
        test_file.write_text("# yamllint enable\nkey: value\n")
        result = run_cli(str(test_file))
        assert result.returncode == 0
        assert result.stdout == ""

    def test_yamllint_enable_line_not_detected(self, tmp_path: Path) -> None:
        """Yamllint enable-line is not detected."""
        test_file = tmp_path / "test.yaml"
        test_file.write_text("key: value  # yamllint enable-line\n")
        result = run_cli(str(test_file))
        assert result.returncode == 0

    def test_pylint_enable_not_detected(self, tmp_path: Path) -> None:
        """Pylint enable is not detected."""
        test_file = tmp_path / "test.py"
        test_file.write_text("# pylint: enable=foo\n")
        result = run_cli(str(test_file))
        assert result.returncode == 0
        assert result.stdout == ""

    def test_pylint_enable_next_not_detected(self, tmp_path: Path) -> None:
        """Pylint enable-next is not detected."""
        test_file = tmp_path / "test.py"
        test_file.write_text("# pylint: enable-next=foo\n")
        result = run_cli(str(test_file))
        assert result.returncode == 0


@pytest.mark.e2e
class TestCaseInsensitivity:
    """E2E tests for case-insensitive matching."""

    def test_uppercase_pylint(self, tmp_path: Path) -> None:
        """Detects uppercase PYLINT: DISABLE."""
        test_file = tmp_path / "test.py"
        test_file.write_text("# PYLINT: DISABLE=foo\n")
        result = run_cli(str(test_file))
        assert result.returncode == 1

    def test_uppercase_mypy(self, tmp_path: Path) -> None:
        """Detects uppercase TYPE: IGNORE."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = foo()  # TYPE: IGNORE\n")
        result = run_cli(str(test_file))
        assert result.returncode == 1

    def test_mixed_case_yamllint(self, tmp_path: Path) -> None:
        """Detects mixed case YamlLint Disable."""
        test_file = tmp_path / "test.yaml"
        test_file.write_text("# YamlLint Disable\nkey: value\n")
        result = run_cli(str(test_file))
        assert result.returncode == 1


@pytest.mark.e2e
class TestWhitespaceTolerance:
    """E2E tests for whitespace tolerance."""

    def test_extra_whitespace_pylint(self, tmp_path: Path) -> None:
        """Tolerates extra whitespace in pylint directive."""
        test_file = tmp_path / "test.py"
        test_file.write_text("# pylint:    disable=foo\n")
        result = run_cli(str(test_file))
        assert result.returncode == 1

    def test_extra_whitespace_mypy(self, tmp_path: Path) -> None:
        """Tolerates extra whitespace in mypy directive."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = foo()  # type:    ignore\n")
        result = run_cli(str(test_file))
        assert result.returncode == 1

    def test_extra_whitespace_yamllint(self, tmp_path: Path) -> None:
        """Tolerates extra whitespace in yamllint directive."""
        test_file = tmp_path / "test.yaml"
        test_file.write_text("# yamllint    disable\nkey: value\n")
        result = run_cli(str(test_file))
        assert result.returncode == 1


@pytest.mark.e2e
class TestMultipleFindings:
    """E2E tests for multiple findings."""

    def test_multiple_findings_single_file(self, tmp_path: Path) -> None:
        """Multiple findings in single file are all reported."""
        test_file = tmp_path / "test.py"
        test_file.write_text(
            "# pylint: disable=foo\n"
            "x = bar()  # type: ignore\n"
            "# pylint: skip-file\n"
        )
        result = run_cli(str(test_file))
        assert result.returncode == 1
        lines = result.stdout.strip().split("\n")
        assert len(lines) == 3

    def test_multiple_findings_multiple_files(self, tmp_path: Path) -> None:
        """Findings across multiple files are all reported."""
        file1 = tmp_path / "a.py"
        file2 = tmp_path / "b.yaml"
        file1.write_text("x = foo()  # type: ignore\n")
        file2.write_text("# yamllint disable\nkey: value\n")
        result = run_cli(str(file1), str(file2))
        assert result.returncode == 1
        lines = result.stdout.strip().split("\n")
        assert len(lines) == 2
        assert "a.py" in result.stdout
        assert "b.yaml" in result.stdout

    def test_multiple_directives_same_line(self, tmp_path: Path) -> None:
        """Multiple directives on same line are all reported."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = foo()  # pylint: disable=bar  # type: ignore\n")
        result = run_cli(str(test_file))
        assert result.returncode == 1
        lines = result.stdout.strip().split("\n")
        assert len(lines) == 2
        assert "pylint" in result.stdout
        assert "mypy" in result.stdout


@pytest.mark.e2e
class TestRealisticScenarios:
    """E2E tests with realistic file content."""

    def test_python_file_with_mixed_content(self, tmp_path: Path) -> None:
        """Realistic Python file with some suppressions."""
        test_file = tmp_path / "example.py"
        test_file.write_text('''"""Module docstring."""

import os
import sys  # type: ignore[import]

# pylint: disable=too-many-arguments
def complex_function(a, b, c, d, e, f):
    """Do something complex."""
    result = a + b + c + d + e + f
    return result  # type: ignore


class MyClass:
    """A class."""

    def method(self):
        """A method."""
        pass  # pylint: disable=unnecessary-pass
''')
        result = run_cli(str(test_file))
        assert result.returncode == 1
        lines = result.stdout.strip().split("\n")
        assert len(lines) == 4

    def test_yaml_file_with_mixed_content(self, tmp_path: Path) -> None:
        """Realistic YAML file with some suppressions."""
        test_file = tmp_path / "config.yaml"
        test_file.write_text('''---
# yamllint disable-file
name: example
settings:
  debug: true
  log_level: info  # yamllint disable-line rule:truthy
  max_connections: 100
''')
        result = run_cli(str(test_file))
        assert result.returncode == 1
        lines = result.stdout.strip().split("\n")
        assert len(lines) == 2

    def test_clean_python_file(self, tmp_path: Path) -> None:
        """Clean Python file without any suppressions."""
        test_file = tmp_path / "clean.py"
        test_file.write_text('''"""Clean module."""

from typing import List


def add_numbers(numbers: List[int]) -> int:
    """Add all numbers in the list."""
    return sum(numbers)


def main() -> None:
    """Main entry point."""
    result = add_numbers([1, 2, 3, 4, 5])
    print(f"Sum: {result}")


if __name__ == "__main__":
    main()
''')
        result = run_cli(str(test_file))
        assert result.returncode == 0
        assert result.stdout == ""
