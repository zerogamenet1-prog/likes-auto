(function(){
  var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var coarse = window.matchMedia && window.matchMedia('(pointer: coarse)').matches;
  var rootEl = document.documentElement;

  function ready(fn){
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', fn);
    else fn();
  }

  function toast(msg){
    var el = document.getElementById('laToast');
    if (!el) return;
    el.textContent = msg;
    el.classList.add('show');
    clearTimeout(toast._t);
    toast._t = setTimeout(function(){ el.classList.remove('show'); }, 1800);
  }
  window.laToast = toast;

  function copyText(text){
    if (navigator.clipboard && navigator.clipboard.writeText) {
      return navigator.clipboard.writeText(text);
    }
    return new Promise(function(res, rej){
      var ta = document.createElement('textarea');
      ta.value = text;
      ta.setAttribute('readonly', '');
      ta.style.position = 'fixed';
      ta.style.left = '-9999px';
      document.body.appendChild(ta);
      ta.select();
      try { document.execCommand('copy'); res(); }
      catch (err) { rej(err); }
      document.body.removeChild(ta);
    });
  }

  function fmt(n){
    try { return Math.round(n).toLocaleString('en-US'); }
    catch (e) { return String(Math.round(n)); }
  }

  function countUp(el){
    var target = parseFloat(el.getAttribute('data-target') || '0');
    if (!target || el.getAttribute('data-done') === '1') return;
    el.setAttribute('data-done', '1');
    if (reduce) { el.textContent = fmt(target); return; }
    var start = performance.now();
    var dur = 1100;
    var tick = function(now){
      var t = Math.min(1, (now - start) / dur);
      var e = 1 - Math.pow(1 - t, 3);
      el.textContent = fmt(target * e);
      if (t < 1) requestAnimationFrame(tick);
      else el.textContent = fmt(target);
    };
    requestAnimationFrame(tick);
  }

  ready(function(){
    document.body.classList.add('la-ready');
    if (window.laSyncPack) window.laSyncPack();

    var nodes = document.querySelectorAll('.la-card,.la-plat,.la-why,.la-svc,.la-stat,.la-faq details,.la-page-head,.la-order-card,.la-form-shell,.la-cta-band,.la-section h2,.la-prose,.la-code,.la-table-wrap,.la-notice,.adm-card,.adm-ok,.adm-error,.la-filter,.la-review,.la-photo-card,.la-pay-card,.la-hero-login,.la-bigstat,.la-plat-pill,.la-pay-shot,.la-split-photo,.la-feat-list article,.la-about-card,.la-why-card,.la-step-card,.la-login-card,.la-sample-table,.la-pop-card,.la-marquee,.la-statsbar,.la-rate-card,.la-hero-social');
    if (!reduce && !coarse) {
      for (var i = 0; i < nodes.length; i++) {
        nodes[i].classList.add('la-reveal');
        nodes[i].style.setProperty('--d', ((i % 8) * 45) + 'ms');
      }
      if ('IntersectionObserver' in window) {
        var io = new IntersectionObserver(function(entries){
          for (var j = 0; j < entries.length; j++) {
            if (entries[j].isIntersecting) {
              entries[j].target.classList.add('is-in');
              var nums = entries[j].target.querySelectorAll('[data-target]');
              for (var q = 0; q < nums.length; q++) countUp(nums[q]);
              if (entries[j].target.hasAttribute('data-target')) countUp(entries[j].target);
              io.unobserve(entries[j].target);
            }
          }
        }, {threshold: 0.08, rootMargin: '0px 0px -6% 0px'});
        for (var k = 0; k < nodes.length; k++) io.observe(nodes[k]);
      } else {
        for (var n = 0; n < nodes.length; n++) nodes[n].classList.add('is-in');
        var all = document.querySelectorAll('[data-target]');
        for (var a = 0; a < all.length; a++) countUp(all[a]);
      }
    } else {
      var all2 = document.querySelectorAll('[data-target]');
      for (var a2 = 0; a2 < all2.length; a2++) countUp(all2[a2]);
    }

    var header = document.querySelector('.la-header');
    var bar = document.getElementById('laProgress');
    var topBtn = document.getElementById('laTop');
    var onScroll = function(){
      if (header) header.classList.toggle('is-scrolled', window.scrollY > 8);
      if (topBtn) topBtn.classList.toggle('is-on', window.scrollY > 420);
      if (bar) {
        var h = document.documentElement;
        var max = h.scrollHeight - h.clientHeight;
        var p = max > 0 ? h.scrollTop / max : 0;
        bar.style.transform = 'scaleX(' + Math.min(1, Math.max(0, p)).toFixed(4) + ')';
      }
    };
    onScroll();
    window.addEventListener('scroll', onScroll, {passive:true});

    document.addEventListener('pointerdown', function(e){
      var b = e.target.closest('.la-btn, .la-google-btn, .la-iconbtn, .la-chip');
      if (!b || reduce) return;
      var r = b.getBoundingClientRect();
      var s = document.createElement('span');
      s.className = 'la-ripple';
      s.style.left = (e.clientX - r.left) + 'px';
      s.style.top = (e.clientY - r.top) + 'px';
      b.appendChild(s);
      setTimeout(function(){ if (s.parentNode) s.parentNode.removeChild(s); }, 560);
    });

    document.addEventListener('submit', function(e){
      var form = e.target;
      if (!form || form.tagName !== 'FORM') return;
      var msg = form.getAttribute('data-confirm');
      if (msg && !window.confirm(msg)) { e.preventDefault(); return; }
      if (form.hasAttribute('data-no-load')) return;
      var btn = form.querySelector('button[type="submit"], button.la-btn');
      if (!btn || btn.disabled) return;
      btn.classList.add('is-loading');
      btn.setAttribute('aria-busy', 'true');
    });

    document.addEventListener('invalid', function(e){
      if (!e.target || !e.target.classList) return;
      e.target.classList.remove('is-shake');
      void e.target.offsetWidth;
      e.target.classList.add('is-shake');
    }, true);

    document.addEventListener('click', function(e){
      var amt = e.target.closest('[data-amt]');
      if (amt) {
        var form = amt.closest('form');
        var inp = form && form.querySelector('input[name="amount"]');
        if (inp) {
          inp.value = amt.getAttribute('data-amt');
          inp.dispatchEvent(new Event('input', {bubbles:true}));
          inp.classList.remove('is-flash');
          void inp.offsetWidth;
          inp.classList.add('is-flash');
          var list = form.querySelectorAll('[data-amt]');
          for (var i = 0; i < list.length; i++) list[i].classList.toggle('is-on', list[i] === amt);
        }
        return;
      }
      var t = e.target.closest('[data-copy]');
      if (!t) return;
      e.preventDefault();
      var text = t.getAttribute('data-copy') || (t.textContent || '').trim();
      if (!text) return;
      copyText(text).then(function(){ toast('คัดลอกแล้ว'); }).catch(function(){ toast('คัดลอกแล้ว'); });
    });

    var cells = document.querySelectorAll('.la-svc-table td[data-label="สถานะ"]');
    for (var c = 0; c < cells.length; c++) cells[c].classList.add('la-status');

    var faqs = document.querySelectorAll('.la-faq details');
    for (var f = 0; f < faqs.length; f++) {
      faqs[f].addEventListener('toggle', function(){
        if (!this.open) return;
        for (var x = 0; x < faqs.length; x++) if (faqs[x] !== this) faqs[x].open = false;
      });
    }

    var live = document.getElementById('laLiveCount');
    if (live && !reduce) {
      var n = parseInt((live.textContent || '4523').replace(/,/g, ''), 10) || 4523;
      setInterval(function(){
        n += Math.floor(Math.random() * 7) + 1;
        if (n > 9800) n = 4100 + Math.floor(Math.random() * 400);
        live.textContent = fmt(n);
      }, 1800);
    }

    if (reduce || coarse) return;

    var tx = window.innerWidth * 0.72, ty = 120, x = tx, y = ty, raf = 0;
    var move = function(){
      x += (tx - x) * 0.14;
      y += (ty - y) * 0.14;
      rootEl.style.setProperty('--lx', x.toFixed(1) + 'px');
      rootEl.style.setProperty('--ly', y.toFixed(1) + 'px');
      raf = 0;
      if (Math.abs(tx - x) > 0.5 || Math.abs(ty - y) > 0.5) raf = requestAnimationFrame(move);
    };
    window.addEventListener('pointermove', function(e){
      tx = e.clientX; ty = e.clientY;
      if (!raf) raf = requestAnimationFrame(move);
      var card = e.target.closest('.la-card,.la-plat,.la-why,.la-svc,.la-stat,.la-order-card,.la-form-shell,.la-cta-band,.la-modal-card,.adm-card,.la-about-card,.la-why-card,.la-plat-card,.la-login-card,.la-review,.la-pop-card,.la-pay-shot,.la-step-card');
      if (card) {
        var r = card.getBoundingClientRect();
        card.style.setProperty('--sx', ((e.clientX - r.left) / r.width * 100).toFixed(2) + '%');
        card.style.setProperty('--sy', ((e.clientY - r.top) / r.height * 100).toFixed(2) + '%');
      }
      var phone = e.target.closest('.la-phone-wrap');
      if (phone) {
        var pr = phone.getBoundingClientRect();
        var dx = (e.clientX - (pr.left + pr.width / 2)) / pr.width;
        var dy = (e.clientY - (pr.top + pr.height / 2)) / pr.height;
        phone.style.setProperty('--rx', (-dy * 8).toFixed(2) + 'deg');
        phone.style.setProperty('--ry', (dx * 10).toFixed(2) + 'deg');
      }
    }, {passive:true});
  });
})();
