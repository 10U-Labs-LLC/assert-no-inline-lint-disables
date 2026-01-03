"""Unit tests for the cli module.

These tests use mocking to isolate CLI logic from scanner implementation,
following TDD principles where tests can be written before implementation.
"""

import sys
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from assert_no_inline_lint_disables.cli import main
from assert_no_inline_lint_disables.scanner import Finding


def run_main_with_args(args: list[str]) -> int:
    """Run main() with given args and return exit code."""
    with patch.object(sys, "argv", ["test"] + args):
        try:
            main()
            return 0  # main() always calls sys.exit(), so this is unreachable
        except SystemExit as e:
            return e.code if isinstance(e.code, int) else 1


def create_mock_finding(path: str, line: int, linter: str, directive: str) -> Finding:
    """Create a Finding object for testing."""
    return Finding(path=path, line_number=line, linter=linter, directive=directive)


@pytest.mark.unit
class TestMainFunction:
    """Tests for the main function argument handling."""

    def test_no_files_exits_2(self) -> None:
        """No files argument exits 2 (argparse error)."""
        exit_code = run_main_with_args(["--linters", "pylint"])
        assert exit_code == 2

    def test_no_linters_exits_2(self, tmp_path: Path) -> None:
        """No linters argument exits 2 (argparse error)."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = 1\n")
        exit_code = run_main_with_args([str(test_file)])
        assert exit_code == 2


@pytest.mark.unit
class TestMainWithMockedScanner:
    """Tests for main function with mocked scanner."""

    def test_clean_file_exits_0(self, tmp_path: Path) -> None:
        """Clean file (no findings) exits 0."""
        test_file = tmp_path / "clean.py"
        test_file.write_text("x = 1\n")
        with patch("assert_no_inline_lint_disables.cli.scan_file") as mock_scan:
            mock_scan.return_value = []
            exit_code = run_main_with_args(["--linters", "pylint", str(test_file)])
        assert exit_code == 0
        mock_scan.assert_called_once()

    def test_file_with_finding_exits_1(self, tmp_path: Path) -> None:
        """File with finding exits 1."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = 1\n")
        finding = create_mock_finding(str(test_file), 1, "pylint", "pylint: disable")
        with patch("assert_no_inline_lint_disables.cli.scan_file") as mock_scan:
            mock_scan.return_value = [finding]
            exit_code = run_main_with_args(["--linters", "pylint", str(test_file)])
        assert exit_code == 1

    def test_missing_file_exits_2(self) -> None:
        """Missing file exits 2."""
        exit_code = run_main_with_args(
            ["--linters", "pylint", "/nonexistent/file.py"]
        )
        assert exit_code == 2

    def test_invalid_linter_exits_2(self, tmp_path: Path) -> None:
        """Invalid linter exits 2."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = 1\n")
        exit_code = run_main_with_args(["--linters", "invalid", str(test_file)])
        assert exit_code == 2

    def test_commas_only_linters_exits_2(self, tmp_path: Path) -> None:
        """Linters with only commas exits 2."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = 1\n")
        exit_code = run_main_with_args(["--linters", ",,,", str(test_file)])
        assert exit_code == 2


@pytest.mark.unit
class TestOutputFormats:
    """Tests for output format options."""

    def test_quiet_suppresses_output(
        self,
        tmp_path: Path,
        capsys: Any,
    ) -> None:
        """Quiet flag suppresses output."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = 1\n")
        finding = create_mock_finding(str(test_file), 1, "pylint", "pylint: disable")
        with patch("assert_no_inline_lint_disables.cli.scan_file") as mock_scan:
            mock_scan.return_value = [finding]
            run_main_with_args(["--linters", "pylint", "--quiet", str(test_file)])
        captured = capsys.readouterr()
        assert captured.out == ""

    def test_count_output(self, tmp_path: Path, capsys: Any) -> None:
        """Count flag outputs count."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = 1\n")
        findings = [
            create_mock_finding(str(test_file), 1, "pylint", "pylint: disable"),
            create_mock_finding(str(test_file), 2, "pylint", "pylint: disable"),
        ]
        with patch("assert_no_inline_lint_disables.cli.scan_file") as mock_scan:
            mock_scan.return_value = findings
            run_main_with_args(["--linters", "pylint", "--count", str(test_file)])
        captured = capsys.readouterr()
        assert "2" in captured.out


