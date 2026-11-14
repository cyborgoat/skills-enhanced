# jsonq

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE) ![Node 18+](https://img.shields.io/badge/node-18%2B-green)

Query JSON from the command line with a tiny dotted-path syntax.

## Features

- Reads JSON from stdin and prints the value at a path
- Dotted paths for nested objects, `a.b.c`
- No dependencies; one file

## Requirements

- Node.js 18+

## Installation

```bash
git clone https://github.com/acme/node-cli.git
cd node-cli
npm install
```

## Usage

```bash
echo '{"user":{"name":"Ada","langs":["en","fr"]}}' | node bin/jsonq.js user.langs
```

```text
["en","fr"]
```

Print the version with `node bin/jsonq.js --version`.

## Development

```bash
npm test
npm run lint
```

## Contributing

Contributions are welcome. Open an [issue](https://github.com/acme/node-cli/issues) to discuss a change, then send a pull request. Run `npm test` first.

## License

Released under the [MIT License](LICENSE). © 2026 Acme Labs
