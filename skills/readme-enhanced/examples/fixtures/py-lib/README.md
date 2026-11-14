# textstats

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE) [![CI](https://github.com/acme/py-lib/actions/workflows/ci.yml/badge.svg)](https://github.com/acme/py-lib/actions/workflows/ci.yml) ![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue)

Count words, sentences and reading time in plain text, with no dependencies.

## Features

- Word and sentence counts that handle punctuation and newlines
- Reading-time estimate at a configurable words-per-minute
- Pure Python, one small module, nothing to install but the package itself

## Requirements

- Python 3.9+

## Installation

```bash
git clone https://github.com/acme/py-lib.git
cd py-lib
pip install .
```

## Usage

```python
from textstats import reading_time, sentences, words

text = "Reading is fast. Writing is slow! " * 60

print(words(text))         # 360
print(sentences(text))     # 120
print(reading_time(text))  # 1.8 (minutes at 200 words per minute)
```

Pass `wpm` to change the reading speed: `reading_time(text, wpm=250)`.

## Development

```bash
pip install -e ".[dev]"
pytest
```

## Contributing

Contributions are welcome. Open an [issue](https://github.com/acme/py-lib/issues) to discuss a change, then send a pull request. Run `pytest` before you do.

## License

Released under the [MIT License](LICENSE). © 2026 Acme Labs
