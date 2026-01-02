"""Command-line interface for assert-no-inline-lint-disables."""

import argparse
import fnmatch
import json
import sys

from assert_no_inline_lint_disables.scanner import (
    Finding,
    parse_linters,
    scan_file,
)

EXIT_SUCCESS = 0
EXIT_FINDINGS = 1
EXIT_ERROR = 2


def create_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser."""
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
    parser.add_argument(
        "--linters",
        required=True,
        metavar="LINTERS",
        help="Comma-separated linters to check: yamllint,pylint,mypy",
    )
    parser.add_argument(
        "--exclude",
        action="append",
        default=[],
        metavar="PATTERN",
        help="Glob pattern to exclude files (repeatable).",
    )

    # Output mode group (mutually exclusive)
    output_group = parser.add_mutually_exclusive_group()
    output_group.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress output, exit code only.",
    )
    output_group.add_argument(
        "--count",
        action="store_true",
        help="Print finding count only.",
    )
    output_group.add_argument(
        "--json",
        action="store_true",
        help="Output findings as JSON.",
    )

    # Behavior modifiers (mutually exclusive)
    behavior_group = parser.add_mutually_exclusive_group()
    behavior_group.add_argument(
        "--fail-fast",
        action="store_true",
        help="Exit on first finding.",
    )
    behavior_group.add_argument(
        "--warn-only",
        action="store_true",
        help="Always exit 0, report only.",
    )

    parser.add_argument(
        "--allow",
        action="append",
        default=[],
        metavar="PATTERN",
        help="Allow directive pattern (repeatable).",
    )

    return parser


def output_findings(
    findings: list[Finding],
    use_json: bool,
    use_count: bool,
) -> None:
    """Output findings in the appropriate format."""
    if use_json:
        print(json.dumps([f.to_dict() for f in findings]))
    elif use_count:
        print(len(findings))
    else:
        for finding in findings:
            print(finding)


def main() -> None:
    """Main entry point for the CLI."""
    parser = create_parser()
    args = parser.parse_args()

    # Parse and validate linters
    try:
        linters = parse_linters(args.linters)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(EXIT_ERROR)

    all_findings: list[Finding] = []
    had_error = False

    for path in args.files:
        # Check exclude patterns
        if any(fnmatch.fnmatch(path, pattern) for pattern in args.exclude):
            continue

        try:
            with open(path, encoding="utf-8") as f:
                content = f.read()
        except OSError as e:
            print(f"Error reading {path}: {e}", file=sys.stderr)
            had_error = True
            continue

        findings = scan_file(path, content, linters, args.allow)

        if findings and args.fail_fast:
            if not args.quiet:
                output_findings([findings[0]], args.json, args.count)
            sys.exit(EXIT_FINDINGS)

        all_findings.extend(findings)

    # Handle output
    if not args.quiet:
        output_findings(all_findings, args.json, args.count)

    # Determine exit code
    if args.warn_only:
        sys.exit(EXIT_SUCCESS)

    if all_findings:
        sys.exit(EXIT_FINDINGS)

    if had_error:
        sys.exit(EXIT_ERROR)

    sys.exit(EXIT_SUCCESS)
