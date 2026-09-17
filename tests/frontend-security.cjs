// Exercise real HTML-producing functions without a browser or external network.
const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const payload = '<img src=x onerror="alert(1)">';
function load(file) {
  const source = fs.readFileSync(file, 'utf8')
    .replace(/^import\s+.*?;\s*$/gm, '')
    .replace(/export\s*\{[^}]*\};?/g, '')
    .replace(/export\s+(?=function)/g, '');
  const context = vm.createContext({console, Set, Date, URL, document: {
    getElementById: () => null, querySelector: () => null, addEventListener: () => {},
  }, window: {}, localStorage: {getItem: () => null}, authenticatedFetch: () => {throw Error('Network disabled in rendering test');}});
  vm.runInContext(source, context);
  return context;
}
const requests = load('frontend/dashboard_v2/js/blood-requests.js');
const rows = requests.buildRequestRows([{id: 1, patient_name: payload, blood_group: 'A+', units_required: 1,
  hospital_name: payload, priority: 'Normal', status: 'Pending', required_date: '2026-09-13'}]);
assert(!rows.includes(payload));
assert(rows.includes('&lt;img'));
const matches = load('frontend/dashboard_v2/js/find_match.js');
const card = matches.createRequestCard({id: 1, patient: payload, hospital: payload, priority: 'Normal',
  bloodGroup: 'A+', units: 1, district: payload, requiredDate: '2026-09-13'});
assert(!card.includes(payload));
assert(card.includes('&lt;img'));
console.log('Frontend stored-XSS rendering checks passed.');
