// Regenerate the example decks: node examples/build.js
const path = require('path');
const { buildDeck } = require('../scripts/build-deck');
const deck = require('./deck.json');
const insight = require('./insight-deck.json');

// One dense slide at each density level, to compare
const probe = {
  type: 'panels', title: 'Same content, three densities', layout: '0|1/2', colFlex: [1.2, 1],
  panels: [
    { kind: 'table', title: 'Services', header: ['Service', 'Owner', 'p95 ms', 'Status'], rows: [['Checkout', 'Payments', '240', 'Healthy'], ['Catalog', 'Discovery', '90', 'Healthy'], ['Inventory', 'Supply', '130', 'At risk'], ['Orders', 'Fulfilment', '310', 'At risk'], ['Shipping', 'Fulfilment', '280', 'Healthy'], ['Pricing', 'Discovery', '160', 'Healthy'], ['Notifications', 'Growth', '75', 'Healthy'], ['Search', 'Discovery', '110', 'Healthy']] },
    { kind: 'bullets', title: 'Findings', items: ['Two services miss their SLO', 'Orders p95 is 24% over budget', 'Inventory depends on a single cache', 'Shipping is within SLO but trending up', 'Search and Catalog have the most headroom'] },
    { kind: 'stats', title: 'Headline', stats: [{ label: 'Uptime', value: '99.97%' }, { label: 'Errors', value: '0.42%' }, { label: 'p95', value: '310 ms' }] },
  ],
};
const densitySpec = { title: 'Density comparison', slides: ['low', 'medium', 'high'].map((d) => ({ ...probe, density: d, subtitle: `density: ${d}` })) };

(async () => {
  for (const [spec, out] of [[deck, 'example.pptx'], [insight, 'insight-report.pptx'], [densitySpec, 'density-demo.pptx']]) {
    console.log('Wrote', await buildDeck(spec, path.join(__dirname, out), { baseDir: __dirname }));
  }
})().catch((e) => { console.error(e.message); process.exit(1); });
