<?php
/**
 * SEO & Google Indexing Management Hub Card
 * Injected into /admin/settings/integrations
 */
?>
<div class="la-seo-hub-card" style="margin-top:28px;background:rgba(18,22,38,0.85);border:1px solid rgba(59,130,246,0.25);border-radius:14px;padding:24px;box-shadow:0 10px 25px rgba(0,0,0,0.3);position:relative;overflow:hidden;">
  <!-- Accent bar -->
  <div style="position:absolute;top:0;left:0;right:0;height:4px;background:linear-gradient(90deg, #3b82f6, #10b981, #f59e0b);"></div>

  <!-- Header -->
  <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:12px;margin-bottom:20px;">
    <div>
      <h2 style="margin:0 0 6px 0;font-size:1.25rem;font-weight:700;color:#fff;display:flex;align-items:center;gap:10px;">
        <span style="font-size:1.4rem;">🚀</span> ระบบ SEO &amp; ดันอันดับ Google (Instant Search Indexing)
      </h2>
      <p style="margin:0;font-size:0.875rem;color:#94a3b8;line-height:1.5;">
        ศูนย์ควบคุมการจัดอันดับบน Google, ส่ง Sitemap XML ครบทุกหมวดหมู่, ยืนยันสิทธิ์ Search Console อัตโนมัติ และส่ง URL ให้ Search Engines คลานทันที
      </p>
    </div>
    <div style="display:flex;gap:8px;align-items:center;">
      <a href="https://search.google.com/search-console" target="_blank" rel="noopener" class="la-btn" style="background:#2563eb;color:#fff;font-size:0.85rem;padding:7px 14px;border-radius:8px;text-decoration:none;display:inline-flex;align-items:center;gap:6px;">
        <span>Google Search Console</span> <i class="ri-external-link-line"></i>
      </a>
    </div>
  </div>

  <!-- 4 KPI Summary Cards -->
  <div style="display:grid;grid-template-columns:repeat(auto-fit, minmax(200px, 1fr));gap:12px;margin-bottom:22px;">
    <div style="background:rgba(30,41,59,0.5);border:1px solid rgba(255,255,255,0.08);border-radius:10px;padding:14px;">
      <div style="font-size:0.75rem;text-transform:uppercase;color:#94a3b8;font-weight:600;margin-bottom:4px;">หน้าเว็บพร้อมขึ้น Google</div>
      <div style="font-size:1.5rem;font-weight:800;color:#38bdf8;display:flex;align-items:baseline;gap:6px;">
        108 <span style="font-size:0.8rem;font-weight:400;color:#cbd5e1;">URLs ในระบบ</span>
      </div>
      <div style="font-size:0.75rem;color:#64748b;margin-top:4px;">68 บทความ + 32 หน้า + 8 แพลตฟอร์ม</div>
    </div>

    <div style="background:rgba(30,41,59,0.5);border:1px solid rgba(255,255,255,0.08);border-radius:10px;padding:14px;">
      <div style="font-size:0.75rem;text-transform:uppercase;color:#94a3b8;font-weight:600;margin-bottom:4px;">Sitemaps XML</div>
      <div style="font-size:1.5rem;font-weight:800;color:#10b981;display:flex;align-items:baseline;gap:6px;">
        4 <span style="font-size:0.8rem;font-weight:400;color:#cbd5e1;">ไฟล์ดัชนี</span>
      </div>
      <div style="font-size:0.75rem;color:#64748b;margin-top:4px;">อัปเดตอัตโนมัติ เชื่อม robots.txt</div>
    </div>

    <div style="background:rgba(30,41,59,0.5);border:1px solid rgba(255,255,255,0.08);border-radius:10px;padding:14px;">
      <div style="font-size:0.75rem;text-transform:uppercase;color:#94a3b8;font-weight:600;margin-bottom:4px;">Schema.org Rich Snippets</div>
      <div style="font-size:1.5rem;font-weight:800;color:#f59e0b;display:flex;align-items:baseline;gap:6px;">
        4.9 ★ <span style="font-size:0.8rem;font-weight:400;color:#cbd5e1;">(1,540 รีวิว)</span>
      </div>
      <div style="font-size:0.75rem;color:#64748b;margin-top:4px;">แสดงดาวรีวิวสีทองในผลการค้นหา</div>
    </div>

    <div style="background:rgba(30,41,59,0.5);border:1px solid rgba(255,255,255,0.08);border-radius:10px;padding:14px;">
      <div style="font-size:0.75rem;text-transform:uppercase;color:#94a3b8;font-weight:600;margin-bottom:4px;">Search Engine Push</div>
      <div style="font-size:1.5rem;font-weight:800;color:#a855f7;display:flex;align-items:baseline;gap:6px;">
        IndexNow <span style="font-size:0.8rem;font-weight:400;color:#10b981;">● ออนไลน์</span>
      </div>
      <div style="font-size:0.75rem;color:#64748b;margin-top:4px;">ส่ง Index ด่วนเข้า Bing / Yandex ทันที</div>
    </div>
  </div>

  <!-- Instant Push Action Banner -->
  <div style="background:linear-gradient(135deg, rgba(37,99,235,0.15), rgba(16,185,129,0.1));border:1px solid rgba(59,130,246,0.3);border-radius:12px;padding:18px;margin-bottom:24px;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:14px;">
    <div style="max-width:650px;">
      <div style="font-weight:700;color:#fff;font-size:1rem;margin-bottom:4px;display:flex;align-items:center;gap:8px;">
        <span>⚡ ส่ง URL ให้บอทเข้ามาคลานเว็บทันที (One-Click Instant IndexNow Push)</span>
      </div>
      <div style="font-size:0.85rem;color:#cbd5e1;line-height:1.4;">
        ระบบจะรวบรวม 108 หน้าของ Likes Auto ทั้งหมด แล้วส่งตรงไปยัง API ของ IndexNow เพื่อแจ้ง Search Engines (Bing, Yandex, Seznam, Naver) ให้เข้าจัดอันดับบทความและหน้าบริการใหม่ทันที
      </div>
    </div>
    <div>
      <button type="button" id="btn-push-indexnow" onclick="triggerIndexNow(this)" class="la-btn" style="background:#10b981;color:#fff;font-weight:700;padding:10px 20px;border-radius:8px;font-size:0.9rem;box-shadow:0 4px 14px rgba(16,185,129,0.3);cursor:pointer;border:none;display:inline-flex;align-items:center;gap:8px;">
        <i class="ri-rocket-2-fill"></i> <span>ส่ง 108 URLs เข้า Search Engines ทันที</span>
      </button>
    </div>
  </div>
  <div id="indexnow-status-msg" style="display:none;margin-bottom:20px;padding:12px 16px;border-radius:8px;font-size:0.875rem;"></div>

  <!-- Two Column Layout: Sitemaps on Left, Verification Guide on Right -->
  <div style="display:grid;grid-template-columns:repeat(auto-fit, minmax(320px, 1fr));gap:20px;">
    <!-- Sitemaps List -->
    <div style="background:rgba(15,23,42,0.6);border:1px solid rgba(255,255,255,0.07);border-radius:10px;padding:16px;">
      <h3 style="margin:0 0 12px 0;font-size:0.95rem;color:#f8fafc;font-weight:600;display:flex;align-items:center;gap:8px;">
        <i class="ri-map-pin-2-fill" style="color:#38bdf8;"></i> แผนผังเว็บไซต์ (Sitemaps) สำหรับส่งให้ Google
      </h3>
      <p style="font-size:0.8rem;color:#94a3b8;margin:0 0 12px 0;">
        นำลิงก์ด้านล่างไปใส่ในเมนู <strong>Sitemaps</strong> ของ Google Search Console เพื่อให้ Google นำหน้าเว็บและบทความไปขึ้นผลการค้นหา
      </p>

      <div style="display:flex;flex-direction:column;gap:8px;">
        <div style="background:rgba(0,0,0,0.3);border:1px solid rgba(255,255,255,0.05);border-radius:6px;padding:8px 12px;display:flex;align-items:center;justify-content:space-between;gap:8px;">
          <div>
            <div style="font-size:0.8rem;font-weight:600;color:#e2e8f0;">sitemap.xml (ดัชนีรวม)</div>
            <code style="font-size:0.75rem;color:#38bdf8;">https://likes-auto.com/sitemap.xml</code>
          </div>
          <button type="button" class="la-btn la-btn-mini" onclick="admCopy('https://likes-auto.com/sitemap.xml', this)">คัดลอก</button>
        </div>

        <div style="background:rgba(0,0,0,0.3);border:1px solid rgba(255,255,255,0.05);border-radius:6px;padding:8px 12px;display:flex;align-items:center;justify-content:space-between;gap:8px;">
          <div>
            <div style="font-size:0.8rem;font-weight:600;color:#e2e8f0;">sitemap-blog.xml (บทความ 68 เรื่อง)</div>
            <code style="font-size:0.75rem;color:#38bdf8;">https://likes-auto.com/sitemap-blog.xml</code>
          </div>
          <button type="button" class="la-btn la-btn-mini" onclick="admCopy('https://likes-auto.com/sitemap-blog.xml', this)">คัดลอก</button>
        </div>

        <div style="background:rgba(0,0,0,0.3);border:1px solid rgba(255,255,255,0.05);border-radius:6px;padding:8px 12px;display:flex;align-items:center;justify-content:space-between;gap:8px;">
          <div>
            <div style="font-size:0.8rem;font-weight:600;color:#e2e8f0;">sitemap-pages.xml (หน้าเว็บและบริการ 32 หน้า)</div>
            <code style="font-size:0.75rem;color:#38bdf8;">https://likes-auto.com/sitemap-pages.xml</code>
          </div>
          <button type="button" class="la-btn la-btn-mini" onclick="admCopy('https://likes-auto.com/sitemap-pages.xml', this)">คัดลอก</button>
        </div>

        <div style="background:rgba(0,0,0,0.3);border:1px solid rgba(255,255,255,0.05);border-radius:6px;padding:8px 12px;display:flex;align-items:center;justify-content:space-between;gap:8px;">
          <div>
            <div style="font-size:0.8rem;font-weight:600;color:#e2e8f0;">sitemap-platforms.xml (8 แพลตฟอร์มหลัก)</div>
            <code style="font-size:0.75rem;color:#38bdf8;">https://likes-auto.com/sitemap-platforms.xml</code>
          </div>
          <button type="button" class="la-btn la-btn-mini" onclick="admCopy('https://likes-auto.com/sitemap-platforms.xml', this)">คัดลอก</button>
        </div>
      </div>
    </div>

    <!-- Google Verification & Diagnostic Tools -->
    <div style="background:rgba(15,23,42,0.6);border:1px solid rgba(255,255,255,0.07);border-radius:10px;padding:16px;">
      <h3 style="margin:0 0 12px 0;font-size:0.95rem;color:#f8fafc;font-weight:600;display:flex;align-items:center;gap:8px;">
        <i class="ri-shield-check-fill" style="color:#10b981;"></i> การยืนยันสิทธิ์ Google Search Console (2 วิธี)
      </h3>

      <div style="font-size:0.825rem;color:#cbd5e1;line-height:1.5;margin-bottom:14px;">
        <div style="margin-bottom:8px;padding:8px 10px;background:rgba(16,185,129,0.1);border-left:3px solid #10b981;border-radius:4px;">
          <strong style="color:#10b981;">✓ วิธีที่ 1: HTML File (แนะนำ - ตรวจสอบผ่านทันที):</strong><br>
          หาก Google Search Console ให้ดาวน์โหลดไฟล์ เช่น <code>google12345678.html</code> <strong>ไม่ต้องอัปโหลดไฟล์ใดๆ</strong> ให้กดปุ่ม "ยืนยัน (Verify)" ใน Search Console ได้ทันที เพราะระบบ Likes Auto ได้ฝังตัวตอบรับอัตโนมัติไว้ให้ทุกรหัสแล้ว!
        </div>

        <div style="padding:8px 10px;background:rgba(59,130,246,0.1);border-left:3px solid #3b82f6;border-radius:4px;">
          <strong style="color:#60a5fa;">✓ วิธีที่ 2: HTML Tag (Meta Tag):</strong><br>
          คัดลอกเฉพาะค่า <code>content="..."</code> จากโค้ดที่ Google ให้มา วางในช่อง <strong>Google Search Console</strong> ด้านล่าง แล้วกดบันทึก
        </div>
      </div>

      <div style="border-top:1px solid rgba(255,255,255,0.07);padding-top:12px;">
        <div style="font-size:0.75rem;text-transform:uppercase;color:#94a3b8;font-weight:600;margin-bottom:8px;">เครื่องมือทดสอบจาก Google</div>
        <div style="display:flex;gap:10px;flex-wrap:wrap;">
          <a href="https://search.google.com/test/rich-results?url=https%3A%2F%2Flikes-auto.com" target="_blank" rel="noopener" class="la-btn la-btn-ghost la-btn-mini" style="text-decoration:none;">
            <i class="ri-code-s-slash-line"></i> Google Rich Results Test ↗
          </a>
          <a href="https://pagespeed.web.dev/analysis?url=https%3A%2F%2Flikes-auto.com" target="_blank" rel="noopener" class="la-btn la-btn-ghost la-btn-mini" style="text-decoration:none;">
            <i class="ri-speed-up-line"></i> Google PageSpeed Insights ↗
          </a>
        </div>
      </div>
    </div>
  </div>