@pytest.mark.unit
class TestFlags:
    """Tests for various flags."""

    def test_fail_fast_exits_on_first(self, tmp_path: Path, capsys: Any) -> None:
        """Fail-fast exits on first finding."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = 1\n")
        findings = [
            create_mock_finding(str(test_file), 1, "pylint", "pylint: disable"),
            create_mock_finding(str(test_file), 2, "pylint", "pylint: disable"),
        ]
        with patch("assert_no_inline_lint_disables.cli.scan_file") as mock_scan:
            mock_scan.return_value = findings
            run_main_with_args(
                ["--linters", "pylint", "--fail-fast", str(test_file)]
            )
        captured = capsys.readouterr()
        lines = [line for line in captured.out.strip().split("\n") if line]
        assert len(lines) == 1

    def test_warn_only_exits_0(self, tmp_path: Path) -> None:
        """Warn-only always exits 0."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = 1\n")
        finding = create_mock_finding(str(test_file), 1, "pylint", "pylint: disable")
        with patch("assert_no_inline_lint_disables.cli.scan_file") as mock_scan:
            mock_scan.return_value = [finding]
            exit_code = run_main_with_args(
                ["--linters", "pylint", "--warn-only", str(test_file)]
            )
        assert exit_code == 0

    def test_allow_passes_to_scan_file(self, tmp_path: Path) -> None:
        """Allow flag is passed to scan_file."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = 1\n")
        with patch("assert_no_inline_lint_disables.cli.scan_file") as mock_scan:
            mock_scan.return_value = []
            run_main_with_args([
                "--linters", "pylint",
                "--allow", "too-many-args",
                str(test_file),
            ])
        # Verify allow patterns were passed
        call_args = mock_scan.call_args
        assert call_args is not None
        assert "too-many-args" in call_args[0][3]  # allow_patterns is 4th arg

    def test_exclude_skips_matching_files(self, tmp_path: Path) -> None:
        """Exclude flag skips matching files."""
        test_file = tmp_path / "test_generated.py"
        test_file.write_text("x = 1\n")
        with patch("assert_no_inline_lint_disables.cli.scan_file") as mock_scan:
            exit_code = run_main_with_args([
                "--linters", "pylint",
                "--exclude", "*_generated.py",
                str(test_file),
            ])
        assert exit_code == 0
        mock_scan.assert_not_called()  # File was excluded, never scanned


@pytest.mark.unit
class TestDirectoryAndExtensionHandling:
    """Tests for directory and extension handling."""

    def test_scans_directories_recursively(self, tmp_path: Path) -> None:
        """Directories are scanned recursively."""
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        py_file = subdir / "test.py"
        py_file.write_text("x = 1\n")
        finding = create_mock_finding(str(py_file), 1, "pylint", "pylint: disable")
        with patch("assert_no_inline_lint_disables.cli.scan_file") as mock_scan:
            mock_scan.return_value = [finding]
            exit_code = run_main_with_args(["--linters", "pylint", str(subdir)])
        assert exit_code == 1
        mock_scan.assert_called_once()

    def test_skips_irrelevant_extensions(self, tmp_path: Path) -> None:
        """Irrelevant extensions are skipped."""
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("content\n")
        with patch("assert_no_inline_lint_disables.cli.scan_file") as mock_scan:
            exit_code = run_main_with_args(["--linters", "pylint", str(txt_file)])
        assert exit_code == 0
        mock_scan.assert_not_called()  # .txt not scanned for pylint

    def test_scans_relevant_extensions(self, tmp_path: Path) -> None:
        """Relevant extensions are scanned."""
        py_file = tmp_path / "test.py"
        py_file.write_text("x = 1\n")
        finding = create_mock_finding(str(py_file), 1, "pylint", "pylint: disable")
        with patch("assert_no_inline_lint_disables.cli.scan_file") as mock_scan:
            mock_scan.return_value = [finding]
            exit_code = run_main_with_args(["--linters", "pylint", str(py_file)])
        assert exit_code == 1
        mock_scan.assert_called_once()


@pytest.mark.unit
class TestVerboseFlag:
    """Tests for the --verbose flag."""

    def test_verbose_shows_linters(self, tmp_path: Path, capsys: Any) -> None:
        """Verbose shows linters being checked."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = 1\n")
        with patch("assert_no_inline_lint_disables.cli.scan_file") as mock_scan:
            mock_scan.return_value = []
            run_main_with_args(
                ["--linters", "pylint,mypy", "--verbose", str(test_file)]
            )
        captured = capsys.readouterr()
        assert "Checking for: mypy, pylint" in captured.out

    def test_verbose_shows_scanning(self, tmp_path: Path, capsys: Any) -> None:
        """Verbose shows files being scanned."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = 1\n")
        with patch("assert_no_inline_lint_disables.cli.scan_file") as mock_scan:
            mock_scan.return_value = []
            run_main_with_args(["--linters", "pylint", "--verbose", str(test_file)])
        captured = capsys.readouterr()
        assert f"Scanning: {test_file}" in captured.out

    def test_verbose_silently_skips_directory(
        self, tmp_path: Path, capsys: Any
    ) -> None:
        """Verbose does not show skipped directories (scans recursively instead)."""
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        with patch("assert_no_inline_lint_disables.cli.scan_file") as mock_scan:
            mock_scan.return_value = []
            run_main_with_args(["--linters", "pylint", "--verbose", str(subdir)])
        captured = capsys.readouterr()
        assert "Skipping" not in captured.out

    def test_verbose_silently_skips_extension(
        self, tmp_path: Path, capsys: Any
    ) -> None:
        """Verbose silently skips irrelevant extensions."""
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("content\n")
        with patch("assert_no_inline_lint_disables.cli.scan_file") as mock_scan:
            mock_scan.return_value = []
            run_main_with_args(["--linters", "pylint", "--verbose", str(txt_file)])
        captured = capsys.readouterr()
        assert "Skipping" not in captured.out

    def test_verbose_silently_skips_excluded(
        self, tmp_path: Path, capsys: Any
    ) -> None:
        """Verbose silently skips excluded files."""
        test_file = tmp_path / "generated.py"
        test_file.write_text("x = 1\n")
        with patch("assert_no_inline_lint_disables.cli.scan_file") as mock_scan:
            mock_scan.return_value = []
            run_main_with_args([
                "--linters", "pylint",
                "--verbose",
                "--exclude", "*generated.py",
                str(test_file),
            ])
        captured = capsys.readouterr()
        assert "Skipping" not in captured.out

    def test_verbose_shows_findings(self, tmp_path: Path, capsys: Any) -> None:
        """Verbose shows findings inline."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = 1\n")
        finding = create_mock_finding(str(test_file), 1, "pylint", "pylint: disable")
        with patch("assert_no_inline_lint_disables.cli.scan_file") as mock_scan:
            mock_scan.return_value = [finding]
            run_main_with_args(["--linters", "pylint", "--verbose", str(test_file)])
        captured = capsys.readouterr()
        assert "pylint: disable" in captured.out

    def test_verbose_shows_summary(self, tmp_path: Path, capsys: Any) -> None:
        """Verbose shows summary at end."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = 1\n")
        finding = create_mock_finding(str(test_file), 1, "pylint", "pylint: disable")
        with patch("assert_no_inline_lint_disables.cli.scan_file") as mock_scan:
            mock_scan.return_value = [finding]
            run_main_with_args(["--linters", "pylint", "--verbose", str(test_file)])
        captured = capsys.readouterr()
        assert "Scanned 1 file(s), found 1 finding(s)" in captured.out

    def test_verbose_short_flag(self, tmp_path: Path, capsys: Any) -> None:
        """Short -v flag works."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = 1\n")
        with patch("assert_no_inline_lint_disables.cli.scan_file") as mock_scan:
            mock_scan.return_value = []
            run_main_with_args(["--linters", "pylint", "-v", str(test_file)])
        captured = capsys.readouterr()
        assert "Checking for: pylint" in captured.out

    def test_verbose_mutually_exclusive_with_quiet(self, tmp_path: Path) -> None:
        """Verbose and quiet are mutually exclusive."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = 1\n")
        exit_code = run_main_with_args([
            "--linters", "pylint", "--verbose", "--quiet", str(test_file)
        ])
        assert exit_code == 2

    def test_verbose_mutually_exclusive_with_count(self, tmp_path: Path) -> None:
        """Verbose and count are mutually exclusive."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = 1\n")
        exit_code = run_main_with_args([
            "--linters", "pylint", "--verbose", "--count", str(test_file)
        ])
        assert exit_code == 2

    def test_verbose_with_fail_fast(self, tmp_path: Path, capsys: Any) -> None:
        """Verbose with fail-fast shows finding and summary."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = 1\n")
        findings = [
            create_mock_finding(str(test_file), 1, "pylint", "pylint: disable"),
            create_mock_finding(str(test_file), 2, "pylint", "pylint: disable"),
        ]
        with patch("assert_no_inline_lint_disables.cli.scan_file") as mock_scan:
            mock_scan.return_value = findings
            run_main_with_args([
                "--linters", "pylint", "--verbose", "--fail-fast", str(test_file)
            ])
        captured = capsys.readouterr()
        assert "pylint: disable" in captured.out
        assert "found 1 finding" in captured.out


@pytest.mark.unit
class TestErrorHandling:
    """Tests for error handling paths."""

    def test_unreadable_file_exits_2(
        self, tmp_path: Path, capsys: Any
    ) -> None:
        """Unreadable file causes exit code 2."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = 1\n")
        test_file.chmod(0o000)
        try:
            exit_code = run_main_with_args([
                "--linters", "pylint", str(test_file)
            ])
            assert exit_code == 2
            captured = capsys.readouterr()
            assert "Error reading" in captured.err
        finally:
            test_file.chmod(0o644)

    def test_unreadable_file_continues_scanning(
        self, tmp_path: Path, capsys: Any
    ) -> None:
        """Unreadable file doesn't stop scanning other files."""
        unreadable = tmp_path / "unreadable.py"
        unreadable.write_text("x = 1\n")
        unreadable.chmod(0o000)
        readable = tmp_path / "readable.py"
        readable.write_text("x = 1\n")
        finding = create_mock_finding(str(readable), 1, "pylint", "pylint: disable")
        try:
            with patch("assert_no_inline_lint_disables.cli.scan_file") as mock_scan:
                mock_scan.return_value = [finding]
                exit_code = run_main_with_args([
                    "--linters", "pylint", str(unreadable), str(readable)
                ])
            # Exit 1 because we found a violation (takes precedence over error)
            assert exit_code == 1
            captured = capsys.readouterr()
            assert "Error reading" in captured.err
            assert "pylint: disable" in captured.out
        finally:
            unreadable.chmod(0o644)
