<!-- Top KPI Overview -->
<div class="page-kpi-grid">
  <div class="page-kpi-card">
    <div class="kpi-icon blue"><i class="ri-file-text-line"></i></div>
    <div class="kpi-body">
      <span class="kpi-lbl">หน้าเว็บคงที่ทั้งหมด</span>
      <span class="kpi-val"><?= count($pages) ?> <small>หน้า</small></span>
      <span class="kpi-sub"><i class="ri-checkbox-circle-line" style="color:#22c55e"></i> เผยแพร่และเปิดให้เข้าชมแล้ว</span>
    </div>
  </div>
  <div class="page-kpi-card">
    <div class="kpi-icon green"><i class="ri-shield-check-line"></i></div>
    <div class="kpi-body">
      <span class="kpi-lbl">หน้านโยบายหลัก</span>
      <span class="kpi-val text-green">3/3 <small>สมบูรณ์</small></span>
      <span class="kpi-sub">FAQ, ข้อกำหนด, นโยบาย ครบถ้วน</span>
    </div>
  </div>
  <div class="page-kpi-card">
    <div class="kpi-icon purple"><i class="ri-link-m"></i></div>
    <div class="kpi-body">
      <span class="kpi-lbl">รูปแบบ URL</span>
      <span class="kpi-val text-purple">/p/[slug]</span>
      <span class="kpi-sub">Clean SEO Friendly URLs</span>
    </div>
  </div>
  <div class="page-kpi-card">
    <div class="kpi-icon amber"><i class="ri-google-line"></i></div>
    <div class="kpi-body">
      <span class="kpi-lbl">การจัดทำดัชนี (SEO)</span>
      <span class="kpi-val text-blue">พร้อม Index</span>
      <span class="kpi-sub">รวมใน sitemap.xml อัตโนมัติ</span>
    </div>
  </div>
</div>