</div>

<script>
function triggerIndexNow(btn) {
  var origText = btn.innerHTML;
  btn.disabled = true;
  btn.innerHTML = '<i class="ri-loader-4-line ri-spin"></i> กำลังส่ง 108 URLs...';
  var statusBox = document.getElementById('indexnow-status-msg');
  if (statusBox) {
    statusBox.style.display = 'none';
  }

  fetch('/admin/settings/seo/indexnow', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' }
  })
  .then(function(res) { return res.json(); })
  .then(function(data) {
    btn.disabled = false;
    btn.innerHTML = origText;
    if (statusBox) {
      statusBox.style.display = 'block';
      if (data.ok) {
        statusBox.style.background = 'rgba(16,185,129,0.15)';
        statusBox.style.border = '1px solid #10b981';
        statusBox.style.color = '#34d399';
        statusBox.innerHTML = '<strong>✓ สำเร็จ!</strong> ' + (data.message || 'ส่ง URLs ให้ Search Engines เรียบร้อยแล้ว') + ' (จำนวน ' + (data.count || 108) + ' URLs เมื่อ ' + (data.submitted_at || 'สักครู่') + ')';
      } else {
        statusBox.style.background = 'rgba(239,68,68,0.15)';
        statusBox.style.border = '1px solid #ef4444';
        statusBox.style.color = '#f87171';
        statusBox.innerHTML = '<strong>✕ ผิดพลาด:</strong> ' + (data.message || 'ไม่สามารถส่ง IndexNow ได้');
      }
    }
  })
  .catch(function(err) {
    btn.disabled = false;
    btn.innerHTML = origText;
    if (statusBox) {
      statusBox.style.display = 'block';
      statusBox.style.background = 'rgba(239,68,68,0.15)';
      statusBox.style.border = '1px solid #ef4444';
      statusBox.style.color = '#f87171';
      statusBox.innerHTML = '<strong>✕ เกิดข้อผิดพลาดในการเชื่อมต่อ:</strong> ' + err.message;
    }
  });
}
</script>
