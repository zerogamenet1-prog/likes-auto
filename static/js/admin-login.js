(function () {
  var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var root = document.documentElement;
  var body = document.body;
  var card = document.getElementById("alCard");
  var form = document.getElementById("alForm");
  var user = document.getElementById("alUser");
  var pass = document.getElementById("alPass");
  var eye = document.getElementById("alEye");
  var caps = document.getElementById("alCaps");
  var remember = document.getElementById("alRemember");
  var clock = document.getElementById("alClock");
  var hello = document.getElementById("alHello");
  var typeEl = document.getElementById("alType");
  var themeBtn = document.getElementById("alTheme");
  var canvas = document.getElementById("alStars");
  var KEY = "la-admin-user";

  function pad(n) { return n < 10 ? "0" + n : String(n); }

  function tickClock() {
    var now = new Date();
    var th = new Date(now.toLocaleString("en-US", { timeZone: "Asia/Bangkok" }));
    var h = th.getHours();
    var text = pad(h) + ":" + pad(th.getMinutes()) + ":" + pad(th.getSeconds());
    if (clock) {
      clock.textContent = text + " ICT";
      clock.setAttribute("datetime", th.toISOString());
    }
    if (hello && !hello.getAttribute("data-set")) {
      var greet = h < 12 ? "อรุณสวัสดิ์ ศูนย์บัญชาการ" : h < 18 ? "สวัสดีตอนบ่าย ศูนย์บัญชาการ" : "ราตรีสวัสดิ์ ศูนย์บัญชาการ";
      hello.textContent = greet;
      hello.setAttribute("data-set", "1");
    }
  }
  tickClock();
  setInterval(tickClock, 1000);

  if (themeBtn) {
    themeBtn.addEventListener("click", function () {
      var next = root.getAttribute("data-theme") === "dark" ? "light" : "dark";
      root.setAttribute("data-theme", next);
      try { localStorage.setItem("la-dash-theme", next); } catch (e) {}
    });
  }

  try {
    var saved = localStorage.getItem(KEY) || "";
    if (user && !user.value && saved) {
      user.value = saved;
      if (remember) remember.checked = true;
      if (pass) pass.focus();
    } else if (user && user.value) {
      if (remember) remember.checked = true;
      if (pass) pass.focus();
    } else if (user) {
      user.focus();
    }
  } catch (e) {
    if (user) user.focus();
  }

  if (eye && pass) {
    eye.addEventListener("click", function () {
      var show = pass.type === "password";
      pass.type = show ? "text" : "password";
      eye.innerHTML = show ? '<i class="ri-eye-off-line"></i>' : '<i class="ri-eye-line"></i>';
      eye.setAttribute("aria-label", show ? "ซ่อนรหัสผ่าน" : "แสดงรหัสผ่าน");
    });
  }

  function checkCaps(e) {
    if (!caps) return;
    var on = e.getModifierState && e.getModifierState("CapsLock");
    caps.hidden = !on;
  }
  if (pass) {
    pass.addEventListener("keydown", checkCaps);
    pass.addEventListener("keyup", checkCaps);
  }

  if (form) {
    form.addEventListener("submit", function () {
      if (body.classList.contains("is-locked")) return;
      form.classList.add("is-busy");
      try {
        if (remember && remember.checked && user) localStorage.setItem(KEY, user.value.trim());
        else localStorage.removeItem(KEY);
      } catch (e) {}
    });
  }

  var left = parseInt(body.getAttribute("data-lock") || "0", 10);
  var hint = document.getElementById("alLockHint");
  if (left > 0) {
    var remain = left;
    var go = document.getElementById("alGo");
    function fmt(s) {
      var m = Math.floor(s / 60);
      var r = s % 60;
      return m + " นาที " + pad(r) + " วินาที";
    }
    function paint() {
      if (hint) hint.textContent = "ปลดล็อกใน " + fmt(remain);
      if (go) go.querySelector(".al-go-text").textContent = "ล็อกอยู่ · " + fmt(remain);
    }
    paint();
    var iv = setInterval(function () {
      remain -= 1;
      if (remain <= 0) {
        clearInterval(iv);
        window.location.reload();
        return;
      }
      paint();
    }, 1000);
  }

  var lines = [
    "สแกนสถานะร้าน · ออเดอร์เข้าคิวแบบเรียลไทม์",
    "เติมเงิน PromptPay พร้อมตรวจสลิปอัตโนมัติ",
    "ซิงก์บริการจาก API ผู้ให้บริการในคลิกเดียว",
    "เซสชันแอดมินหมดอายุเองเมื่อไม่ได้ใช้งาน"
  ];
  if (typeEl && !reduce) {
    var li = 0, ci = 0, del = false;
    function typeTick() {
      var word = lines[li];
      typeEl.textContent = word.slice(0, ci);
      if (!del && ci < word.length) { ci += 1; setTimeout(typeTick, 38); return; }
      if (!del && ci >= word.length) { del = true; setTimeout(typeTick, 1600); return; }
      if (del && ci > 0) { ci -= 1; setTimeout(typeTick, 18); return; }
      del = false; li = (li + 1) % lines.length; setTimeout(typeTick, 280);
    }
    typeTick();
  } else if (typeEl) {
    typeEl.textContent = lines[0];
  }

  if (card && !reduce && window.matchMedia("(pointer:fine)").matches) {
    window.addEventListener("pointermove", function (e) {
      body.style.setProperty("--mx", e.clientX + "px");
      body.style.setProperty("--my", e.clientY + "px");
      var r = card.getBoundingClientRect();
      var x = (e.clientX - r.left) / r.width - 0.5;
      var y = (e.clientY - r.top) / r.height - 0.5;
      card.style.setProperty("--ry", (x * 8).toFixed(2) + "deg");
      card.style.setProperty("--rx", (-y * 8).toFixed(2) + "deg");
    });
    card.addEventListener("pointerleave", function () {
      card.style.setProperty("--rx", "0deg");
      card.style.setProperty("--ry", "0deg");
    });
  }

  if (canvas && canvas.getContext && !reduce) {
    var ctx = canvas.getContext("2d");
    var dots = [];
    function resize() {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    }
    function seed() {
      dots = [];
      var n = Math.min(90, Math.floor((canvas.width * canvas.height) / 18000));
      for (var i = 0; i < n; i++) {
        dots.push({
          x: Math.random() * canvas.width,
          y: Math.random() * canvas.height,
          r: Math.random() * 1.6 + 0.3,
          v: Math.random() * 0.25 + 0.05
        });
      }
    }
    function draw() {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.fillStyle = "rgba(245,183,77,.55)";
      for (var i = 0; i < dots.length; i++) {
        var d = dots[i];
        d.y -= d.v;
        if (d.y < -4) { d.y = canvas.height + 4; d.x = Math.random() * canvas.width; }
        ctx.beginPath();
        ctx.arc(d.x, d.y, d.r, 0, Math.PI * 2);
        ctx.fill();
      }
      requestAnimationFrame(draw);
    }
    resize();
    seed();
    draw();
    window.addEventListener("resize", function () { resize(); seed(); });
  }
})();
