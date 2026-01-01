"""Integration tests for the CLI module."""

from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from assert_no_inline_lint_disables.cli import main


def run_main_with_args(args: list[str]) -> int:
    """Run main() with the given arguments and return the exit code."""
    with patch("sys.argv", ["assert-no-inline-lint-disables", *args]):
        try:
            main()
            return 0
        except SystemExit as e:
            return int(e.code) if e.code is not None else 0


@pytest.mark.integration
class TestCliExitCodes:
    """Tests for CLI exit codes."""

    def test_exit_0_no_findings(self, tmp_path: Path) -> None:
        """Exit code 0 when no findings."""
        test_file = tmp_path / "clean.py"
        test_file.write_text("def foo():\n    return 42\n")
        exit_code = run_main_with_args([str(test_file)])
        assert exit_code == 0

    def test_exit_1_with_findings(self, tmp_path: Path) -> None:
        """Exit code 1 when findings exist."""
        test_file = tmp_path / "dirty.py"
        test_file.write_text("x = 1  # type: ignore\n")
        exit_code = run_main_with_args([str(test_file)])
        assert exit_code == 1

    def test_exit_2_file_not_found(self) -> None:
        """Exit code 2 when file does not exist."""
        exit_code = run_main_with_args(["/nonexistent/path/file.py"])
        assert exit_code == 2

    def test_exit_1_overrides_exit_2(self, tmp_path: Path) -> None:
        """If findings exist, exit 1 even if some files have errors."""
        good_file = tmp_path / "good.py"
        good_file.write_text("x = 1\n")
        dirty_file = tmp_path / "dirty.py"
        dirty_file.write_text("x = 1  # type: ignore\n")
        exit_code = run_main_with_args([
            str(good_file),
            "/nonexistent/file.py",
            str(dirty_file),
        ])
        assert exit_code == 1


@pytest.mark.integration
class TestCliOutput:
    """Tests for CLI output formatting."""

    def test_output_format(
        self,
        tmp_path: Path,
        capsys: Any,
    ) -> None:
        """Output format is path:line:tool:directive."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = 1  # type: ignore\n")
        run_main_with_args([str(test_file)])
        captured = capsys.readouterr()
        assert f"{test_file}:1:mypy:type: ignore" in captured.out

    def test_multiple_findings_output(
        self,
        tmp_path: Path,
        capsys: Any,
    ) -> None:
        """Multiple findings are output on separate lines."""
        test_file = tmp_path / "test.py"
        test_file.write_text(
            "# pylint: disable=foo\n"
            "x = 1  # type: ignore\n"
        )
        run_main_with_args([str(test_file)])
        captured = capsys.readouterr()
        lines = captured.out.strip().split("\n")
        assert len(lines) == 2

    def test_no_output_when_clean(
        self,
        tmp_path: Path,
        capsys: Any,
    ) -> None:
        """No stdout when no findings."""
        test_file = tmp_path / "clean.py"
        test_file.write_text("def foo():\n    return 42\n")
        run_main_with_args([str(test_file)])
        captured = capsys.readouterr()
        assert captured.out == ""


@pytest.mark.integration
class TestCliMultipleFiles:
    """Tests for scanning multiple files."""

    def test_multiple_clean_files(self, tmp_path: Path) -> None:
        """Exit 0 when all files are clean."""
        file1 = tmp_path / "a.py"
        file2 = tmp_path / "b.py"
        file1.write_text("x = 1\n")
        file2.write_text("y = 2\n")
        exit_code = run_main_with_args([str(file1), str(file2)])
        assert exit_code == 0

    def test_findings_across_files(
        self,
        tmp_path: Path,
        capsys: Any,
    ) -> None:
        """Findings from multiple files are all reported."""
        file1 = tmp_path / "a.py"
        file2 = tmp_path / "b.py"
        file1.write_text("x = 1  # type: ignore\n")
        file2.write_text("# pylint: disable=foo\n")
        run_main_with_args([str(file1), str(file2)])
        captured = capsys.readouterr()
        lines = captured.out.strip().split("\n")
        assert len(lines) == 2
        assert "a.py" in lines[0]
        assert "b.py" in lines[1]