<!-- Add / Edit Page Form (Collapsible Drawer Card) -->
<div class="page-form-card" id="page-form-section" style="<?php if (empty($pages) || !empty($editing)): ?>display:block<?php else: ?>display:none<?php endif; ?>">
  <div class="page-form-head">
    <div style="display:flex;align-items:center;gap:10px">
      <div class="form-badge-icon">
        <i class="<?php if (!empty($editing)): ?>ri-edit-2-line<?php else: ?>ri-add-circle-line<?php endif; ?>"></i>
      </div>
      <div>
        <h3 style="margin:0;font-size:1.1rem;color:#f8fafc">
          <?php if (!empty($editing)): ?>แก้ไขหน้าเว็บ: <?= !empty($editing) ? htmlspecialchars((string)$editing['title']) : '' ?><?php else: ?>สร้างหน้าเว็บใหม่ (Create New Page)<?php endif; ?>
        </h3>
        <p class="la-muted" style="margin:2px 0 0;font-size:13px">
          กำหนดหัวข้อ, ที่อยู่ลิงก์ (Slug) และเนื้อหาหน้าเว็บที่จะแสดงให้ลูกค้าอ่าน
        </p>
      </div>
    </div>
    <button type="button" class="page-close-btn" onclick="togglePageForm()" title="ปิดแบบฟอร์ม">
      <i class="ri-close-line"></i>
    </button>
  </div>

  <!-- Quick Page Templates -->
  <div class="page-presets-row">
    <span class="preset-title"><i class="ri-magic-line"></i> แม่แบบหน้ายอดนิยม:</span>
    <div class="preset-chips">
      <button type="button" class="preset-chip" onclick="fillPagePreset('faq', 'คำถามที่พบบ่อย (FAQ)', 'รวมคำถามที่ลูกค้าสอบถามบ่อยเกี่ยวกับการสั่งซื้อ การเติมเงิน และการใช้งานระบบ')">
        <i class="ri-questionnaire-line"></i> FAQ คำถามพบบ่อย
      </button>
      <button type="button" class="preset-chip" onclick="fillPagePreset('terms', 'ข้อกำหนดการใช้งาน (Terms of Service)', 'ข้อกำหนดและเงื่อนไขการใช้บริการของ LIKES AUTO เพื่อความเข้าใจที่ถูกต้องระหว่างผู้ให้บริการและผู้ใช้บริการ')">
        <i class="ri-file-shield-line"></i> ข้อกำหนด (Terms)
      </button>
      <button type="button" class="preset-chip" onclick="fillPagePreset('privacy', 'นโยบายความเป็นส่วนตัว (Privacy Policy)', 'นโยบายการคุ้มครองข้อมูลส่วนบุคคลและการรักษาความลับของลูกค้า LIKES AUTO')">
        <i class="ri-shield-user-line"></i> นโยบาย (Privacy)
      </button>
      <button type="button" class="preset-chip" onclick="fillPagePreset('about', 'เกี่ยวกับเรา (About Us)', 'LIKES AUTO ผู้ให้บริการระบบการตลาดโซเชียลมีเดียอันดับ 1 ในไทย ด้วยระบบอัตโนมัติ 24 ชั่วโมง')">
        <i class="ri-information-line"></i> เกี่ยวกับเรา (About)
      </button>
      <button type="button" class="preset-chip" onclick="fillPagePreset('contact', 'ติดต่อเรา (Contact Us)', 'ช่องทางการติดต่อทีมงาน LIKES AUTO บริการตอบคำถามและดูแลลูกค้าทุกวัน')">
        <i class="ri-customer-service-2-line"></i> ติดต่อเรา (Contact)
      </button>
      <button type="button" class="preset-chip" onclick="fillPagePreset('guide', 'คู่มือการสั่งซื้อและเติมเงิน', 'ขั้นตอนการเติมเงินผ่าน PromptPay และการสั่งซื้อบริการปั้มไลค์ ปั้มฟอล อย่างละเอียด')">
        <i class="ri-book-open-line"></i> คู่มือ (Guide)
      </button>
    </div>
  </div>

  <form method="post" action="/admin/appearance/pages" class="page-grid-form" onsubmit="return validatePageForm(this)">
    <input type="hidden" name="pid" value="<?= !empty($editing) ? htmlspecialchars((string)$editing['id']) : '' ?>">

    <div class="form-fields-grid">
      <!-- Title -->
      <div class="field-item">
        <label class="la-field" for="page-title">
          <span>หัวข้อหน้าเว็บ (Title)</span> <span class="req">*</span>
        </label>
        <div class="input-with-icon">
          <i class="ri-heading icon"></i>
          <input class="la-input" id="page-title" name="title" value="<?= !empty($editing) ? htmlspecialchars((string)$editing['title']) : '' ?>" placeholder="เช่น คำถามที่พบบ่อย (FAQ)" required oninput="autoSuggestSlug(this.value)">
        </div>
        <span class="field-hint">ชื่อหัวข้อหลักที่จะปรากฏด้านบนสุดของหน้าเว็บ</span>
      </div>

      <!-- Slug -->
      <div class="field-item">
        <label class="la-field" for="page-slug">
          <span>ลิงก์ URL ย่อ (Slug)</span> <span class="req">*</span>
        </label>
        <div class="input-with-icon">
          <i class="ri-link icon"></i>
          <input class="la-input" id="page-slug" name="slug" placeholder="เช่น faq หรือ terms" value="<?= !empty($editing) ? htmlspecialchars((string)$editing['slug']) : '' ?>" required oninput="updateSlugPreview(this.value)">
        </div>
        <span class="slug-live-preview">
          ที่อยู่หน้าจริง: <code id="slug-preview-text">https://likes-auto.com/p/<?= !empty($editing) ? htmlspecialchars((string)$editing['slug']) : '...' ?></code>
        </span>
      </div>

      <!-- Body / Content -->
      <div class="field-item full-width">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px">
          <label class="la-field" for="page-body" style="margin:0">
            <span>เนื้อหาหน้าเว็บ (Content)</span>
          </label>
          <!-- Formatting Toolbar -->
          <div class="format-toolbar">
            <button type="button" class="format-btn" onclick="insertFormat('**', '**', 'ข้อความตัวหนา')" title="ตัวหนา (Bold)"><b>B</b></button>
            <button type="button" class="format-btn" onclick="insertFormat('*', '*', 'ข้อความตัวเอียง')" title="ตัวเอียง (Italic)"><i>I</i></button>
            <button type="button" class="format-btn" onclick="insertFormat('## ', '', 'หัวข้อย่อย')" title="หัวข้อย่อย H2"><b>H2</b></button>
            <button type="button" class="format-btn" onclick="insertFormat('- ', '', 'รายการ')" title="รายการแบบจุด (Bullet List)">• รายการ</button>
            <button type="button" class="format-btn" onclick="insertFormat('[', '](https://)', 'ชื่อลิงก์')" title="แทรก URL ลิงก์"><i class="ri-link"></i> ลิงก์</button>
            <button type="button" class="format-btn" onclick="insertFormat('> ', '', 'ข้อความเน้นพิเศษ')" title="กล่องข้อความเตือน / อ้างอิง"><i class="ri-double-quotes-l"></i> เน้น</button>
          </div>
        </div>

        <textarea class="la-input page-textarea" id="page-body" name="body" placeholder="พิมพ์เนื้อหาหน้าเว็บที่นี่ รองรับข้อความธรรมดา, เว้นวรรค, ย่อหน้า, และ Markdown..." oninput="updateWordCount()"><?= !empty($editing) ? htmlspecialchars((string)$editing['body']) : '' ?></textarea>
        
        <div class="textarea-footer">
          <span class="word-counter" id="page-char-count">0 ตัวอักษร · 0 คำ</span>
          <span class="textarea-hint"><i class="ri-information-line"></i> ขึ้นบรรทัดใหม่ด้วยปุ่ม Enter ปกติ</span>
        </div>
      </div>
    </div>

    <div class="form-btn-actions">
      <button class="la-btn la-btn-primary" type="submit" id="btn-save-page">
        <i class="ri-save-3-line"></i> <span><?php if (!empty($editing)): ?>บันทึกการแก้ไขหน้าเว็บ<?php else: ?>บันทึกและเผยแพร่หน้าเว็บ<?php endif; ?></span>
      </button>
      <?php if (!empty($editing)): ?>
      <a class="la-btn la-btn-ghost" href="/admin/appearance/pages">
        <i class="ri-close-line"></i> ยกเลิก
      </a>
      <?php else: ?>
      <button type="button" class="la-btn la-btn-ghost" onclick="togglePageForm()">
        ยกเลิก
      </button>
      <?php endif; ?>
    </div>
  </form>
