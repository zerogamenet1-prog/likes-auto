(function () {
  var mq = window.matchMedia;
  var reduce = mq && mq("(prefers-reduced-motion: reduce)").matches;
  var coarse = mq && mq("(pointer: coarse)").matches;
  var saveData = !!(navigator.connection && navigator.connection.saveData);
  var lightFX = reduce || coarse || saveData;

  function ready(fn) {
    if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", fn);
    else fn();
  }

  function whenIdle(fn, ms) {
    if (window.requestIdleCallback) {
      window.requestIdleCallback(fn, { timeout: ms || 1800 });
    } else {
      setTimeout(fn, ms || 400);
    }
  }

  function visible(el, cb, margin) {
    if (!el) return;
    if (!("IntersectionObserver" in window)) {
      cb(true);
      return;
    }
    var io = new IntersectionObserver(
      function (ents) {
        ents.forEach(function (e) {
          if (e.isIntersecting) {
            cb(true);
            io.disconnect();
          }
        });
      },
      { rootMargin: margin || "80px 0px" }
    );
    io.observe(el);
  }

  /* —— Reviews slider —— */
  function initReviews() {
    var track = document.getElementById("laRevTrack");
    var slider = document.getElementById("laRevSlider");
    var dotsBox = document.getElementById("laRevDots");
    if (!track || !slider || !dotsBox) return;
    var cards = Array.prototype.slice.call(track.querySelectorAll(".la-rev-card"));
    if (!cards.length) return;
    var hold = false;
    var hover = false;
    var inView = !coarse;
    var timer = null;

    function leftOf(card) {
      return card.getBoundingClientRect().left - track.getBoundingClientRect().left + track.scrollLeft;
    }
    function nearest() {
      var x = track.scrollLeft;
      var best = 0;
      var gap = 1e9;
      cards.forEach(function (card, i) {
        var d = Math.abs(leftOf(card) - x);
        if (d < gap) {
          gap = d;
          best = i;
        }
      });
      return best;
    }
    function paint() {
      var i = nearest();
      Array.prototype.forEach.call(dotsBox.children, function (btn, n) {
        btn.classList.toggle("is-on", n === i);
      });
    }
    function go(dir) {
      var i = nearest() + dir;
      if (i < 0) i = cards.length - 1;
      if (i >= cards.length) i = 0;
      track.scrollTo({ left: leftOf(cards[i]), behavior: reduce ? "auto" : "smooth" });
    }
    cards.forEach(function (_, i) {
      var btn = document.createElement("button");
      btn.type = "button";
      btn.setAttribute("aria-label", "รีวิว " + (i + 1));
      btn.addEventListener("click", function () {
        track.scrollTo({ left: leftOf(cards[i]), behavior: reduce ? "auto" : "smooth" });
      });
      dotsBox.appendChild(btn);
    });
    var prev = document.getElementById("laRevPrev");
    var next = document.getElementById("laRevNext");
    if (prev) prev.onclick = function () { go(-1); };
    if (next) next.onclick = function () { go(1); };
    track.addEventListener("scroll", paint, { passive: true });
    paint();

    function tick() {
      if (!hold && !hover && inView && !document.hidden) go(1);
    }
    function arm() {
      if (timer) clearInterval(timer);
      if (reduce) return;
      timer = setInterval(tick, coarse ? 7000 : 4800);
    }
    arm();

    if ("IntersectionObserver" in window) {
      var vio = new IntersectionObserver(
        function (ents) {
          ents.forEach(function (e) {
            inView = e.isIntersecting;
          });
        },
        { threshold: 0.15 }
      );
      vio.observe(slider);
    }

    track.addEventListener("pointerdown", function () { hold = true; });
    ["pointerup", "pointercancel"].forEach(function (ev) {
      track.addEventListener(ev, function () { hold = false; });
    });
    if (!coarse) {
      slider.addEventListener("mouseenter", function () { hover = true; });
      slider.addEventListener("mouseleave", function () {
        hover = false;
        hold = false;
      });
    }
  }

  /* —— Hero spin + password eye —— */
  function initHeroBits() {
    var spin = document.getElementById("laHeroSpin");
    if (spin && !reduce) {
      var words = (spin.getAttribute("data-words") || "")
        .split(",")
        .map(function (w) { return w.trim(); })
        .filter(Boolean);
      var i = 0;
      if (words.length > 1) {
        setInterval(function () {
          i = (i + 1) % words.length;
          spin.classList.add("is-swap");
          setTimeout(function () {
            spin.textContent = "เพิ่มยอดบน " + words[i];
            spin.classList.remove("is-swap");
          }, 180);
        }, coarse ? 3600 : 2400);
      }
    }
    var pass = document.getElementById("laHomePass");
    var eye = document.getElementById("laHomeEye");
    if (pass && eye) {
      eye.addEventListener("click", function () {
        var show = pass.type === "password";
        pass.type = show ? "text" : "password";
        eye.innerHTML = show ? '<i class="ri-eye-off-line"></i>' : '<i class="ri-eye-line"></i>';
        eye.setAttribute("aria-label", show ? "ซ่อนรหัสผ่าน" : "แสดงรหัสผ่าน");
      });
    }
  }

  /* —— Live ticker (data from Python JSON) —— */
  function initTicker() {
    var rail = document.getElementById("laTickerRail");
    var meta = document.getElementById("laTickerMeta");
    var box = document.getElementById("laLiveTicker");
    if (!rail || !box) return;
    var raw = document.getElementById("laTickerData");
    var pool = [];
    try {
      pool = raw ? JSON.parse(raw.textContent || "[]") : [];
    } catch (e) {
      pool = [];
    }
    if (!pool.length) return;

    var deck = [];
    var items = [];
    var hourCount = 52 + Math.floor(Math.random() * 28);
    var started = false;

    function shuffle(arr) {
      for (var i = arr.length - 1; i > 0; i--) {
        var j = Math.floor(Math.random() * (i + 1));
        var t = arr[i];
        arr[i] = arr[j];
        arr[j] = t;
      }
      return arr;
    }
    function refill() {
      deck = shuffle(pool.slice());
    }
    function fmt(n) {
      try {
        return Math.round(n).toLocaleString("th-TH");
      } catch (e) {
        return String(n);
      }
    }
    function pick() {
      if (!deck.length) refill();
      var base = deck.pop();
      var visibleMap = {};
      for (var i = 0; i < items.length; i++) visibleMap[items[i].u] = 1;
      var guard = 0;
      while (visibleMap[base.u] && deck.length && guard < 8) {
        deck.unshift(base);
        base = deck.pop();
        guard++;
      }
      var jitter = Math.max(1, Math.round(base.q * (0.75 + Math.random() * 0.55)));
      return {
        u: base.u,
        p: base.p,
        s: base.s,
        q: jitter,
        l: base.l,
        oid: 84000 + Math.floor(Math.random() * 14000),
        age: Math.floor(Math.random() * 18) + 2,
      };
    }
    function ageText(sec) {
      if (sec < 8) return "เมื่อกี้";
      if (sec < 60) return sec + " วินาทีที่แล้ว";
      return Math.max(1, Math.floor(sec / 60)) + " นาทีที่แล้ว";
    }
    function render(row, hot) {
      var el = document.createElement("article");
      el.className = "la-ticker-item" + (hot ? " is-hot" : "");
      el.innerHTML =
        '<div class="la-ticker-logo"><img src="/static/assets/plats/' +
        row.l +
        '.svg" alt="" width="22" height="22" loading="lazy" decoding="async"></div>' +
        '<div class="la-ticker-body"><strong>' +
        row.u +
        " · สั่ง " +
        row.s +
        "</strong><span>" +
        row.p +
        " · #" +
        row.oid +
        " · กำลังส่งงาน</span></div>" +
        '<div class="la-ticker-meta"><b>+' +
        fmt(row.q) +
        "</b><small>" +
        ageText(row.age) +
        "</small></div>";
      return el;
    }
    function paint(hotFirst) {
      rail.innerHTML = "";
      for (var i = 0; i < items.length; i++) {
        rail.appendChild(render(items[i], hotFirst && i === 0));
      }
      if (meta) meta.textContent = "+" + hourCount + " ออเดอร์ใน 1 ชม.";
    }
    function tick() {
      if (document.hidden) return;
      var next = pick();
      next.age = 2 + Math.floor(Math.random() * 5);
      items.unshift(next);
      if (items.length > (coarse ? 2 : 3)) items.pop();
      hourCount += 1;
      paint(true);
      var nodes = rail.querySelectorAll(".la-ticker-item");
      for (var i = 1; i < nodes.length; i++) {
        var age = items[i].age + (4 + Math.floor(Math.random() * 9));
        items[i].age = age;
        var small = nodes[i].querySelector("small");
        if (small) small.textContent = ageText(age);
      }
    }
    function start() {
      if (started) return;
      started = true;
      refill();
      var n = coarse ? 2 : 3;
      for (var s = 0; s < n; s++) items.push(pick());
      paint(true);
      var delay = reduce ? 10000 : coarse ? 5200 : 2600 + Math.floor(Math.random() * 1400);
      setInterval(tick, delay);
    }

    if (coarse || saveData) {
      whenIdle(start, 1600);
    } else {
      start();
    }
  }

  ready(function () {
    initHeroBits();
    initReviews();
    initTicker();
  });
})();
