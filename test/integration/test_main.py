"""Integration tests for the __main__ module."""

import importlib
from pathlib import Path
from unittest.mock import patch

import pytest


@pytest.mark.integration
class TestMainModule:
    """Tests for the __main__ module."""

    def test_main_module_calls_main(self, tmp_path: Path) -> None:
        """Importing __main__ calls the main function."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = 1\n")

        with patch("sys.argv", ["prog", str(test_file)]):
            with pytest.raises(SystemExit) as exc_info:
                importlib.import_module("assert_no_inline_lint_disables.__main__")

            assert exc_info.value.code == 0
