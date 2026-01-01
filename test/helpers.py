"""Shared test utilities."""

import subprocess
import sys


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    """Run the assert-no-inline-lint-disables CLI with the given arguments."""
    return subprocess.run(
        [sys.executable, "-m", "assert_no_inline_lint_disables", *args],
        capture_output=True,
        text=True,
        check=False,
    )