</div>

<!-- Section Header & Toggles -->
<div class="page-section-header">
  <div style="display:flex;align-items:center;gap:10px">
    <h3 style="margin:0;font-size:1.15rem;color:#f8fafc">
      <i class="ri-file-list-3-line" style="color:#3b82f6"></i> รายการหน้าเว็บคงที่ทั้งหมด (<?= count($pages) ?> หน้า)
    </h3>
    <button type="button" class="la-btn la-btn-mini la-btn-primary" onclick="togglePageForm(true)">
      <i class="ri-add-line"></i> สร้างหน้าใหม่
    </button>
  </div>
  <div class="view-toggles">
    <button type="button" class="view-toggle is-active" id="view-card-btn" onclick="setPageViewMode('cards')">
      <i class="ri-grid-fill"></i> แบบการ์ด
    </button>
    <button type="button" class="view-toggle" id="view-table-btn" onclick="setPageViewMode('table')">
      <i class="ri-table-line"></i> แบบตาราง
    </button>
  </div>
</div>

<!-- 1. Rich Page Cards View -->
<div class="page-cards-container" id="page-cards-view">
  <?php if (!empty($pages)): ?>
<?php foreach ($pages as $r): ?>
  <div class="page-card-item">
    <!-- Card Head -->
    <div class="page-card-head">
      <div class="page-brand-box">
        <div class="page-avatar">
          <?php if (($r['slug'] ?? '') === 'faq'): ?>
            <i class="ri-questionnaire-line"></i>
          <?php elseif (($r['slug'] ?? '') === 'terms' || ($r['slug'] ?? '') === 'privacy'): ?>
            <i class="ri-shield-check-line"></i>
          <?php elseif (($r['slug'] ?? '') === 'contact'): ?>
            <i class="ri-customer-service-2-line"></i>
          <?php elseif (($r['slug'] ?? '') === 'about'): ?>
            <i class="ri-information-line"></i>
          <?php else: ?>
            <i class="ri-file-text-line"></i>
          <?php endif; ?>
        </div>
        <div>
          <div style="display:flex;align-items:center;gap:8px">
            <h4 class="page-title"><?= htmlspecialchars((string)($r['title'] ?? '')) ?></h4>
            <span class="page-id-badge">ID: <?= htmlspecialchars((string)($r['id'] ?? '')) ?></span>
          </div>
          <span class="page-slug-badge">
            <i class="ri-hashtag"></i> <?= htmlspecialchars((string)($r['slug'] ?? '')) ?>
          </span>
        </div>
      </div>
      <div class="page-status-indicator">
        <span class="status-pulse-dot"></span>
        <span class="status-text">ออนไลน์</span>
      </div>
    </div>

    <!-- Card Body -->
    <div class="page-card-body">
      <!-- URL Box -->
      <div class="page-url-box">
        <span class="url-lbl"><i class="ri-link"></i> URL:</span>
        <code class="url-text">https://likes-auto.com/p/<?= htmlspecialchars((string)($r['slug'] ?? '')) ?></code>
        <div class="url-btns">
          <button type="button" class="url-icon-btn" onclick="copyPageUrl('https://likes-auto.com/p/<?= htmlspecialchars((string)($r['slug'] ?? '')) ?>', this)" title="คัดลอกลิงก์">
            <i class="ri-file-copy-line"></i>
          </button>
          <a href="/p/<?= htmlspecialchars((string)($r['slug'] ?? '')) ?>" target="_blank" rel="noopener" class="url-icon-btn" title="เปิดดูหน้าจริง">
            <i class="ri-external-link-line"></i>
          </a>
        </div>
      </div>

      <!-- Content Snippet -->
      <div class="page-snippet-box">
        <span class="snippet-lbl"><i class="ri-article-line"></i> ตัวอย่างเนื้อหา:</span>
        <p class="snippet-text">
          <?php if (!empty($r['body'])): ?>
            <?= htmlspecialchars(mb_substr((string)($r['body'] ?? ''), 0, 140)) ?><?= mb_strlen((string)($r['body'] ?? '')) > 140 ? '...' : '' ?>
          <?php else: ?>
            <em class="la-muted">ยังไม่ได้กรอกเนื้อหา</em>
          <?php endif; ?>
        </p>
      </div>
    </div>

    <!-- Card Actions Footer -->
    <div class="page-card-foot">
      <a href="/p/<?= htmlspecialchars((string)($r['slug'] ?? '')) ?>" target="_blank" rel="noopener" class="la-btn la-btn-primary card-action-btn">
        <i class="ri-external-link-line"></i> <span>เปิดดูหน้าจริง</span>
      </a>
      <a href="/admin/appearance/pages?edit=<?= htmlspecialchars((string)($r['id'] ?? '')) ?>" class="la-btn la-btn-ghost card-action-btn">
        <i class="ri-edit-line"></i> <span>แก้ไข</span>
      </a>
      <form method="post" action="/admin/appearance/pages/<?= htmlspecialchars((string)($r['id'] ?? '')) ?>/delete" onsubmit="return confirm('ยืนยันลบหน้าเว็บ <?= htmlspecialchars((string)($r['title'] ?? '')) ?> (/p/<?= htmlspecialchars((string)($r['slug'] ?? '')) ?>)?')" style="margin:0">
        <button type="submit" class="la-btn la-btn-danger card-action-btn" title="ลบหน้าเว็บนี้">
          <i class="ri-delete-bin-line"></i>
        </button>
      </form>
    </div>
  </div>
  <?php endforeach; ?>
  <?php else: ?>
  <div class="page-empty-box">
    <div class="empty-icon"><i class="ri-pages-line"></i></div>
    <h4>ยังไม่มีหน้าเว็บในระบบ</h4>
    <p class="la-muted">กดปุ่ม "สร้างหน้าใหม่" ด้านบนเพื่อเริ่มสร้างหน้าข้อกำหนด นโยบาย หรือคำถามที่พบบ่อย</p>
    <button type="button" class="la-btn la-btn-primary" onclick="togglePageForm(true)">
      <i class="ri-add-line"></i> สร้างหน้าแรก
    </button>
  </div>
  <?php endif; ?>
