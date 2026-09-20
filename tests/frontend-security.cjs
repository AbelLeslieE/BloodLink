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
const filterFixtures = [
  {id: 1, patient_name: 'Abel', hospital_name: 'Little Flower', blood_group: 'A+', priority: 'Urgent', status: 'In Progress'},
  {id: 5, patient_name: 'Albert', hospital_name: 'Rajagiri', blood_group: 'AB+', priority: 'Emergency', status: 'In Progress'},
  {id: 7, patient_name: 'Maria', hospital_name: 'City Hospital', blood_group: 'O-', priority: 'Normal', status: 'Fulfilled'},
];
assert.deepEqual(
  Array.from(requests.filterBloodRequests(filterFixtures, {bloodGroup: 'A+'}), request => request.id),
  [1]
);
assert.deepEqual(
  Array.from(requests.filterBloodRequests(filterFixtures, {urgency: 'emergency', status: 'in progress'}), request => request.id),
  [5]
);
assert.deepEqual(
  Array.from(requests.filterBloodRequests(filterFixtures, {query: 'br-0007'}), request => request.id),
  [7]
);
assert.deepEqual(
  Array.from(requests.filterBloodRequests(filterFixtures, {query: 'little flower', bloodGroup: 'A+'}), request => request.id),
  [1]
);
const matches = load('frontend/dashboard_v2/js/find_match.js');
const card = matches.createRequestCard({id: 1, patient: payload, hospital: payload, priority: 'Normal',
  bloodGroup: 'A+', units: 1, district: payload, requiredDate: '2026-09-13'});
assert(!card.includes(payload));
assert(card.includes('&lt;img'));
console.log('Frontend stored-XSS rendering checks passed.');
