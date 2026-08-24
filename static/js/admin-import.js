
(function () {
  var form = document.getElementById('import-form');
  if (!form) return;
  var pid = form.getAttribute('data-pid') || '';
  var main = form.getAttribute('data-main') || '';
  var key = 'la_import_' + pid + '_' + main;
  function store() {
    try { return JSON.parse(sessionStorage.getItem(key) || '{}'); }
    catch (e) { return {}; }
  }
  function save(data) { sessionStorage.setItem(key, JSON.stringify(data)); }
  function toThb(rate, cur, usd) {
    cur = String(cur || 'USD').toUpperCase().replace(/\s+/g, '');
    rate = parseFloat(rate) || 0;
    usd = parseFloat(usd) || 35;
    if (cur === 'THB' || cur === 'BAHT') return rate;
    var map = { USD: 1, EUR: 1.08, GBP: 1.27, INR: 0.012, TRY: 0.029, RUB: 0.011, IDR: 0.000063, VND: 0.00004, PHP: 0.017, MYR: 0.22, SGD: 0.74, AUD: 0.65, CAD: 0.73, BRL: 0.18 };
    return rate * (map[cur] || 1) * usd;
  }
  function applyPrices(force) {
    var usd = parseFloat(document.getElementById('usd_rate').value) || 35;
    var pct = parseFloat(document.getElementById('percent').value) || 0;
    var extra = parseFloat(document.getElementById('fixed').value) || 0;
    document.querySelectorAll('#catalog-table tbody tr[data-rate]').forEach(function (tr) {
      var cost = toThb(tr.getAttribute('data-rate'), tr.getAttribute('data-cur'), usd);
      var sell = Math.round((cost * (1 + pct / 100) + extra) * 100) / 100;
      var costEl = tr.querySelector('.js-cost');
      if (costEl) costEl.textContent = cost.toFixed(2);
      var inp = tr.querySelector('.js-sell');
      if (inp && (force || !inp.dataset.touched)) inp.value = sell.toFixed(2);
    });
  }
  function sync() {
    var data = store();
    document.querySelectorAll('.js-pick').forEach(function (cb) {
      var row = cb.closest('tr');
      var price = row ? row.querySelector('.js-sell') : null;
      if (cb.checked && price) data[cb.value] = price.value;
      else delete data[cb.value];
    });
    save(data);
    var n = Object.keys(data).length;
    var el = document.getElementById('pick-count');
    if (el) el.textContent = n ? ('selected ' + n) : 'none';
    var th = document.getElementById('pick-count');
    if (th) th.textContent = n ? ('\u0e40\u0e25\u0e37\u0e2d\u0e01\u0e41\u0e25\u0e49\u0e27 ' + n + ' \u0e23\u0e32\u0e22\u0e01\u0e32\u0e23') : '\u0e22\u0e31\u0e07\u0e44\u0e21\u0e48\u0e44\u0e14\u0e49\u0e40\u0e25\u0e37\u0e2d\u0e01';
  }
  document.querySelectorAll('.js-sell').forEach(function (inp) {
    inp.addEventListener('input', function () { inp.dataset.touched = '1'; sync(); });
  });
  document.querySelectorAll('.js-pick').forEach(function (cb) {
    cb.addEventListener('change', sync);
  });
  var checkPage = document.getElementById('check-page');
  if (checkPage) checkPage.addEventListener('change', function () {
    document.querySelectorAll('.js-pick').forEach(function (x) { x.checked = checkPage.checked; });
    sync();
  });
  var saved = store();
  document.querySelectorAll('.js-pick').forEach(function (cb) {
    if (saved[cb.value] != null) {
      cb.checked = true;
      var inp = cb.closest('tr').querySelector('.js-sell');
      if (inp) { inp.value = saved[cb.value]; inp.dataset.touched = '1'; }
    }
  });
  var recalc = document.getElementById('recalc-btn');
  if (recalc) recalc.addEventListener('click', function () { applyPrices(true); sync(); });
  ['usd_rate', 'percent', 'fixed'].forEach(function (id) {
    var el = document.getElementById(id);
    if (el) el.addEventListener('input', function () { applyPrices(false); });
  });
  var addFiltered = document.getElementById('add-filtered');
  if (addFiltered) addFiltered.addEventListener('click', function (event) {
    if (!confirm('\u0e40\u0e1e\u0e34\u0e48\u0e21\u0e1a\u0e23\u0e34\u0e01\u0e32\u0e23\u0e17\u0e31\u0e49\u0e07\u0e2b\u0e21\u0e14\u0e17\u0e35\u0e48\u0e01\u0e23\u0e2d\u0e07\u0e2d\u0e22\u0e39\u0e48 (\u0e2a\u0e39\u0e07\u0e2a\u0e38\u0e14 1,000 \u0e23\u0e32\u0e22\u0e01\u0e32\u0e23)?')) {
      event.preventDefault();
      return;
    }
    document.getElementById('scope').value = 'filtered';
  });
  var addSelected = document.getElementById('add-selected');
  if (addSelected) addSelected.addEventListener('click', function () {
    document.getElementById('scope').value = 'selected';
  });
  form.addEventListener('submit', function () {
    sync();
    document.getElementById('picks').value = JSON.stringify(store());
  });
  applyPrices(false);
  sync();
})();