</div>

<!-- 2. Detailed Table View (Hidden by default, toggleable) -->
<div class="adm-table-wrap page-table-wrap" id="page-table-view" style="display:none">
  <table class="adm-table">
    <thead>
      <tr>
        <th style="width:60px">ID</th>
        <th>ลิงก์ย่อ (Slug)</th>
        <th>หัวข้อหน้าเว็บ</th>
        <th>ที่อยู่หน้าจริง (URL)</th>
        <th>สถานะ</th>
        <th style="text-align:right">จัดการ</th>
      </tr>
    </thead>
    <tbody>
      <?php if (!empty($pages)): ?>
<?php foreach ($pages as $r): ?>
      <tr>
        <td><span class="page-id-badge"><?= htmlspecialchars((string)($r['id'] ?? '')) ?></span></td>
        <td><strong style="color:#60a5fa"><?= htmlspecialchars((string)($r['slug'] ?? '')) ?></strong></td>
        <td><div style="font-weight:600;color:#f8fafc"><?= htmlspecialchars((string)($r['title'] ?? '')) ?></div></td>
        <td>
          <code style="font-size:12px;background:rgba(0,0,0,0.3);padding:3px 8px;border-radius:4px;color:#38bdf8">/p/<?= htmlspecialchars((string)($r['slug'] ?? '')) ?></code>
        </td>
        <td>
          <span class="adm-badge active"><i class="ri-checkbox-circle-fill"></i> ออนไลน์</span>
        </td>
        <td>
          <div class="adm-actions" style="justify-content:flex-end">
            <a class="la-btn la-btn-mini" href="/p/<?= htmlspecialchars((string)($r['slug'] ?? '')) ?>" target="_blank" rel="noopener"><i class="ri-external-link-line"></i> เปิด</a>
            <a class="la-btn la-btn-mini la-btn-ghost" href="/admin/appearance/pages?edit=<?= htmlspecialchars((string)($r['id'] ?? '')) ?>"><i class="ri-edit-line"></i> แก้</a>
            <form method="post" action="/admin/appearance/pages/<?= htmlspecialchars((string)($r['id'] ?? '')) ?>/delete" onsubmit="return confirm('ลบหน้านี้?')" style="display:inline">
              <button class="la-btn la-btn-mini la-btn-danger" type="submit"><i class="ri-delete-bin-line"></i></button>
            </form>
          </div>
        </td>
      </tr>
      <?php endforeach; ?>
