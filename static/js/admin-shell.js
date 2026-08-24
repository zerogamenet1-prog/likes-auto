(function () {
  var root = document.documentElement;
  var saved = '';
  try { saved = localStorage.getItem('la-dash-theme') || ''; } catch (e) {}
  if (!saved) saved = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  root.setAttribute('data-theme', saved === 'dark' ? 'dark' : 'light');

  window.dashToggleTheme = function () {
    var next = root.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
    root.setAttribute('data-theme', next);
    try { localStorage.setItem('la-dash-theme', next); } catch (e) {}
  };

  window.dashToggleNav = function () {
    document.body.classList.toggle('adm-nav-open');
  };

  window.dashToggleMenu = function (id) {
    document.querySelectorAll('.dash-menu').forEach(function (el) {
      if (el.id !== id) el.classList.remove('open');
    });
    var m = document.getElementById(id);
    if (m) m.classList.toggle('open');
  };

  document.addEventListener('click', function (e) {
    if (!e.target.closest('.dash-drop')) {
      document.querySelectorAll('.dash-menu').forEach(function (el) { el.classList.remove('open'); });
    }
  });

  document.querySelectorAll('.dash-side a').forEach(function (a) {
    a.addEventListener('click', function () {
      document.body.classList.remove('adm-nav-open');
    });
  });

  window.dashSearch = function (el) {
    var q = (el.value || '').toLowerCase();
    document.querySelectorAll('.dash-side a').forEach(function (a) {
      if (a.classList.contains('dash-brand') || a.closest('.dash-side-foot')) return;
      a.style.display = !q || a.textContent.toLowerCase().indexOf(q) >= 0 ? '' : 'none';
    });
  };

  window.admCopy = function (text, btn) {
    var done = function () {
      if (!btn) return;
      var old = btn.getAttribute('data-label') || btn.textContent;
      btn.setAttribute('data-label', old);
      btn.textContent = 'คัดลอกแล้ว';
      setTimeout(function () { btn.textContent = old; }, 1400);
    };
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(done).catch(function () {
        window.prompt('คัดลอกข้อความนี้', text);
      });
    } else {
      window.prompt('คัดลอกข้อความนี้', text);
    }
  };

  window.admFilter = function (el) {
    var q = (el.value || '').toLowerCase();
    var wrap = el.closest('.adm-table-wrap') || document;
    wrap.querySelectorAll('tbody tr').forEach(function (tr) {
      tr.style.display = tr.innerText.toLowerCase().indexOf(q) >= 0 ? '' : 'none';
    });
  };

  document.querySelectorAll('.adm-table').forEach(function (table) {
    var headers = [];
    table.querySelectorAll('thead th').forEach(function (th) {
      headers.push((th.textContent || '').trim());
    });
    table.querySelectorAll('tbody tr').forEach(function (tr) {
      tr.querySelectorAll('td').forEach(function (td, i) {
        var label = headers[i] || '';
        if (!label && i === headers.length - 1) label = 'จัดการ';
        if (label) td.setAttribute('data-label', label);
      });
    });
  });
})();
