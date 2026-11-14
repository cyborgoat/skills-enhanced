#!/usr/bin/env node
// jsonq - query JSON with a dotted path: echo '{"a":{"b":1}}' | jsonq a.b
const path = process.argv[2];
if (path === '--version') { console.log('1.2.0'); process.exit(0); }
let input = '';
process.stdin.on('data', (d) => (input += d)).on('end', () => {
  const value = path.split('.').reduce((o, k) => (o == null ? o : o[k]), JSON.parse(input));
  console.log(JSON.stringify(value));
});
