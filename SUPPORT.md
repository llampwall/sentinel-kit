# Support

## How to file issues and get help

This project uses GitHub issues to track bugs and feature requests. Please search the existing issues before filing new issues to avoid duplicates. For new issues, file your bug or feature request as a new issue.

For help or questions about using this project, please:

- Open a [GitHub issue](https://github.com/github/spec-kit/issues/new) for bug reports, feature requests, or questions about the Spec-Driven Development methodology
- Check the [comprehensive guide](./spec-driven.md) for detailed documentation on the Spec-Driven Development process
- Review the [README](./README.md) and [`docs/quickstart.md`](docs/quickstart.md) for the uv/`sentinel`-centric bootstrap and troubleshooting tips. Make sure to run `uv run sentinel selfcheck` (Windows, Linux, or macOS) before filing environment-specific issues.

## Project Status

**Spec Kit** is under active development and maintained by GitHub staff **AND THE COMMUNITY**. The recommended local workflow is:

1. `uv sync --locked --dev` (installs specify-cli + SentinelKit).
2. `uv run sentinel selfcheck --verbose` (contracts, context, mcp, sentinel pytest gates).
3. `uv run pytest -q` (system/contract regression suites).

We will do our best to respond to support, feature requests, and community questions in a timely manner.

## GitHub Support Policy

Support for this project is limited to the resources listed above.
