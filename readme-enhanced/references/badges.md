# Badges

A badge earns its place if a reader acts on it. Keep the total within the style's limit (3 / 5 / 6), on one line under the title, and make sure each points at this repository (the linter checks the owner/name).

| Badge | When | Snippet |
|---|---|---|
| Licence | always | `[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)` |
| CI status | a GitHub Actions workflow exists | `[![CI](https://github.com/OWNER/REPO/actions/workflows/ci.yml/badge.svg)](https://github.com/OWNER/REPO/actions/workflows/ci.yml)` |
| Runtime version | the manifest declares one | `![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)` |
| npm version | published to npm | `[![npm](https://img.shields.io/npm/v/NAME)](https://www.npmjs.com/package/NAME)` |
| PyPI version | published to PyPI | `[![PyPI](https://img.shields.io/pypi/v/NAME)](https://pypi.org/project/NAME/)` |
| crates.io | published to crates.io | `[![crates.io](https://img.shields.io/crates/v/NAME)](https://crates.io/crates/NAME)` |
| Coverage | a coverage service is wired into CI | use the service's own badge URL |

- Add a registry badge only if the package really is published (`scaffold_readme.py --registry`).
- Skip vanity badges (stars, "made with love", download counters on a young project).
- Static `img.shields.io/badge/...` badges need no service and cannot go stale or break.
