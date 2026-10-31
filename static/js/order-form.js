(function () {
  var cat = document.getElementById('cat-pick');
  var svc = document.getElementById('svc-pick');
  if (!cat || !svc) return;
  var qty = document.getElementById('qty-pick');
  var meta = document.getElementById('svc-meta');
  var charge = document.getElementById('charge-preview');
  var avgEl = document.getElementById('avg-time');
  var chips = document.getElementById('qty-chips');
  var search = document.getElementById('svc-search');
  var startCat = cat.getAttribute('data-start') || '';
  var startSid = (svc.getAttribute('data-start') || '') + '';
  var cats = [];
  var catEl = document.getElementById('cat-data');
  if (catEl) {
    try { cats = JSON.parse(catEl.textContent || '[]'); } catch (e) { cats = []; }
  }
  var items = [];
  var platFilter = '';
  var cache = {};
  var ac = null;
  var timer = 0;
  var pickMode = '';
  var pickRows = [];
  var catBtn = null;
  var svcBtn = null;
  var activeWrap = null;
  var pickList = null;
  var pickFilter = null;

  function esc(s) {
    return String(s || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/"/g, '&quot;');
  }
  function splitVal(val) {
    var s = val || '';
    var i = s.indexOf(':::');
    if (i < 0) return { platform: s, category: '' };
    return { platform: s.slice(0, i), category: s.slice(i + 3) };
  }
  function current() {
    var id = svc.value;
    for (var i = 0; i < items.length; i++) {
      if (String(items[i].id) === String(id)) return items[i];
    }
    return null;
  }
  function flash(el) {
    if (!el) return;
    el.classList.remove('is-flash');
    void el.offsetWidth;
    el.classList.add('is-flash');
  }
  function fmtQty(n) {
    n = parseInt(n, 10) || 0;
    if (n >= 1000000) {
      var m = n / 1000000;
      return (Number.isInteger(m) ? m : m.toFixed(1)) + 'M';
    }
    try { return n.toLocaleString('en-US'); } catch (e) { return String(n); }
  }
  function parseFacts(name) {
    var t = decodeEnt(name || '');
    var facts = {};
    var re = /\[([^\]]+)\]/g;
    var m;
    while ((m = re.exec(t))) {
      var raw = m[1];
      var i = raw.indexOf(':');
      if (i < 0) continue;
      facts[raw.slice(0, i).trim().toLowerCase()] = raw.slice(i + 1).trim();
    }
    return facts;
  }
  function specs(s) {
    var n = decodeEnt((s && s.name) || '').toLowerCase();
    var facts = parseFacts((s && s.name) || '');
    var quality = 'คุณภาพสูง';
    var speed = facts['เริ่มงาน'] || facts['start time'] || facts['start'] || 'เริ่มตามคิว';
    var warranty = facts['รับประกันเดิม'] || facts['รับประกัน'] || facts['refill'] || facts['guarantee'] || 'ตามรายการ';
    var link = 'ลิงก์สาธารณะ';
    if (/fast|instant|express|\u0e40\u0e23\u0e47\u0e27/.test(n) && !facts['เริ่มงาน']) speed = 'เริ่มเร็ว';
    if (/refill|guarantee|\u0e23\u0e31\u0e1a\u0e1b\u0e23\u0e30\u0e01\u0e31\u0e19/.test(n) && !facts['รับประกันเดิม'] && !facts['รับประกัน']) warranty = 'มีรับประกัน';
    if (/hq|premium|real|\u0e04\u0e38\u0e13\u0e20\u0e32\u0e1e/.test(n)) quality = 'พรีเมียม';
    if (/^no$/i.test(warranty)) warranty = 'ไม่มีรับประกัน';
    if (/^yes$/i.test(warranty)) warranty = 'มีรับประกัน';
    return { quality: quality, speed: speed, warranty: warranty, link: link, facts: facts };
  }
  function currentCat() {
    var val = cat.value;
    for (var i = 0; i < cats.length; i++) {
      if (cats[i].platform + ':::' + cats[i].category === val) return cats[i];
    }
    return null;
  }
  function decodeEnt(s) {
    var t = String(s || '');
    var i = 0;
    while (i < 3 && /&(#\d+|#x[0-9a-f]+|[a-z]+);/i.test(t)) {
      var el = document.createElement('textarea');
      el.innerHTML = t;
      if (el.value === t) break;
      t = el.value;
      i += 1;
    }
    return t.replace(/\s{2,}/g, ' ').trim();
  }
  function shortName(s) {
    var t = decodeEnt(s);
    var cut = t.split('[')[0].trim();
    if (cut.length < 10) cut = t;
    if (cut.length > 64) cut = cut.slice(0, 62).trim() + '…';
    return cut;
  }
  function fmtBaht(n) {
    n = parseFloat(n) || 0;
    try { return '฿' + n.toFixed(2); } catch (e) { return '฿' + n; }
  }
  function svcTitle(s) {
    return decodeEnt((s && (s.title || s.name_short || s.name)) || 'บริการ');
  }
  function svcBits(s) {
    var bits = (s && s.bits) || [];
    if (bits.length) return bits;
    var sp = specs(s);
    var out = [];
    out.push('🚀 ' + (sp.speed || 'ตามคิว'));
    out.push('⌛ ' + (sp.speed || 'ตามคิว'));
    out.push(sp.warranty && sp.warranty.indexOf('ไม่มี') >= 0 ? '⛔ ไม่มีประกัน' : '♻️ ' + (sp.warranty || 'ตามรายการ'));
    if (s && s.recommend) out.push('⚡ แนะนำ');
    return out;
  }
  function platImg(src, extraClass) {
    if (!src) return '';
    return '<img class="la-platlogo' + (extraClass ? ' ' + extraClass : '') + '" src="' + esc(src) + '" alt="" width="22" height="22">';
  }
  function svcHtml(s) {
    var bits = svcBits(s).map(function (b) {
      return esc(String(b).replace('\u231B', '\u23F3'));
    }).join(' <span class="la-pipe">|</span> ');
    return platImg(s.logo)
      + '<em class="la-sid">' + esc(s.id) + '</em>'
      + '<em class="la-pick-price">' + esc(fmtBaht(s.rate)) + '/1k</em>'
      + '<span class="la-pick-copy">'
      + '<b>' + esc(svcTitle(s)) + '</b>'
      + (bits ? ' <span class="la-pipe">|</span> ' + bits : '')
      + '</span>';
  }
  function compactHtml(s) {
    return svcHtml(s);
  }
  function syncSvcBtn() {
    if (!svcBtn) return;
    var s = current();
    if (!s) {
      svcBtn.classList.remove('is-svcbtn');
      setBtn(svcBtn, items && items.length ? 'เลือกบริการ' : 'ไม่พบบริการ', 'ri-price-tag-3-line', '#c4b5fd');
      return;
    }
    svcBtn.classList.add('is-svcbtn');
    setBtn(svcBtn, '', 'ri-price-tag-3-line', '#c4b5fd', compactHtml(s));
  }
  function setBtn(btn, text, icon, color, html, logo) {
    if (!btn) return;
    var lab = btn.querySelector('.la-pick-label');
    var ico = btn.querySelector('.la-pick-ico');
    if (lab) {
      if (html) lab.innerHTML = html;
      else lab.textContent = text || '';
    }
    if (logo) {
      if (ico && ico.tagName === 'IMG') {
        ico.src = logo;
        ico.className = 'la-platlogo la-pick-ico';
      } else if (ico) {
        ico.outerHTML = platImg(logo, 'la-pick-ico');
      }
    } else if (ico) {
      if (ico.tagName === 'IMG') {
        var i = document.createElement('i');
        i.className = 'la-pick-ico ' + (icon || 'ri-apps-2-line');
        i.style.color = color || '#c4b5fd';
        ico.replaceWith(i);
      } else {
        ico.className = 'la-pick-ico ' + (icon || 'ri-apps-2-line');
        ico.style.color = color || '#c4b5fd';
      }
    }
  }
  function catLabel() {
    var c = currentCat();
    if (!c) return 'เลือกหมวดหมู่';
    return c.label;
  }
  function syncCatBtn() {
    var c = currentCat();
    setBtn(catBtn, catLabel(), c && c.icon, c && c.color, null, c && c.logo);
  }
  function mountPick(sel) {
    sel.classList.add('la-pick-native');
    sel.tabIndex = -1;
    var wrap = document.createElement('div');
    wrap.className = 'la-pick';
    sel.parentNode.insertBefore(wrap, sel);
    wrap.appendChild(sel);
    var btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'la-pick-btn';
    btn.innerHTML = '<i class="la-pick-ico ri-apps-2-line"></i><span class="la-pick-label">เลือก</span><i class="ri-arrow-down-s-line"></i>';
    wrap.appendChild(btn);
    var drop = document.createElement('div');
    drop.className = 'la-pick-drop';
    drop.innerHTML = '<div class="la-pick-drop-in">'
      + '<div class="la-pick-search"><i class="ri-search-line"></i>'
      + '<input type="search" class="la-pick-filter" placeholder="\u0e04\u0e49\u0e19\u0e2b\u0e32" autocomplete="off"></div>'
      + '<div class="la-pick-list" role="listbox"></div></div>';
    wrap.appendChild(drop);
    drop.addEventListener('click', function (e) { e.stopPropagation(); });
    drop.querySelector('.la-pick-list').addEventListener('click', function (e) {
      var item = e.target.closest('.la-pick-item');
      if (!item) return;
      choose(decodeURIComponent(item.getAttribute('data-value') || ''));
    });
    var ft = 0;
    drop.querySelector('.la-pick-filter').addEventListener('input', function () {
      clearTimeout(ft);
      ft = setTimeout(paintList, 50);
    });
    return btn;
  }
  function paintList() {
    if (!pickList) return;
    var q = ((pickFilter && pickFilter.value) || '').toLowerCase().trim();
    var cur = pickMode === 'cat' ? cat.value : String(svc.value || '');
    var html = '';
    for (var i = 0; i < pickRows.length; i++) {
      var row = pickRows[i];
      if (q && row.hay.indexOf(q) < 0) continue;
      html += '<button type="button" class="la-pick-item' + (row.svc ? ' is-svc' : '') + (row.value === cur ? ' is-on' : '')
        + (row.recommend ? ' is-rec' : '') + '" data-value="' + encodeURIComponent(row.value) + '">';
      if (row.svc) html += row.html;
      else {
        html += (row.logo ? platImg(row.logo) : (row.icon ? '<i class="' + row.icon + '" style="color:' + (row.color || '#c4b5fd') + '"></i>' : ''))
          + '<span><b>' + esc(row.title) + '</b></span>';
      }
      html += '</button>';
    }
    pickList.innerHTML = html || '<p class="la-pick-empty">\u0e44\u0e21\u0e48\u0e1e\u0e1a\u0e23\u0e32\u0e22\u0e01\u0e32\u0e23</p>';
    var on = pickList.querySelector('.is-on');
    if (on) on.scrollIntoView({ block: 'nearest' });
  }
  function placeDrop(wrap) {
    wrap.classList.remove('is-up');
    var btn = wrap.querySelector('.la-pick-btn');
    if (!btn) return;
    var r = btn.getBoundingClientRect();
    var room = window.innerWidth <= 720 ? 220 : 520;
    if (r.bottom + room > window.innerHeight && r.top > room) wrap.classList.add('is-up');
  }
  function openPick(mode) {
    if (pickMode === mode) { closePick(); return; }
    closePick();
    pickMode = mode;
    var btn = mode === 'cat' ? catBtn : svcBtn;
    activeWrap = btn.closest('.la-pick');
    pickList = activeWrap.querySelector('.la-pick-list');
    pickFilter = activeWrap.querySelector('.la-pick-filter');
    if (mode === 'cat') {
      pickRows = visibleCats().map(function (c) {
        return {
          value: c.platform + ':::' + c.category,
          title: c.label,
          sub: '',
          hay: ((c.label || '') + ' ' + (c.category || '') + ' ' + (c.platform || '')).toLowerCase(),
          icon: c.icon || 'ri-apps-2-line',
          color: c.color || '#c4b5fd',
          logo: c.logo || ''
        };
      });
    } else {
      pickRows = items.map(function (s) {
        var name = decodeEnt(s.name || '');
        return {
          value: String(s.id),
          html: svcHtml(s),
          svc: true,
          recommend: !!s.recommend,
          hay: (s.id + ' ' + name + ' ' + svcTitle(s) + ' ' + ((s.bits || []).join(' ')) + ' ' + (s.platform || '') + ' ' + (s.category || '')).toLowerCase()
        };
      });
    }
    pickFilter.value = '';
    paintList();
    placeDrop(activeWrap);
    activeWrap.classList.add('is-open');
    btn.classList.add('is-open');
    if (window.innerWidth > 720) {
      setTimeout(function () { pickFilter.focus(); }, 60);
    }
  }
  function closePick() {
    document.querySelectorAll('.la-pick.is-open').forEach(function (w) { w.classList.remove('is-open', 'is-up'); });
    if (catBtn) catBtn.classList.remove('is-open');
    if (svcBtn) svcBtn.classList.remove('is-open');
    pickMode = '';
    activeWrap = null;
  }
  function choose(value) {
    if (pickMode === 'cat') {
      cat.value = value;
      syncCatBtn();
      closePick();
      load('', false);
      return;
    }
    svc.value = value;
    syncSvcBtn();
    closePick();
    info();
  }
  function visibleCats() {
    var q = ((search && search.value) || '').toLowerCase().trim();
    var out = [];
    for (var i = 0; i < cats.length; i++) {
      var c = cats[i];
      if (platFilter && c.platform !== platFilter) continue;
      var hay = ((c.label || '') + ' ' + (c.category || '') + ' ' + (c.platform || '')).toLowerCase();
      if (q && hay.indexOf(q) < 0) continue;
      out.push(c);
    }
    return out;
  }
  function renderCats(keep) {
    var start = keep || cat.value;
    var list = visibleCats();
    cat.innerHTML = '';
    var blank = document.createElement('option');
    blank.value = '';
    blank.textContent = 'เลือกหมวดหมู่';
    cat.appendChild(blank);
    var first = '';
    list.forEach(function (c) {
      var o = document.createElement('option');
      o.value = c.platform + ':::' + c.category;
      o.textContent = c.label;
      cat.appendChild(o);
      if (!first) first = o.value;
    });
    if (start) cat.value = start;
    if (!cat.value && first) cat.value = first;
    syncCatBtn();
  }
  function renderChips(s) {
    if (!chips || !s || !qty) return;
    if (s.needs_comments) {
      chips.innerHTML = '';
      chips.hidden = true;
      return;
    }
    chips.hidden = false;
    var opts = [s.min_qty, 100, 500, 1000, 5000, 10000];
    if (s.max_qty && s.max_qty <= 100000) opts.push(s.max_qty);
    var seen = {};
    chips.innerHTML = '';
    opts.forEach(function (v) {
      v = parseInt(v, 10);
      if (!v || v < s.min_qty || v > s.max_qty || seen[v]) return;
      seen[v] = 1;
      var b = document.createElement('button');
      b.type = 'button';
      b.className = 'la-chip' + (String(qty.value) === String(v) ? ' is-on' : '');
      try { b.textContent = v.toLocaleString('en-US'); }
      catch (err) { b.textContent = String(v); }
      b.addEventListener('click', function () {
        qty.value = v;
        info();
      });
      chips.appendChild(b);
    });
  }
  function setText(id, text) {
    var el = document.getElementById(id);
    if (el) el.textContent = text;
  }
  function fillSelect(keepId) {
    svc.innerHTML = '';
    var first = null;
    items.forEach(function (s) {
      var o = document.createElement('option');
      o.value = s.id;
      o.textContent = '#' + s.id + '  ' + svcTitle(s);
      svc.appendChild(o);
      if (!first) first = s;
    });
    if (!svc.options.length) {
      var empty = document.createElement('option');
      empty.value = '';
      empty.textContent = 'ไม่พบบริการ';
      svc.appendChild(empty);
    }
    if (keepId) svc.value = keepId;
    if (!svc.value && first) svc.value = first.id;
    syncSvcBtn();
    info();
  }
  function renderExplain(s) {
    var box = document.getElementById('svc-explain');
    var hint = document.getElementById('qty-hint');
    if (hint) {
      if (s && s.needs_comments) {
        hint.textContent = 'ขั้นต่ำ: ' + fmtQty(s.min_qty) + ' - สูงสุด: ' + fmtQty(s.max_qty) + ' (นับจากจำนวนบรรทัดคอมเมนต์)';
      } else if (s && (s.min_qty || s.max_qty)) {
        hint.textContent = 'ขั้นต่ำ: ' + fmtQty(s.min_qty) + ' - สูงสุด: ' + fmtQty(s.max_qty);
      } else {
        hint.textContent = '';
      }
    }
    if (!box) return;
    var notes = (s && s.notes) || [];
    if (!notes.length) {
      box.innerHTML = '<p class="la-explain-head"><i class="ri-error-warning-line"></i> กรุณาอ่านคำอธิบายก่อนสั่งซื้อ</p><p class="la-muted">เลือกบริการเพื่อดูรายละเอียดจากผู้ให้บริการ</p>';
      return;
    }
    box.innerHTML = '<p class="la-explain-head"><i class="ri-error-warning-line"></i> กรุณาอ่านคำอธิบายก่อนสั่งซื้อ</p><ul>' + notes.map(function (n) {
      var val = String(n.value || '');
      var body = val.indexOf('http') === 0
        ? '<a href="' + esc(val) + '" target="_blank" rel="noopener">' + esc(val) + '</a>'
        : esc(val);
      return '<li><i class="ri-checkbox-blank-circle-fill"></i><span><b>' + esc(n.label) + ' :</b> ' + body + '</span></li>';
    }).join('') + '</ul>';
  }
  function setCharge(text) {
    if (!charge) return;
    if (charge.tagName === 'INPUT') charge.value = text;
    else charge.textContent = text;
  }
  function setAvg(text) {
    if (!avgEl) return;
    avgEl.value = text || '-';
  }
  function info() {
    var s = current();
    if (!s) {
      if (meta) meta.textContent = '';
      if (charge) setCharge('-');
      setAvg('-');
      if (chips) chips.innerHTML = '';
      var nameBlank = document.getElementById('svc-name');
      if (nameBlank) nameBlank.textContent = 'เลือกบริการทางซ้าย';
      setText('svc-desc', '');
      renderExplain(null);
      syncOrderFields(null);
      return;
    }
    if (qty) {
      qty.min = s.min_qty;
      qty.max = s.max_qty;
      if (!s.needs_comments) {
        var n = parseInt(qty.value || '0', 10);
        if (!n || n < s.min_qty) qty.value = s.min_qty;
        if (n > s.max_qty) qty.value = s.max_qty;
      }
    }
    var catShow = decodeEnt(s.category_th || s.category || '');
    var bits = svcBits(s);
    if (meta) {
      meta.textContent = bits.concat([
        'ช่วง ' + fmtQty(s.min_qty) + '-' + fmtQty(s.max_qty),
        'เรท ' + fmtBaht(s.rate) + ' ต่อ 1000'
      ]).join('  |  ');
    }
    var nameEl = document.getElementById('svc-name');
    if (nameEl) nameEl.innerHTML = (s.logo ? platImg(s.logo) : '') + esc(svcTitle(s));
    var platEl = document.getElementById('svc-plat');
    if (platEl) platEl.innerHTML = (s.logo ? platImg(s.logo) : '') + esc((s.platform || '') + (catShow ? ' · ' + catShow : ''));
    setText('svc-rate', s.rate + ' บาท');
    setText('svc-range', fmtQty(s.min_qty) + ' - ' + fmtQty(s.max_qty));
    setText('svc-desc', decodeEnt(s.desc || ''));
    var sp = specs(s);
    var facts = sp.facts || {};
    setText('spec-quality', sp.quality);
    setText('spec-speed', sp.speed);
    setText('spec-warranty', sp.warranty);
    setText('spec-link', sp.link);
    setText('svc-start', facts['เริ่มงาน'] || facts['start time'] || facts['start'] || sp.speed);
    setText('svc-pace', facts['ความเร็ว'] || facts['speed'] || facts['average time'] || '-');
    setAvg(facts['average time'] || facts['เวลาเฉลี่ย'] || facts['ความเร็ว'] || facts['speed'] || sp.speed || '-');
    setText('svc-cap', facts['สูงสุด'] || facts['max'] || facts['maximum'] || fmtQty(s.max_qty));
    if (charge && qty) {
      var qn = parseFloat(qty.value) || 0;
      var c = Math.round((parseFloat(s.rate) * qn / 1000) * 100) / 100;
      setCharge((charge.tagName === 'INPUT' ? '' : 'ค่าบริการ ') + c.toFixed(2) + ' บาท');
      setText('svc-charge', c.toFixed(2) + ' บาท');
      flash(charge);
    }
    renderChips(s);
    renderExplain(s);
    syncOrderFields(s);
    if (s.needs_comments) syncCommentsQty();
  }
  function load(keepId, useSid) {
    var parts = splitVal(cat.value);
    var q = ((search && search.value) || '').trim();
    var platform = platFilter || parts.platform || '';
    var category = q ? '' : (parts.category || '');
    var sid = useSid ? startSid : '';
    if (!platform && !category && !q && !sid) {
      items = [];
      fillSelect('');
      return;
    }
    var key = platform + '|' + category + '|' + q + '|' + sid;
    if (cache[key]) {
      items = cache[key];
      fillSelect(keepId || sid);
      return;
    }
    if (ac) ac.abort();
    ac = window.AbortController ? new AbortController() : null;
    if (svcBtn) svcBtn.classList.remove('is-svcbtn');
    setBtn(svcBtn, 'กำลังโหลด...', 'ri-loader-4-line', '#c4b5fd');
    var url = '/shop/services.json?limit=80'
      + '&platform=' + encodeURIComponent(platform)
      + '&category=' + encodeURIComponent(category)
      + '&q=' + encodeURIComponent(q);
    if (sid) url += '&sid=' + encodeURIComponent(sid);
    fetch(url, { signal: ac ? ac.signal : undefined, cache: 'default' })
      .then(function (r) { return r.json(); })
      .then(function (data) {
        items = ((data && data.items) || []).map(function (row) {
          row.name = decodeEnt(row.name);
          row.name_short = decodeEnt(row.name_short || '');
          row.title = decodeEnt(row.title || row.name_short || row.name);
          row.desc = decodeEnt(row.desc);
          row.category_th = decodeEnt(row.category_th);
          row.bits = (row.bits || []).map(function (b) { return decodeEnt(b); });
          return row;
        });
        cache[key] = items;
        fillSelect(keepId || sid);
      })
      .catch(function (err) {
        if (err && err.name === 'AbortError') return;
        items = [];
        if (svcBtn) svcBtn.classList.remove('is-svcbtn');
        setBtn(svcBtn, 'โหลดไม่สำเร็จ', 'ri-error-warning-line', '#fda4af');
      });
  }

  catBtn = mountPick(cat);
  svcBtn = mountPick(svc);
  catBtn.addEventListener('click', function (e) { e.stopPropagation(); openPick('cat'); });
  svcBtn.addEventListener('click', function (e) { e.stopPropagation(); openPick('svc'); });
  document.addEventListener('click', closePick);
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape') closePick(); });

  if (startCat) platFilter = startCat;
  renderCats();
  if (qty) qty.addEventListener('input', info);
  if (search) {
    search.addEventListener('input', function () {
      clearTimeout(timer);
      timer = setTimeout(function () {
        renderCats(cat.value);
        load(svc.value, false);
      }, 180);
    });
  }
  document.querySelectorAll('#platBar [data-cat]').forEach(function (b) {
    b.addEventListener('click', function () {
      platFilter = b.getAttribute('data-cat') || '';
      document.querySelectorAll('#platBar [data-cat]').forEach(function (x) {
        x.classList.toggle('is-on', x === b);
      });
      renderCats('');
      load('', false);
    });
  });
  var linkEl = document.getElementById('link-pick');
  var linkWrap = document.getElementById('link-wrap');
  var commentsWrap = document.getElementById('comments-wrap');
  var commentsEl = document.getElementById('comments-pick');
  var commentsHint = document.getElementById('comments-hint');

  function countCommentLines(text) {
    return String(text || '').split(/\r?\n/).filter(function (ln) { return ln.trim(); }).length;
  }
  function syncOrderFields(s) {
    var needsLink = !s || s.needs_link !== false;
    var needsComments = !!(s && s.needs_comments);
    if (linkWrap) linkWrap.hidden = !needsLink;
    if (linkEl) {
      linkEl.required = needsLink;
      if (!needsLink) linkEl.value = '';
    }
    if (commentsWrap) commentsWrap.hidden = !needsComments;
    if (commentsEl) {
      commentsEl.required = needsComments;
      commentsEl.setAttribute('rows', '8');
      if (!needsComments) commentsEl.value = '';
    }
    if (commentsHint) {
      commentsHint.textContent = needsComments
        ? 'กด Enter เพื่อขึ้นบรรทัดใหม่ · 1 บรรทัด = 1 คอมเมนต์ · จำนวนอัปเดตอัตโนมัติ'
        : '';
    }
    if (needsComments && qty) {
      qty.readOnly = true;
      qty.classList.add('is-synced');
    } else if (qty) {
      qty.readOnly = false;
      qty.classList.remove('is-synced');
    }
  }
  function syncCommentsQty() {
    var s = current();
    if (!s || !s.needs_comments || !qty || !commentsEl) return;
    var n = countCommentLines(commentsEl.value);
    if (n > 0) qty.value = n;
    else qty.value = s.min_qty || 1;
    if (commentsHint) {
      var warn = '';
      if (n > 0 && n < s.min_qty) warn = ' · ต้องมีอย่างน้อย ' + fmtQty(s.min_qty) + ' บรรทัด';
      else if (n > s.max_qty) warn = ' · เกินสูงสุด ' + fmtQty(s.max_qty) + ' บรรทัด';
      commentsHint.textContent = 'มี ' + n + ' คอมเมนต์' + warn + ' · กด Enter เพื่อขึ้นบรรทัดใหม่';
    }
    var hint = document.getElementById('qty-hint');
    if (hint) {
      hint.textContent = 'ขั้นต่ำ: ' + fmtQty(s.min_qty) + ' - สูงสุด: ' + fmtQty(s.max_qty) + ' (นับจากจำนวนบรรทัดคอมเมนต์)';
    }
    infoChargeOnly();
  }
  function infoChargeOnly() {
    var s = current();
    if (!s || !charge || !qty) return;
    var qn = parseFloat(qty.value) || 0;
    var c = Math.round((parseFloat(s.rate) * qn / 1000) * 100) / 100;
    setCharge((charge.tagName === 'INPUT' ? '' : 'ค่าบริการ ') + c.toFixed(2) + ' บาท');
    setText('svc-charge', c.toFixed(2) + ' บาท');
    flash(charge);
  }
  if (commentsEl) commentsEl.addEventListener('input', syncCommentsQty);
  var pasteBtn = document.getElementById('paste-link');
  if (pasteBtn && linkEl) {
    pasteBtn.addEventListener('click', function () {
      if (navigator.clipboard && navigator.clipboard.readText) {
        navigator.clipboard.readText().then(function (t) {
          if (t) linkEl.value = t.trim();
        }).catch(function () {
          linkEl.focus();
          linkEl.select();
        });
      } else {
        linkEl.focus();
      }
    });
  }
  load(startSid, !!startSid);
})();
