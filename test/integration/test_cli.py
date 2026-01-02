"""Integration tests for the CLI module."""

import json
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
        exit_code = run_main_with_args(["--linters", "pylint,mypy", str(test_file)])
        assert exit_code == 0

    def test_exit_1_with_findings(self, tmp_path: Path) -> None:
        """Exit code 1 when findings exist."""
        test_file = tmp_path / "dirty.py"
        test_file.write_text("x = 1  # type: ignore\n")
        exit_code = run_main_with_args(["--linters", "mypy", str(test_file)])
        assert exit_code == 1

    def test_exit_2_file_not_found(self) -> None:
        """Exit code 2 when file does not exist."""
        exit_code = run_main_with_args([
            "--linters", "pylint",
            "/nonexistent/path/file.py",
        ])
        assert exit_code == 2

    def test_exit_2_invalid_linter(self, tmp_path: Path) -> None:
        """Exit code 2 when linter is invalid."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = 1\n")
        exit_code = run_main_with_args(["--linters", "eslint", str(test_file)])
        assert exit_code == 2

    def test_exit_1_overrides_exit_2(self, tmp_path: Path) -> None:
        """If findings exist, exit 1 even if some files have errors."""
        good_file = tmp_path / "good.py"
        good_file.write_text("x = 1\n")
        dirty_file = tmp_path / "dirty.py"
        dirty_file.write_text("x = 1  # type: ignore\n")
        exit_code = run_main_with_args([
            "--linters", "mypy",
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
        """Output format is path:line:linter:directive."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = 1  # type: ignore\n")
        run_main_with_args(["--linters", "mypy", str(test_file)])
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
        run_main_with_args(["--linters", "pylint,mypy", str(test_file)])
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
        run_main_with_args(["--linters", "pylint,mypy", str(test_file)])
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
        exit_code = run_main_with_args([
            "--linters", "pylint,mypy",
            str(file1),
            str(file2),
        ])
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
        run_main_with_args(["--linters", "pylint,mypy", str(file1), str(file2)])
        captured = capsys.readouterr()
        lines = captured.out.strip().split("\n")
        assert len(lines) == 2
        assert "a.py" in lines[0]
        assert "b.py" in lines[1]


@pytest.mark.integration
class TestCliLinterFiltering:
    """Tests for --linters flag."""

    def test_single_linter(self, tmp_path: Path, capsys: Any) -> None:
        """Only specified linter is checked."""
        test_file = tmp_path / "test.py"
        test_file.write_text("# pylint: disable=foo\nx = 1  # type: ignore\n")
        exit_code = run_main_with_args(["--linters", "mypy", str(test_file)])
        assert exit_code == 1
        captured = capsys.readouterr()
        assert "mypy" in captured.out
        assert "pylint" not in captured.out

    def test_multiple_linters(self, tmp_path: Path, capsys: Any) -> None:
        """Multiple specified linters are checked."""
        test_file = tmp_path / "test.py"
        test_file.write_text("# pylint: disable=foo\nx = 1  # type: ignore\n")
        run_main_with_args(["--linters", "pylint,mypy", str(test_file)])
        captured = capsys.readouterr()
        assert "pylint" in captured.out
        assert "mypy" in captured.out


@pytest.mark.integration
class TestCliExclude:
    """Tests for --exclude flag."""

    def test_exclude_single_pattern(self, tmp_path: Path) -> None:
        """Excluded files are skipped."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = 1  # type: ignore\n")
        exit_code = run_main_with_args([
            "--linters", "mypy",
            "--exclude", "*.py",
            str(test_file),
        ])
        assert exit_code == 0

    def test_exclude_multiple_patterns(self, tmp_path: Path, capsys: Any) -> None:
        """Multiple exclude patterns work together."""
        file1 = tmp_path / "test.py"
        file2 = tmp_path / "vendor.py"
        file1.write_text("x = 1  # type: ignore\n")
        file2.write_text("y = 2  # type: ignore\n")
        run_main_with_args([
            "--linters", "mypy",
            "--exclude", "*vendor*",
            str(file1),
            str(file2),
        ])
        captured = capsys.readouterr()
        assert "test.py" in captured.out
        assert "vendor.py" not in captured.out


@pytest.mark.integration
class TestCliQuiet:
    """Tests for --quiet flag."""

    def test_quiet_no_output(self, tmp_path: Path, capsys: Any) -> None:
        """Quiet mode produces no output."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = 1  # type: ignore\n")
        exit_code = run_main_with_args([
            "--linters", "mypy",
            "--quiet",
            str(test_file),
        ])
        assert exit_code == 1
        captured = capsys.readouterr()
        assert captured.out == ""

    def test_quiet_still_returns_exit_code(self, tmp_path: Path) -> None:
        """Quiet mode still returns correct exit code."""
        test_file = tmp_path / "clean.py"
        test_file.write_text("x = 1\n")
        exit_code = run_main_with_args([
            "--linters", "mypy",
            "--quiet",
            str(test_file),
        ])
        assert exit_code == 0


