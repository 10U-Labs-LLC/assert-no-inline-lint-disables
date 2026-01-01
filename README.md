# assert-no-inline-lint-disables

A CLI tool to assert that files contain no inline lint-disable directives for
yamllint, pylint, and mypy.

## Installation

```bash
pip install assert-no-inline-lint-disables
```

## Usage

```bash
assert-no-inline-lint-disables FILE [FILE ...]
```

### Exit Codes

- `0`: No inline lint-disable directives found
- `1`: One or more inline lint-disable directives found
- `2`: Usage or runtime error (e.g., file not found)

### Output

When directives are found, each finding is printed to stdout in the format:

```text
<path>:<line-number>:<tool>:<directive>
```

For example:

```text
src/example.py:10:pylint:pylint: disable
src/example.py:15:mypy:type: ignore
config.yaml:5:yamllint:yamllint disable
```

## Detected Directives

### yamllint (suppressions only)

- `yamllint disable-line`
- `yamllint disable`
- `yamllint disable-file`

### pylint (suppressions only)

- `pylint: disable`
- `pylint: disable-next`
- `pylint: disable-line`
- `pylint: skip-file`

### mypy (suppressions only)

- `type: ignore` (including bracketed forms like `type: ignore[attr-defined]`)
- `mypy: ignore-errors`

## Matching Behavior

- Case-insensitive matching
- Tolerates extra whitespace (e.g., `pylint:  disable`, `type:   ignore`)
- Finds matches anywhere in the line
- Does **not** flag "enable" directives (e.g., `yamllint enable`, `pylint: enable`)

## License

Apache 2.0 - see [LICENSE.txt](LICENSE.txt)