<?php else: ?>
      <tr>
        <td colspan="6" style="text-align:center;padding:30px">ยังไม่มีหน้าเว็บ</td>
      </tr>
      <?php endif; ?>
    </tbody>
  </table>
</div>

<!-- Operational & Appearance Guide -->
<div class="page-guide-grid">
  <div class="page-guide-card">
    <div class="guide-icon"><i class="ri-link-m"></i></div>
    <div class="guide-content">
      <h4>การนำลิงก์ไปใส่ในเมนูเว็บไซต์</h4>
      <p>เมื่อสร้างหน้าเสร็จแล้ว พี่สามารถนำลิงก์ <code>/p/ชื่อslug</code> ไปเพิ่มในแท็บ <a href="/admin/appearance/menu" style="color:#60a5fa">เมนู (Menu)</a> เพื่อให้ปรากฏที่ Header หรือ Footer ของเว็บไซต์ได้ทันที</p>
    </div>
  </div>
  <div class="page-guide-card">
    <div class="guide-icon"><i class="ri-smartphone-line"></i></div>
    <div class="guide-content">
      <h4>การแสดงผลบนอุปกรณ์เคลื่อนที่</h4>
      <p>ทุกหน้าที่สร้างจะถูกจัดโครงสร้างหน้าตาให้อ่านง่าย สบายตา และรองรับ Responsive บนมือถือ แท็บเล็ต และคอมพิวเตอร์โดยอัตโนมัติ</p>
    </div>
  </div>
  <div class="page-guide-card">
    <div class="guide-icon"><i class="ri-search-eye-line"></i></div>
    <div class="guide-content">
      <h4>SEO & Clean URLs</h4>
      <p>ระบบใช้โครงสร้าง URL แบบ <code>/p/[slug]</code> ที่สะอาด ปลอดภัย และเป็นมิตรกับ Search Engine เพื่อให้ติดอันดับบน Google ได้ง่ายขึ้น</p>
    </div>
  </div>