@pytest.mark.integration
class TestCliCount:
    """Tests for --count flag."""

    def test_count_output(self, tmp_path: Path, capsys: Any) -> None:
        """Count mode outputs only the count."""
        test_file = tmp_path / "test.py"
        test_file.write_text("# pylint: disable=foo\nx = 1  # type: ignore\n")
        run_main_with_args(["--linters", "pylint,mypy", "--count", str(test_file)])
        captured = capsys.readouterr()
        assert captured.out.strip() == "2"

    def test_count_zero(self, tmp_path: Path, capsys: Any) -> None:
        """Count mode outputs 0 for clean files."""
        test_file = tmp_path / "clean.py"
        test_file.write_text("x = 1\n")
        run_main_with_args(["--linters", "mypy", "--count", str(test_file)])
        captured = capsys.readouterr()
        assert captured.out.strip() == "0"


@pytest.mark.integration
class TestCliJson:
    """Tests for --json flag."""

    def test_json_output(self, tmp_path: Path, capsys: Any) -> None:
        """JSON mode outputs valid JSON."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = 1  # type: ignore\n")
        run_main_with_args(["--linters", "mypy", "--json", str(test_file)])
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert len(data) == 1
        assert data[0]["linter"] == "mypy"
        assert data[0]["line"] == 1

    def test_json_empty_array(self, tmp_path: Path, capsys: Any) -> None:
        """JSON mode outputs empty array for clean files."""
        test_file = tmp_path / "clean.py"
        test_file.write_text("x = 1\n")
        run_main_with_args(["--linters", "mypy", "--json", str(test_file)])
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data == []


@pytest.mark.integration
class TestCliFailFast:
    """Tests for --fail-fast flag."""

    def test_fail_fast_exits_on_first(self, tmp_path: Path, capsys: Any) -> None:
        """Fail-fast exits on first finding."""
        test_file = tmp_path / "test.py"
        test_file.write_text("# pylint: disable=foo\nx = 1  # type: ignore\n")
        exit_code = run_main_with_args([
            "--linters", "pylint,mypy",
            "--fail-fast",
            str(test_file),
        ])
        assert exit_code == 1
        captured = capsys.readouterr()
        lines = captured.out.strip().split("\n")
        assert len(lines) == 1


@pytest.mark.integration
class TestCliWarnOnly:
    """Tests for --warn-only flag."""

    def test_warn_only_exits_0(self, tmp_path: Path) -> None:
        """Warn-only always exits 0."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = 1  # type: ignore\n")
        exit_code = run_main_with_args([
            "--linters", "mypy",
            "--warn-only",
            str(test_file),
        ])
        assert exit_code == 0

    def test_warn_only_still_outputs(self, tmp_path: Path, capsys: Any) -> None:
        """Warn-only still outputs findings."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = 1  # type: ignore\n")
        run_main_with_args(["--linters", "mypy", "--warn-only", str(test_file)])
        captured = capsys.readouterr()
        assert "mypy" in captured.out


@pytest.mark.integration
class TestCliAllow:
    """Tests for --allow flag."""

    def test_allow_skips_matching(self, tmp_path: Path) -> None:
        """Allowed patterns are skipped."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = 1  # type: ignore[import]\n")
        exit_code = run_main_with_args([
            "--linters", "mypy",
            "--allow", "type: ignore[import]",
            str(test_file),
        ])
        assert exit_code == 0

    def test_allow_multiple_patterns(self, tmp_path: Path, capsys: Any) -> None:
        """Multiple allow patterns work together."""
        test_file = tmp_path / "test.py"
        test_file.write_text(
            "# pylint: disable=too-many-arguments\n"
            "x = 1  # type: ignore[import]\n"
            "y = 2  # type: ignore\n"
        )
        run_main_with_args([
            "--linters", "pylint,mypy",
            "--allow", "type: ignore[import]",
            "--allow", "too-many-arguments",
            str(test_file),
        ])
        captured = capsys.readouterr()
        lines = captured.out.strip().split("\n")
        assert len(lines) == 1
        assert "type: ignore" in lines[0]
        assert "[import]" not in lines[0]
