# ai-ats-latex-resume-builder

## Overview

Streamlit application that ingests resume input (file or raw text), performs optional OCR/vision extraction for scanned content, enriches input with market-trend snippets, generates LaTeX through a selected LLM provider, validates/sanitizes the LaTeX, and compiles a downloadable PDF.

## Tech Stack

- Python (requirements.txt based)

## Repository Structure

- `.coverage`
- `.gitignore`
- `app.py`
- `CHANGELOG.md`
- `CODE_OF_CONDUCT.md`
- `CONTRIBUTING.md`
- `LICENSE`
- `packages.txt`
- `pytest.ini`
- `README.md`
- `requirements.txt`
- `SECURITY.md`
- ... and 4 more entries

## Getting Started

### Prerequisites

- Git
- Runtime dependencies for this project's stack

### Installation

```bash
uv venv
uv pip install -r requirements.txt
```

## Usage

Run the primary app with `uv run app.py`.

## Testing

Run tests with `uv run pytest` from repository root.

## Security

Please review [SECURITY.md](SECURITY.md) for reporting and handling security issues.

## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) and [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) before opening issues or pull requests.

## Changelog

Ongoing changes are tracked in [CHANGELOG.md](CHANGELOG.md).

## License

This project is licensed under the terms described in [LICENSE](LICENSE).