</div>
<style id="appear-pages-style">
.page-kpi-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}
.page-kpi-card {
  background: linear-gradient(180deg, rgba(30, 41, 59, 0.7) 0%, rgba(15, 23, 42, 0.8) 100%);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  padding: 18px;
  display: flex;
  align-items: center;
  gap: 14px;
  box-shadow: 0 4px 15px -3px rgba(0, 0, 0, 0.25);
  transition: transform 0.2s ease, border-color 0.2s ease;
}
.page-kpi-card:hover {
  transform: translateY(-2px);
  border-color: rgba(59, 130, 246, 0.35);
}
.page-kpi-card .kpi-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.4rem;
  flex-shrink: 0;
}
.page-kpi-card .kpi-icon.blue { background: rgba(59, 130, 246, 0.15); color: #60a5fa; border: 1px solid rgba(59, 130, 246, 0.25); }
.page-kpi-card .kpi-icon.green { background: rgba(34, 197, 94, 0.15); color: #4ade80; border: 1px solid rgba(34, 197, 94, 0.25); }
.page-kpi-card .kpi-icon.purple { background: rgba(168, 85, 247, 0.15); color: #c084fc; border: 1px solid rgba(168, 85, 247, 0.25); }
.page-kpi-card .kpi-icon.amber { background: rgba(245, 158, 11, 0.15); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.25); }
.page-kpi-card .kpi-body { display: flex; flex-direction: column; }
.page-kpi-card .kpi-lbl { font-size: 12px; color: #94a3b8; font-weight: 500; margin-bottom: 2px; }
.page-kpi-card .kpi-val { font-size: 1.35rem; font-weight: 800; color: #f8fafc; line-height: 1.2; }
.page-kpi-card .kpi-val small { font-size: 0.85rem; font-weight: 500; color: #94a3b8; }
.page-kpi-card .kpi-val.text-green { color: #22c55e; }
.page-kpi-card .kpi-val.text-purple { color: #c084fc; font-size: 1.15rem; font-family: monospace; }
.page-kpi-card .kpi-val.text-blue { color: #38bdf8; }
.page-kpi-card .kpi-sub { font-size: 11.5px; color: #64748b; margin-top: 4px; }

/* Page Form Card */
.page-form-card {
  background: linear-gradient(180deg, rgba(30, 41, 59, 0.9) 0%, rgba(15, 23, 42, 0.95) 100%);
  border: 1px solid rgba(59, 130, 246, 0.35);
  border-radius: 14px;
  padding: 22px;
  margin-bottom: 28px;
  box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.4);
  animation: fadeInDown 0.3s ease-out;
}
.page-form-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding-bottom: 14px;
  margin-bottom: 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}
.form-badge-icon {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  background: #2563eb;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.2rem;
}
.page-close-btn {
  background: transparent;
  border: none;
  color: #94a3b8;
  font-size: 1.3rem;
  cursor: pointer;
  padding: 4px;
  border-radius: 6px;
  transition: all 0.15s;
}
.page-close-btn:hover { color: #fff; background: rgba(255, 255, 255, 0.1); }

.page-presets-row {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
  background: rgba(15, 23, 42, 0.6);
  padding: 10px 14px;
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.06);
  margin-bottom: 18px;
}
.preset-title { font-size: 12.5px; font-weight: 600; color: #94a3b8; display: flex; align-items: center; gap: 5px; }
.preset-chips { display: flex; flex-wrap: wrap; gap: 6px; }
.preset-chip {
  padding: 3px 10px;
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: #cbd5e1;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s;
  display: flex;
  align-items: center;
  gap: 4px;
}
.preset-chip:hover {
  background: rgba(59, 130, 246, 0.2);
  border-color: #3b82f6;
  color: #fff;
}

.form-fields-grid {
  display: grid;
  grid-template-columns: 1.2fr 1fr;
  gap: 16px;
  margin-bottom: 20px;
}
@media (max-width: 768px) {
  .form-fields-grid { grid-template-columns: 1fr; }
}
.field-item { display: flex; flex-direction: column; }
.field-item.full-width { grid-column: 1 / -1; }
.field-item .req { color: #ef4444; font-weight: bold; }
.field-item .field-hint { font-size: 11.5px; color: #64748b; margin-top: 4px; }
.slug-live-preview { font-size: 12px; color: #94a3b8; margin-top: 4px; }
.slug-live-preview code { color: #38bdf8; background: rgba(0, 0, 0, 0.3); padding: 2px 6px; border-radius: 4px; }
.input-with-icon { position: relative; display: flex; align-items: center; }
.input-with-icon .icon {
  position: absolute;
  left: 12px;
  color: #64748b;
  font-size: 1.1rem;
  pointer-events: none;
}
.input-with-icon input {
  padding-left: 38px !important;
  width: 100%;
}

.format-toolbar {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
}
.format-btn {
  padding: 2px 8px;
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: #cbd5e1;
  font-size: 11.5px;
  cursor: pointer;
  transition: all 0.15s;
}
.format-btn:hover { background: rgba(255, 255, 255, 0.15); color: #fff; }
.page-textarea {
  min-height: 220px !important;
  padding: 14px !important;
  font-size: 14px !important;
  line-height: 1.6 !important;
  resize: vertical !important;
}
.textarea-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 6px;
  font-size: 11.5px;
  color: #64748b;
}

.form-btn-actions {
  display: flex;
  gap: 10px;
  padding-top: 14px;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
}

/* Page Cards View */
.page-section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 16px;
}
.page-cards-container {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
  gap: 18px;
  margin-bottom: 28px;
}
@media (max-width: 500px) {
  .page-cards-container { grid-template-columns: 1fr; }
}
.page-card-item {
  background: linear-gradient(180deg, rgba(30, 41, 59, 0.75) 0%, rgba(15, 23, 42, 0.85) 100%);
  border: 1px solid rgba(255, 255, 255, 0.09);
  border-radius: 14px;
  box-shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.3);
  display: flex;
  flex-direction: column;
  transition: transform 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease;
  overflow: hidden;
}
.page-card-item:hover {
  transform: translateY(-3px);
  border-color: rgba(59, 130, 246, 0.4);
  box-shadow: 0 8px 30px -4px rgba(37, 99, 235, 0.2);
}
.page-card-head {
  padding: 16px 18px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  background: rgba(15, 23, 42, 0.4);
}
.page-brand-box {
  display: flex;
  align-items: center;
  gap: 12px;
}
.page-avatar {
  width: 42px;
  height: 42px;
  border-radius: 10px;
  background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.3rem;
  box-shadow: 0 2px 10px rgba(37, 99, 235, 0.3);
}
.page-title {
  margin: 0;
  font-size: 1rem;
  font-weight: 700;
  color: #f8fafc;
}
.page-id-badge {
  font-size: 11px;
  padding: 1px 6px;
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.08);
  color: #94a3b8;
  font-weight: 600;
}
.page-slug-badge {
  font-size: 11.5px;
  color: #60a5fa;
  font-family: monospace;
  display: inline-flex;
  align-items: center;
  gap: 2px;
  margin-top: 2px;
}
.page-status-indicator {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 9px;
  border-radius: 20px;
  background: rgba(34, 197, 94, 0.12);
  border: 1px solid rgba(34, 197, 94, 0.25);
}
.status-pulse-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #22c55e;
  box-shadow: 0 0 8px #22c55e;
}
.status-text {
  font-size: 11px;
  font-weight: 600;
  color: #4ade80;
}

.page-card-body {
  padding: 16px 18px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  flex: 1;
}
.page-url-box {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 6px;
  padding: 6px 10px;
}
.page-url-box .url-lbl { font-size: 11px; color: #94a3b8; font-weight: 600; }
.page-url-box .url-text { font-size: 11.5px; color: #38bdf8; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; flex: 1; }
.url-btns { display: flex; gap: 4px; }
.url-icon-btn {
  background: transparent;
  border: none;
  color: #94a3b8;
  cursor: pointer;
  padding: 2px 4px;
  border-radius: 4px;
  font-size: 0.95rem;
}
.url-icon-btn:hover { color: #fff; }

.page-snippet-box {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.snippet-lbl { font-size: 11px; color: #94a3b8; font-weight: 600; display: flex; align-items: center; gap: 4px; }
.snippet-text {
  font-size: 12.5px;
  color: #cbd5e1;
  line-height: 1.5;
  margin: 0;
  background: rgba(255, 255, 255, 0.02);
  padding: 8px 10px;
  border-radius: 6px;
  border: 1px solid rgba(255, 255, 255, 0.04);
}

.page-card-foot {
  padding: 12px 18px;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
  background: rgba(15, 23, 42, 0.3);
  display: flex;
  gap: 8px;
}
.card-action-btn {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 7px 10px !important;
  font-size: 12.5px !important;
  font-weight: 600 !important;
  white-space: nowrap;
}

/* Empty State */
.page-empty-box {
  grid-column: 1 / -1;
  background: rgba(30, 41, 59, 0.5);
  border: 1px dashed rgba(255, 255, 255, 0.12);
  border-radius: 14px;
  padding: 40px 20px;
  text-align: center;
}
.page-empty-box .empty-icon { font-size: 3rem; color: #64748b; margin-bottom: 12px; }
.page-empty-box h4 { font-size: 1.2rem; color: #f8fafc; margin: 0 0 6px; }
.page-empty-box p { max-width: 500px; margin: 0 auto 20px; font-size: 13.5px; }

/* Operational Guide */
.page-guide-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 16px;
  margin-top: 20px;
}
.page-guide-card {
  background: rgba(15, 23, 42, 0.5);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 10px;
  padding: 16px;
  display: flex;
  gap: 14px;
}
.page-guide-card .guide-icon {
  width: 38px;
  height: 38px;
  border-radius: 8px;
  background: rgba(59, 130, 246, 0.1);
  color: #60a5fa;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.2rem;
  flex-shrink: 0;
}
.page-guide-card .guide-content h4 { margin: 0 0 4px; font-size: 13.5px; font-weight: 700; color: #f1f5f9; }
.page-guide-card .guide-content p { margin: 0; font-size: 12px; color: #94a3b8; line-height: 1.45; }
</style>

<script id="appear-pages-js">
function togglePageForm(forceOpen) {
  var formSec = document.getElementById('page-form-section');
  if (!formSec) return;
  var isOpen = formSec.style.display !== 'none';
  if (forceOpen || !isOpen) {
    formSec.style.display = 'block';
    formSec.scrollIntoView({ behavior: 'smooth', block: 'start' });
    var titleInp = document.getElementById('page-title');
    if (titleInp) setTimeout(function(){ titleInp.focus(); }, 200);
  } else {
    formSec.style.display = 'none';
  }
}

function fillPagePreset(slug, title, body) {
  var sInp = document.getElementById('page-slug');
  var tInp = document.getElementById('page-title');
  var bInp = document.getElementById('page-body');
  if (sInp) { sInp.value = slug; updateSlugPreview(slug); }
  if (tInp) tInp.value = title;
  if (bInp && !bInp.value) { bInp.value = body; updateWordCount(); }
}

function updateSlugPreview(val) {
  var clean = val.toLowerCase().replace(/[^a-z0-9_-]/g, '-').replace(/-+/g, '-');
  var sInp = document.getElementById('page-slug');
  if (sInp && sInp.value !== clean) sInp.value = clean;
  var preview = document.getElementById('slug-preview-text');
  if (preview) preview.textContent = 'https://likes-auto.com/p/' + (clean || '...');
}

function autoSuggestSlug(title) {
  var sInp = document.getElementById('page-slug');
  if (sInp && !sInp.value) {
    var slug = title.toLowerCase().trim().replace(/[^a-z0-9]/g, '-').replace(/-+/g, '-').replace(/^-|-$/g, '');
    if (slug) {
      sInp.value = slug;
      updateSlugPreview(slug);
    }
  }
}

function insertFormat(prefix, suffix, placeholder) {
  var textarea = document.getElementById('page-body');
  if (!textarea) return;
  var start = textarea.selectionStart;
  var end = textarea.selectionEnd;
  var sel = textarea.value.substring(start, end) || placeholder;
  var rep = prefix + sel + suffix;
  textarea.value = textarea.value.substring(0, start) + rep + textarea.value.substring(end);
  textarea.focus();
  textarea.setSelectionRange(start + prefix.length, start + prefix.length + sel.length);
  updateWordCount();
}

function updateWordCount() {
  var textarea = document.getElementById('page-body');
  var counter = document.getElementById('page-char-count');
  if (!textarea || !counter) return;
  var val = textarea.value || '';
  var chars = val.length;
  var words = val.trim() ? val.trim().split(/\s+/).length : 0;
  counter.textContent = chars.toLocaleString() + ' ตัวอักษร · ' + words.toLocaleString() + ' คำ';
}

function setPageViewMode(mode) {
  var cardsView = document.getElementById('page-cards-view');
  var tableView = document.getElementById('page-table-view');
  var btnCards = document.getElementById('view-card-btn');
  var btnTable = document.getElementById('view-table-btn');
  if (mode === 'cards') {
    if (cardsView) cardsView.style.display = 'grid';
    if (tableView) tableView.style.display = 'none';
    if (btnCards) btnCards.className = 'view-toggle is-active';
    if (btnTable) btnTable.className = 'view-toggle';
  } else {
    if (cardsView) cardsView.style.display = 'none';
    if (tableView) tableView.style.display = 'block';
    if (btnCards) btnCards.className = 'view-toggle';
    if (btnTable) btnTable.className = 'view-toggle is-active';
  }
}

function copyPageUrl(url, btn) {
  navigator.clipboard.writeText(url).then(function() {
    var orig = btn.innerHTML;
    btn.innerHTML = '<i class="ri-check-line" style="color:#22c55e"></i>';
    setTimeout(function() { btn.innerHTML = orig; }, 1500);
  });
}

function validatePageForm(form) {
  var slug = form.slug ? form.slug.value.trim() : '';
  var title = form.title ? form.title.value.trim() : '';
  if (!slug) {
    alert('กรุณากรอกลิงก์ย่อ (Slug)');
    return false;
  }
  if (!title) {
    alert('กรุณากรอกหัวข้อหน้าเว็บ (Title)');
    return false;
  }
  return true;
}

setTimeout(updateWordCount, 100);
</script>