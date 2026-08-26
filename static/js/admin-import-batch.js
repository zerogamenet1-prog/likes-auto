(function () {
  var overlay = document.getElementById("imp-progress");
  var bar = document.getElementById("imp-progress-bar");
  var pctEl = document.getElementById("imp-progress-pct");
  var textEl = document.getElementById("imp-progress-text");
  var subEl = document.getElementById("imp-progress-sub");
  var cancelBtn = document.getElementById("imp-progress-cancel");
  var cancelled = false;
  var running = false;

  function csrf() {
    var meta = document.querySelector('meta[name="csrf-token"]');
    if (meta && meta.content) return meta.content;
    var inp = document.querySelector('input[name="csrf_token"], input[name="_csrf"]');
    return inp ? inp.value : "";
  }

  function val() {
    var usd = document.getElementById("bulk_usd") || document.getElementById("usd_rate");
    var pct = document.getElementById("bulk_pct") || document.getElementById("percent");
    var fix = document.getElementById("bulk_fix") || document.getElementById("fixed");
    return {
      usd_rate: usd ? usd.value : "35",
      percent: pct ? pct.value : "100",
      fixed: fix ? fix.value : "0"
    };
  }

  function pid() {
    var el =
      document.querySelector("#imp-bulk-top input[name=pid]") ||
      document.querySelector("#import-form input[name=pid]") ||
      document.getElementById("imp-pid");
    return el ? el.value : "";
  }

  function formFilters() {
    var form = document.getElementById("import-form");
    if (!form) return { q: "", cat: "", main: "", stype: "" };
    function g(name) {
      var n = form.querySelector('[name="' + name + '"]');
      return n ? n.value : "";
    }
    return { q: g("q"), cat: g("cat"), main: g("main"), stype: g("stype") };
  }

  function setProgress(percent, processed, total, addedTotal) {
    percent = Math.max(0, Math.min(100, percent || 0));
    if (bar) bar.style.width = percent + "%";
    if (pctEl) pctEl.textContent = percent + "%";
    if (subEl) {
      subEl.textContent = processed + " / " + total + " · เพิ่มแล้ว " + addedTotal + " รายการ";
    }
  }

  function showOverlay(on) {
    if (!overlay) return;
    overlay.hidden = !on;
    document.body.classList.toggle("imp-progress-open", !!on);
  }

  function sleep(ms) {
    return new Promise(function (resolve) {
      setTimeout(resolve, ms);
    });
  }

  async function postBatch(body) {
    var headers = { "Content-Type": "application/x-www-form-urlencoded" };
    var token = csrf();
    if (token) headers["X-CSRF-Token"] = token;
    var res = await fetch("/admin/services/import/batch", {
      method: "POST",
      headers: headers,
      body: body,
      credentials: "same-origin"
    });
    if (!res.ok) {
      var errText = await res.text();
      throw new Error("HTTP " + res.status + " " + (errText || "").slice(0, 120));
    }
    return res.json();
  }

  async function runBatch(btn) {
    if (running) return;
    var scope = btn.getAttribute("data-scope") || "all_new";
    var filters = formFilters();
    if (btn.getAttribute("data-from-form") !== "1") {
      filters.q = "";
      filters.cat = "";
      filters.stype = "";
      filters.main = btn.getAttribute("data-main") || filters.main || "";
      if (scope === "all" || scope === "all_new") filters.main = "";
    }
    var totalHint = parseInt(btn.getAttribute("data-total") || "0", 10) || 0;
    var labels = {
      all: "เพิ่ม/อัปเดตทั้งหมด",
      all_new: "เพิ่มทั้งหมดที่ยังไม่มี",
      main: "เพิ่มทั้งหมวดหลัก",
      main_new: "เพิ่มทั้งหมวดหลัก (ที่ยังไม่มี)",
      filtered: "เพิ่มทั้งที่กรอง",
      filtered_new: "เพิ่มที่กรอง (ที่ยังไม่มี)"
    };
    var msg =
      (labels[scope] || "นำเข้า") +
      (totalHint ? " ประมาณ " + totalHint + " รายการ" : "") +
      "?\nระบบจะนำเข้าทีละชุดพร้อมแสดงเปอร์เซ็นต์";
    if (!window.confirm(msg)) return;

    running = true;
    cancelled = false;
    showOverlay(true);
    if (textEl) textEl.textContent = "เริ่มนำเข้า…";
    setProgress(0, 0, totalHint || 0, 0);
    if (cancelBtn) {
      cancelBtn.disabled = false;
      cancelBtn.textContent = "ยกเลิก";
    }

    var prices = val();
    var offset = 0;
    var batch = 100;
    var addedTotal = 0;
    var total = totalHint;

    try {
      while (!cancelled) {
        var params = new URLSearchParams();
        params.set("pid", pid());
        params.set("scope", scope);
        params.set("usd_rate", prices.usd_rate);
        params.set("percent", prices.percent);
        params.set("fixed", prices.fixed);
        params.set("q", filters.q || "");
        params.set("cat", filters.cat || "");
        params.set("main", filters.main || "");
        params.set("stype", filters.stype || "");
        params.set("offset", String(offset));
        params.set("batch", String(batch));
        var token = csrf();
        if (token) params.set("csrf_token", token);

        if (textEl) textEl.textContent = "กำลังนำเข้า… " + offset + "/" + (total || "?");
        var data = await postBatch(params.toString());
        if (!data || !data.ok) throw new Error((data && data.error) || "batch failed");

        addedTotal += parseInt(data.added || 0, 10) || 0;
        total = parseInt(data.total || total, 10) || total;
        offset = parseInt(data.next_offset || offset + batch, 10);
        setProgress(data.percent, data.processed, total, addedTotal);
        if (textEl) {
          textEl.textContent = data.done
            ? "นำเข้าเสร็จแล้ว"
            : "กำลังนำเข้า… " + (data.percent || 0) + "%";
        }
        if (data.done) break;
        await sleep(120);
      }

      if (cancelled) {
        if (textEl) textEl.textContent = "ยกเลิกแล้ว · นำเข้าไปแล้ว " + addedTotal + " รายการ";
        await sleep(900);
        showOverlay(false);
      } else {
        setProgress(100, total, total, addedTotal);
        if (textEl) textEl.textContent = "เสร็จสิ้น · เพิ่ม/อัปเดต " + addedTotal + " รายการ";
        await sleep(700);
        window.location.href = "/admin/services?added=" + encodeURIComponent(addedTotal);
        return;
      }
    } catch (err) {
      var msgErr = err && err.message ? err.message : String(err);
      if (textEl) textEl.textContent = "เกิดข้อผิดพลาด: " + msgErr;
      if (subEl) subEl.textContent = "ลองใหม่ได้ หรือลดจำนวนด้วยตัวกรองหมวด";
      if (cancelBtn) cancelBtn.textContent = "ปิด";
      try { window.alert("นำเข้าไม่สำเร็จ: " + msgErr); } catch (e) {}
      return;
    } finally {
      running = false;
    }
  }

  if (cancelBtn) {
    cancelBtn.addEventListener("click", function () {
      if (running) {
        cancelled = true;
        cancelBtn.disabled = true;
        if (textEl) textEl.textContent = "กำลังหยุดหลังชุดปัจจุบัน…";
      } else {
        showOverlay(false);
        cancelBtn.textContent = "ยกเลิก";
      }
    });
  }

  document.addEventListener("click", function (ev) {
    var t = ev.target;
    var btn = t && t.closest ? t.closest(".js-imp-batch") : null;
    if (!btn) return;
    ev.preventDefault();
    runBatch(btn);
  });
})();
