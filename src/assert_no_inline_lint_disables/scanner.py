"""Core scanner logic for detecting inline lint-disable directives."""

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Finding:
    """Represents a single finding of an inline lint-disable directive."""

    path: str
    line_number: int
    tool: str
    directive: str

    def __str__(self) -> str:
        """Format finding as path:line:tool:directive."""
        return f"{self.path}:{self.line_number}:{self.tool}:{self.directive}"


# Patterns for detecting inline lint-disable directives (suppressions only).
# Each pattern uses \\s* to tolerate extra whitespace.
# All patterns are case-insensitive.

YAMLLINT_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"yamllint\s+disable-line", re.IGNORECASE), "yamllint disable-line"),
    (re.compile(r"yamllint\s+disable-file", re.IGNORECASE), "yamllint disable-file"),
    (re.compile(r"yamllint\s+disable(?!-)", re.IGNORECASE), "yamllint disable"),
]

PYLINT_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"pylint:\s*disable-next", re.IGNORECASE), "pylint: disable-next"),
    (re.compile(r"pylint:\s*disable-line", re.IGNORECASE), "pylint: disable-line"),
    (re.compile(r"pylint:\s*skip-file", re.IGNORECASE), "pylint: skip-file"),
    (re.compile(r"pylint:\s*disable(?!-)", re.IGNORECASE), "pylint: disable"),
]

MYPY_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"type:\s*ignore", re.IGNORECASE), "type: ignore"),
    (re.compile(r"mypy:\s*ignore-errors", re.IGNORECASE), "mypy: ignore-errors"),
]

ALL_PATTERNS: list[tuple[str, list[tuple[re.Pattern[str], str]]]] = [
    ("yamllint", YAMLLINT_PATTERNS),
    ("pylint", PYLINT_PATTERNS),
    ("mypy", MYPY_PATTERNS),
]


def scan_line(line: str) -> list[tuple[str, str]]:
    """Scan a single line for inline lint-disable directives.

    Args:
        line: The line of text to scan.

    Returns:
        A list of (tool, directive) tuples for each finding.
    """
    findings: list[tuple[str, str]] = []
    for tool, patterns in ALL_PATTERNS:
        for pattern, directive in patterns:
            if pattern.search(line):
                findings.append((tool, directive))
                break  # Only report one finding per tool per line
    return findings


def scan_file(path: str, content: str) -> list[Finding]:
    """Scan file content for inline lint-disable directives.

    Args:
        path: The file path (used for reporting).
        content: The file content to scan.

    Returns:
        A list of Finding objects for each directive found.
    """
    findings: list[Finding] = []
    for line_number, line in enumerate(content.splitlines(), start=1):
        for tool, directive in scan_line(line):
            findings.append(Finding(
                path=path,
                line_number=line_number,
                tool=tool,
                directive=directive,
            ))
    return findings
