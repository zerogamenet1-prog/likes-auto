(function () {
  var form = document.getElementById("import-form");
  var fetchForm = document.getElementById("imp-fetch-form");
  var fetchBtn = document.getElementById("imp-fetch-btn");
  var syncForm = document.getElementById("imp-sync-form");
  var syncBtn = document.getElementById("imp-sync-btn");

  function setBusy(btn, on) {
    if (!btn) return;
    btn.disabled = !!on;
    btn.classList.toggle("is-loading", !!on);
    var label = btn.querySelector(".imp-fetch-label");
    var busy = btn.querySelector(".imp-fetch-busy");
    if (label) label.hidden = !!on;
    if (busy) busy.hidden = !on;
  }

  if (fetchForm && fetchBtn) {
    fetchForm.addEventListener("submit", function () {
      setBusy(fetchBtn, true);
    });
  }
  if (syncForm && syncBtn) {
    syncForm.addEventListener("submit", function () {
      setBusy(syncBtn, true);
    });
  }

  document.querySelectorAll(".imp-bulk-bar, .imp-main-bulk").forEach(function (f) {
    f.addEventListener("submit", function () {
      Array.prototype.forEach.call(f.querySelectorAll("button[type=submit]"), function (b) {
        b.classList.add("is-loading");
        b.disabled = true;
      });
    });
  });

  if (!form) return;

  var pid = form.getAttribute("data-pid") || "";
  var scopeKey = form.getAttribute("data-scope-key") || "";
  var key = "la_import_" + pid + "_" + scopeKey;

  function store() {
    try {
      return JSON.parse(sessionStorage.getItem(key) || "{}");
    } catch (e) {
      return {};
    }
  }
  function save(data) {
    sessionStorage.setItem(key, JSON.stringify(data));
  }
  function toThb(rate, cur, usd) {
    cur = String(cur || "USD")
      .toUpperCase()
      .replace(/\s+/g, "")
      .replace("฿", "THB");
    rate = parseFloat(rate) || 0;
    usd = parseFloat(usd) || 35;
    if (cur === "THB" || cur === "BAHT" || cur === "BATH") return rate;
    var map = {
      USD: 1,
      US$: 1,
      $: 1,
      EUR: 1.08,
      GBP: 1.27,
      INR: 0.012,
      TRY: 0.029,
      RUB: 0.011,
      IDR: 0.000063,
      VND: 0.00004,
      PHP: 0.017,
      MYR: 0.22,
      SGD: 0.74,
      AUD: 0.65,
      CAD: 0.73,
      BRL: 0.18,
    };
    return rate * (map[cur] || 1) * usd;
  }
  function priceInputs() {
    return {
      usd: document.getElementById("usd_rate") || document.getElementById("bulk_usd"),
      pct: document.getElementById("percent") || document.getElementById("bulk_pct"),
      fix: document.getElementById("fixed") || document.getElementById("bulk_fix"),
    };
  }
  function syncPricePair(fromEl) {
    if (!fromEl) return;
    var map = {
      usd_rate: "bulk_usd",
      bulk_usd: "usd_rate",
      percent: "bulk_pct",
      bulk_pct: "percent",
      fixed: "bulk_fix",
      bulk_fix: "fixed",
    };
    var other = document.getElementById(map[fromEl.id] || "");
    if (other && other !== fromEl && other.value !== fromEl.value) other.value = fromEl.value;
  }
  function applyPrices(force) {
    var p = priceInputs();
    if (!p.usd) return;
    var usd = parseFloat(p.usd.value) || 35;
    var pct = parseFloat(p.pct && p.pct.value) || 0;
    var extra = parseFloat(p.fix && p.fix.value) || 0;
    document.querySelectorAll("#catalog-table tbody tr[data-rate]").forEach(function (tr) {
      var cost = toThb(tr.getAttribute("data-rate"), tr.getAttribute("data-cur"), usd);
      var sell = Math.round((cost * (1 + pct / 100) + extra) * 100) / 100;
      var costEl = tr.querySelector(".js-cost");
      if (costEl) costEl.textContent = cost.toFixed(2);
      var inp = tr.querySelector(".js-sell");
      if (inp && (force || !inp.dataset.touched)) inp.value = sell.toFixed(2);
    });
  }
  function paintCount(n) {
    var text = n ? "เลือกแล้ว " + n + " รายการ" : "ยังไม่ได้เลือก";
    var a = document.getElementById("pick-count");
    var b = document.getElementById("pick-count-sticky");
    if (a) a.textContent = text;
    if (b) b.textContent = text;
  }
  function visibleRows() {
    return Array.prototype.filter.call(
      document.querySelectorAll("#catalog-table tbody tr[data-rate]"),
      function (tr) {
        return !tr.hidden;
      }
    );
  }
  function sync() {
    var data = store();
    document.querySelectorAll(".js-pick").forEach(function (cb) {
      var row = cb.closest("tr");
      var price = row ? row.querySelector(".js-sell") : null;
      if (cb.checked && price) data[cb.value] = price.value;
      else delete data[cb.value];
    });
    save(data);
    paintCount(Object.keys(data).length);
  }
  function setPicks(predicate) {
    visibleRows().forEach(function (tr) {
      var cb = tr.querySelector(".js-pick");
      if (!cb) return;
      cb.checked = !!predicate(tr, cb);
    });
    var checkPage = document.getElementById("check-page");
    if (checkPage) {
      var rows = visibleRows();
      checkPage.checked =
        rows.length > 0 &&
        rows.every(function (tr) {
          var cb = tr.querySelector(".js-pick");
          return cb && cb.checked;
        });
    }
    sync();
  }
  function applyHideImported() {
    var hide = document.getElementById("hide-imported");
    var on = hide && hide.checked;
    document.querySelectorAll("#catalog-table tbody tr[data-rate]").forEach(function (tr) {
      tr.hidden = !!(on && tr.classList.contains("is-imported"));
    });
  }
  function setScope(value) {
    var el = document.getElementById("scope");
    if (el) el.value = value;
  }
  function bindScope(id, value, message) {
    var btn = document.getElementById(id);
    if (!btn) return;
    btn.addEventListener("click", function (event) {
      if (message && !confirm(message)) {
        event.preventDefault();
        return;
      }
      setScope(value);
    });
  }

  document.querySelectorAll(".js-sell").forEach(function (inp) {
    inp.addEventListener("input", function () {
      inp.dataset.touched = "1";
      sync();
    });
  });
  document.querySelectorAll(".js-pick").forEach(function (cb) {
    cb.addEventListener("change", sync);
  });
  var checkPage = document.getElementById("check-page");
  if (checkPage) {
    checkPage.addEventListener("change", function () {
      setPicks(function () {
        return checkPage.checked;
      });
    });
  }
  var pickPage = document.getElementById("pick-page");
  if (pickPage) {
    pickPage.addEventListener("click", function () {
      setPicks(function () {
        return true;
      });
    });
  }
  var pickNew = document.getElementById("pick-new");
  if (pickNew) {
    pickNew.addEventListener("click", function () {
      setPicks(function (tr) {
        return !tr.classList.contains("is-imported");
      });
    });
  }
  var pickClear = document.getElementById("pick-clear");
  if (pickClear) {
    pickClear.addEventListener("click", function () {
      setPicks(function () {
        return false;
      });
      save({});
      paintCount(0);
    });
  }
  var hideImported = document.getElementById("hide-imported");
  if (hideImported) {
    hideImported.addEventListener("change", function () {
      applyHideImported();
    });
  }

  var saved = store();
  document.querySelectorAll(".js-pick").forEach(function (cb) {
    if (saved[cb.value] != null) {
      cb.checked = true;
      var inp = cb.closest("tr").querySelector(".js-sell");
      if (inp) {
        inp.value = saved[cb.value];
        inp.dataset.touched = "1";
      }
    }
  });

  var recalc = document.getElementById("recalc-btn");
  if (recalc) {
    recalc.addEventListener("click", function () {
      applyPrices(true);
      sync();
    });
  }
  ["usd_rate", "percent", "fixed", "bulk_usd", "bulk_pct", "bulk_fix"].forEach(function (id) {
    var el = document.getElementById(id);
    if (el)
      el.addEventListener("input", function () {
        syncPricePair(el);
        applyPrices(false);
      });
  });

  bindScope("add-selected", "selected");
  bindScope("add-selected-sticky", "selected");
  bindScope(
    "add-filtered",
    "filtered",
    "เพิ่มบริการทั้งหมดตามตัวกรองปัจจุบัน?"
  );
  bindScope(
    "add-filtered-sticky",
    "filtered",
    "เพิ่มบริการทั้งหมดตามตัวกรองปัจจุบัน?"
  );
  bindScope(
    "add-filtered-new",
    "filtered_new",
    "เพิ่มเฉพาะรายการที่ยังไม่มี ตามตัวกรองปัจจุบัน?"
  );
  bindScope(
    "add-filtered-new-sticky",
    "filtered_new",
    "เพิ่มเฉพาะรายการที่ยังไม่มี ตามตัวกรองปัจจุบัน?"
  );
  bindScope(
    "add-main-new",
    "main_new",
    "เพิ่มเฉพาะที่ยังไม่มี จากทั้งหมวดหลักนี้?"
  );

  form.addEventListener("submit", function () {
    sync();
    document.getElementById("picks").value = JSON.stringify(store());
    var btn = document.activeElement;
    if (btn && btn.tagName === "BUTTON") {
      btn.disabled = true;
      btn.classList.add("is-loading");
    }
    form.querySelectorAll("button[type=submit]").forEach(function (b) {
      b.classList.add("is-loading");
    });
  });

  applyPrices(false);
  applyHideImported();
  sync();
})();
