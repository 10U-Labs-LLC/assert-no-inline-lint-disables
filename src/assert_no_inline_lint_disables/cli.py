"""Command-line interface for assert-no-inline-lint-disables."""

import argparse
import sys

from assert_no_inline_lint_disables.scanner import Finding, scan_file

EXIT_SUCCESS = 0
EXIT_FINDINGS = 1
EXIT_ERROR = 2


def main() -> None:
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        prog="assert-no-inline-lint-disables",
        description="Assert that files contain no inline lint-disable directives.",
    )
    parser.add_argument(
        "files",
        nargs="+",
        metavar="FILE",
        help="One or more file paths to scan.",
    )

    args = parser.parse_args()

    all_findings: list[Finding] = []
    had_error = False

    for path in args.files:
        try:
            with open(path, encoding="utf-8") as f:
                content = f.read()
        except OSError as e:
            print(f"Error reading {path}: {e}", file=sys.stderr)
            had_error = True
            continue

        findings = scan_file(path, content)
        all_findings.extend(findings)

    if had_error and not all_findings:
        sys.exit(EXIT_ERROR)

    if all_findings:
        for finding in all_findings:
            print(finding)
        sys.exit(EXIT_FINDINGS)

    sys.exit(EXIT_SUCCESS)
