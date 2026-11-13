# csv-cleaner

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

A Claude skill that cleans CSV files: it trims whitespace and normalises the layout so the file loads cleanly.

## Installation

```bash
git clone https://github.com/acme/skill.git
cd skill
pip install -r requirements.txt
cp -r ../skill ~/.claude/skills/csv-cleaner
```

## Usage

Ask Claude in plain language, for example "clean up `contacts.csv`", or run the script directly:

```bash
python scripts/clean.py contacts.csv
```

| Script | What it does |
|---|---|
| `scripts/clean.py` | Normalise delimiters and whitespace in a CSV file |

## License

Released under the [MIT License](LICENSE). © 2026 Acme Labs
