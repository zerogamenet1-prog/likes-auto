<style>
/* === LIKES AUTO BLOG ADMIN REVAMP 2026 === */
.blog-kpi-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}
.blog-kpi-card {
  background: linear-gradient(135deg, rgba(30, 41, 59, 0.7), rgba(15, 23, 42, 0.8));
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 14px;
  padding: 18px 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);
  transition: transform 0.2s ease, border-color 0.2s ease;
}
.blog-kpi-card:hover {
  transform: translateY(-2px);
  border-color: rgba(99, 102, 241, 0.4);
}
.kpi-icon {
  width: 52px;
  height: 52px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  flex-shrink: 0;
}
.kpi-icon.blue { background: rgba(59, 130, 246, 0.15); color: #60a5fa; border: 1px solid rgba(59, 130, 246, 0.3); }
.kpi-icon.green { background: rgba(34, 197, 94, 0.15); color: #4ade80; border: 1px solid rgba(34, 197, 94, 0.3); }
.kpi-icon.amber { background: rgba(245, 158, 11, 0.15); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.3); }
.kpi-icon.purple { background: rgba(168, 85, 247, 0.15); color: #c084fc; border: 1px solid rgba(168, 85, 247, 0.3); }
.kpi-body { display: flex; flex-direction: column; }
.kpi-lbl { font-size: 13px; color: #94a3b8; font-weight: 500; }
.kpi-val { font-size: 24px; font-weight: 700; color: #f8fafc; margin: 2px 0; }
.kpi-val small { font-size: 14px; font-weight: 400; color: #94a3b8; margin-left: 4px; }
.kpi-sub { font-size: 12px; color: #64748b; }

/* Alert Messages */
.blog-alert-ok {
  background: rgba(34, 197, 94, 0.12);
  border: 1px solid rgba(34, 197, 94, 0.3);
  color: #86efac;
  padding: 12px 18px;
  border-radius: 10px;
  margin-bottom: 20px;
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 14px;
}

/* Control & Filter Bar */
.blog-control-bar {
  background: rgba(15, 23, 42, 0.6);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 14px;
  padding: 16px 20px;
  margin-bottom: 24px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.blog-filter-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}
.blog-search-box {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1;
  min-width: 280px;
}
.search-input-wrap {
  position: relative;
  flex: 1;
}
.search-input-wrap i {
  position: absolute;
  left: 12px;
  top: 50%;
  transform: translateY(-50%);
  color: #64748b;
  font-size: 16px;
}
.search-input-wrap input {
  padding-left: 36px !important;
  width: 100%;
}
.blog-actions-right {
  display: flex;
  align-items: center;
  gap: 10px;
}
.view-toggles {
  display: inline-flex;
  background: rgba(0, 0, 0, 0.4);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 8px;
  padding: 2px;
}
.view-toggle {
  background: transparent;
  border: none;
  color: #94a3b8;
  padding: 6px 12px;
  font-size: 13px;
  border-radius: 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: all 0.15s ease;
}
.view-toggle.is-active {
  background: #3b82f6;
  color: #ffffff;
  font-weight: 600;
}

/* Category Filter Chips */
.blog-chips-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  padding-top: 10px;
  border-top: 1px solid rgba(255, 255, 255, 0.05);
}
.chips-lbl {
  font-size: 12px;
  color: #64748b;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 4px;
}
.filter-chip {
  background: rgba(30, 41, 59, 0.8);
  border: 1px solid rgba(255, 255, 255, 0.06);
  color: #cbd5e1;
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.15s ease;
  text-decoration: none;
  display: inline-flex;
  align-items: center;
  gap: 5px;
}
.filter-chip:hover, .filter-chip.active {
  background: rgba(59, 130, 246, 0.2);
  border-color: #3b82f6;
  color: #93c5fd;
}

/* Add / Edit Drawer Card */
.blog-form-card {
  background: linear-gradient(135deg, rgba(30, 41, 59, 0.95), rgba(15, 23, 42, 0.98));
  border: 1px solid rgba(99, 102, 241, 0.35);
  border-radius: 16px;
  padding: 24px;
  margin-bottom: 28px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4);
  animation: slideDown 0.25s ease-out;
}
@keyframes slideDown {
  from { opacity: 0; transform: translateY(-10px); }
  to { opacity: 1; transform: translateY(0); }
}
.blog-form-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
  padding-bottom: 14px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}
.form-badge-icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background: rgba(99, 102, 241, 0.2);
  color: #818cf8;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
}
.blog-close-btn {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: #94a3b8;
  width: 32px;
  height: 32px;
  border-radius: 8px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s ease;
}
.blog-close-btn:hover {
  background: rgba(239, 68, 68, 0.2);
  color: #ef4444;
  border-color: rgba(239, 68, 68, 0.4);
}

/* Form Two-Column Grid */
.blog-editor-grid {
  display: grid;
  grid-template-columns: 1fr 340px;
  gap: 24px;
}
@media (max-width: 1024px) {
  .blog-editor-grid { grid-template-columns: 1fr; }
}
.field-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-bottom: 16px;
}
.field-hint {
  font-size: 12px;
  color: #64748b;
}
.slug-live-preview {
  font-size: 12px;
  color: #94a3b8;
  margin-top: 4px;
}
.slug-live-preview code {
  color: #38bdf8;
  background: rgba(0, 0, 0, 0.3);
  padding: 2px 6px;
  border-radius: 4px;
}

/* Preset Tag Chips in Form */
.preset-tag-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin: 6px 0 12px;
}
.ptag-chip {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: #cbd5e1;
  padding: 3px 10px;
  border-radius: 6px;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.15s ease;
}
.ptag-chip:hover {
  background: rgba(99, 102, 241, 0.2);
  border-color: #818cf8;
  color: #ffffff;
}

/* Formatting Toolbar */
.format-toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 4px;
  background: rgba(15, 23, 42, 0.7);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-bottom: none;
  border-radius: 8px 8px 0 0;
  padding: 6px 10px;
}
.format-btn {
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.06);
  color: #cbd5e1;
  padding: 4px 8px;
  border-radius: 5px;
  font-size: 12px;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  transition: all 0.15s ease;
}
.format-btn:hover {
  background: rgba(59, 130, 246, 0.25);
  border-color: #3b82f6;
  color: #ffffff;
}
.blog-textarea {
  border-top-left-radius: 0 !important;
  border-top-right-radius: 0 !important;
  min-height: 440px !important;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 13.5px;
  line-height: 1.6;
}
.textarea-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 6px;
  font-size: 12px;
  color: #64748b;
}

/* Media Sidebar in Form */
.blog-side-box {
  background: rgba(15, 23, 42, 0.6);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 16px;
}
.blog-side-title {
  font-size: 13px;
  font-weight: 600;
  color: #e2e8f0;
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  gap: 6px;
}
.blog-gallery-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
  max-height: 280px;
  overflow-y: auto;
  padding-right: 4px;
}
.blog-thumb-btn {
  background: rgba(0, 0, 0, 0.4);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  padding: 3px;
  cursor: pointer;
  transition: all 0.15s ease;
  display: flex;
  aspect-ratio: 16/9;
  overflow: hidden;
}
.blog-thumb-btn:hover {
  border-color: #3b82f6;
  transform: scale(1.05);
}
.blog-thumb-btn img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 5px;
}

/* === RICH BLOG CARDS GRID === */
.blog-cards-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
}
.blog-card-item {
  background: linear-gradient(135deg, rgba(30, 41, 59, 0.7), rgba(15, 23, 42, 0.8));
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 16px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
  transition: transform 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease;
}
.blog-card-item:hover {
  transform: translateY(-4px);
  border-color: rgba(99, 102, 241, 0.4);
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.35);
}
.blog-card-cover-wrap {
  position: relative;
  width: 100%;
  aspect-ratio: 16/9;
  background: linear-gradient(135deg, #1e1b4b, #0f172a);
  overflow: hidden;
}
.blog-card-cover {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.3s ease;
}
.blog-card-item:hover .blog-card-cover {
  transform: scale(1.04);
}
.blog-card-fallback-cover {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 40px;
  color: rgba(255, 255, 255, 0.2);
  background: linear-gradient(135deg, #1e293b, #0f172a);
}
.blog-badge-overlay {
  position: absolute;
  top: 12px;
  right: 12px;
  display: flex;
  gap: 6px;
}
.status-pill {
  font-size: 11px;
  font-weight: 600;
  padding: 4px 10px;
  border-radius: 20px;
  backdrop-filter: blur(8px);
  display: inline-flex;
  align-items: center;
  gap: 4px;
}
.status-pill.published {
  background: rgba(34, 197, 94, 0.25);
  border: 1px solid rgba(34, 197, 94, 0.4);
  color: #86efac;
}
.status-pill.draft {
  background: rgba(148, 163, 184, 0.25);
  border: 1px solid rgba(148, 163, 184, 0.4);
  color: #e2e8f0;
}
.card-id-pill {
  position: absolute;
  top: 12px;
  left: 12px;
  background: rgba(0, 0, 0, 0.6);
  border: 1px solid rgba(255, 255, 255, 0.15);
  color: #94a3b8;
  font-size: 11px;
  font-weight: 600;
  padding: 3px 8px;
  border-radius: 6px;
  backdrop-filter: blur(4px);
}

.blog-card-content {
  padding: 18px 20px;
  display: flex;
  flex-direction: column;
  flex: 1;
}
.blog-card-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 10px;
}
.tag-badge {
  font-size: 11px;
  background: rgba(59, 130, 246, 0.15);
  color: #93c5fd;
  border: 1px solid rgba(59, 130, 246, 0.25);
  padding: 2px 8px;
  border-radius: 4px;
}
.blog-card-title {
  margin: 0 0 10px;
  font-size: 1.05rem;
  font-weight: 700;
  line-height: 1.4;
  color: #f8fafc;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.blog-card-title:hover {
  color: #60a5fa;
}
.blog-card-url {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: #94a3b8;
  margin-bottom: 12px;
  background: rgba(0, 0, 0, 0.25);
  padding: 4px 8px;
  border-radius: 6px;
  border: 1px solid rgba(255, 255, 255, 0.04);
}
.blog-card-url code {
  color: #38bdf8;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
}
.blog-card-excerpt {
  font-size: 13px;
  color: #94a3b8;
  line-height: 1.5;
  margin: 0 0 14px;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
  flex: 1;
}
.blog-card-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 12px;
  color: #64748b;
  padding-top: 12px;
  border-top: 1px solid rgba(255, 255, 255, 0.05);
}

.blog-card-actions {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 12px 20px;
  background: rgba(15, 23, 42, 0.5);
  border-top: 1px solid rgba(255, 255, 255, 0.06);
}
.blog-card-actions .la-btn {
  flex: 1;
  text-align: center;
  justify-content: center;
}

/* Detailed Table View */
.blog-table-cover {
  width: 54px;
  height: 34px;
  border-radius: 4px;
  object-fit: cover;
  margin-right: 10px;
  vertical-align: middle;
}

/* Guide Cards */
.blog-guide-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 16px;
  margin-top: 24px;
}
.blog-guide-card {
  background: rgba(15, 23, 42, 0.5);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 12px;
  padding: 18px;
  display: flex;
  gap: 14px;
}
.blog-guide-card .guide-icon {
  width: 42px;
  height: 42px;
  border-radius: 10px;
  background: rgba(59, 130, 246, 0.15);
  color: #60a5fa;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  flex-shrink: 0;
}
.blog-guide-card h4 { margin: 0 0 6px; font-size: 14px; color: #f1f5f9; }
.blog-guide-card p { margin: 0; font-size: 13px; color: #94a3b8; line-height: 1.5; }
</style>

<!-- Top KPI Overview -->
<div class="blog-kpi-grid">
  <div class="blog-kpi-card">
    <div class="kpi-icon blue"><i class="ri-article-line"></i></div>
    <div class="kpi-body">
      <span class="kpi-lbl">บทความทั้งหมด</span>
      <span class="kpi-val"><?= (int)($all_n ?? count($posts ?? [])) ?> <small>บทความ</small></span>
      <span class="kpi-sub">คลังคอนเทนต์รวมในระบบ</span>
    </div>
  </div>
  <div class="blog-kpi-card">
    <div class="kpi-icon green"><i class="ri-checkbox-circle-line"></i></div>
    <div class="kpi-body">
      <span class="kpi-lbl">เผยแพร่ออนไลน์</span>
      <span class="kpi-val text-green" style="color:#4ade80"><?= (int)($pub_n ?? 0) ?> <small>บทความ</small></span>
      <span class="kpi-sub"><i class="ri-wifi-line" style="color:#22c55e"></i> เปิดให้บุคคลภายนอกเข้าอ่าน</span>
    </div>
  </div>
  <div class="blog-kpi-card">
    <div class="kpi-icon amber"><i class="ri-draft-line"></i></div>
    <div class="kpi-body">
      <span class="kpi-lbl">ฉบับร่าง / ซ่อน</span>
      <span class="kpi-val" style="color:#fbbf24"><?= (int)($draft_n ?? 0) ?> <small>ฉบับ</small></span>
      <span class="kpi-sub">กำลังเขียนหรือปิดชั่วคราว</span>
    </div>
  </div>
  <div class="blog-kpi-card">
    <div class="kpi-icon purple"><i class="ri-search-eye-line"></i></div>
    <div class="kpi-body">
      <span class="kpi-lbl">การจัดทำดัชนี (SEO)</span>
      <span class="kpi-val" style="color:#c084fc">SEO Ready</span>
      <span class="kpi-sub">Clean URL + Meta + Sitemap</span>
    </div>
  </div>
</div>

<?php if (!empty($saved)): ?>
<div class="blog-alert-ok">
  <i class="ri-checkbox-circle-fill" style="font-size:20px;color:#22c55e"></i>
  <span><strong>สำเร็จ!</strong> บันทึกข้อมูลบทความเรียบร้อยแล้ว</span>
</div>
<?php endif; ?>

<!-- Action & Filter Control Bar -->
<div class="blog-control-bar">
  <div class="blog-filter-row">
    <!-- Search Form -->
    <form method="get" class="blog-search-box" style="margin:0">
      <div class="search-input-wrap">
        <i class="ri-search-line"></i>
        <input class="la-input" name="q" value="<?= htmlspecialchars((string)($q ?? '')) ?>" placeholder="ค้นหาชื่อเรื่อง, แท็ก หรือสลัก URL...">
      </div>
      <select class="la-input" name="st" onchange="this.form.submit()" style="width:140px">
        <option value="" <?php if (empty($st)): ?>selected<?php endif; ?>>ทุกสถานะ</option>
        <option value="on" <?php if (($st ?? '') === 'on'): ?>selected<?php endif; ?>>🟢 เผยแพร่แล้ว</option>
        <option value="off" <?php if (($st ?? '') === 'off'): ?>selected<?php endif; ?>>⚪ ฉบับร่าง</option>
      </select>
      <button class="la-btn la-btn-mini" type="submit">ค้นหา</button>
      <?php if (!empty($q) || !empty($st)): ?>
      <a class="la-btn la-btn-mini la-btn-ghost" href="/admin/appearance/blog">ล้างค่า</a>
      <?php endif; ?>
    </form>

    <!-- Actions Right -->
    <div class="blog-actions-right">
      <div class="view-toggles">
        <button type="button" class="view-toggle is-active" id="view-card-btn" onclick="setBlogViewMode('cards')">
          <i class="ri-grid-fill"></i> แบบการ์ด
        </button>
        <button type="button" class="view-toggle" id="view-table-btn" onclick="setBlogViewMode('table')">
          <i class="ri-table-line"></i> แบบตาราง
        </button>
      </div>
      <button type="button" class="la-btn la-btn-primary" onclick="toggleBlogForm(true)">
        <i class="ri-add-line"></i> เขียนบทความใหม่
      </button>
    </div>
  </div>

  <!-- Quick Category Filter Chips -->
  <div class="blog-chips-row">
    <span class="chips-lbl"><i class="ri-filter-3-line"></i> หมวดหมู่:</span>
    <a href="/admin/appearance/blog" class="filter-chip <?php if (empty($q)): ?>active<?php endif; ?>">ทั้งหมด</a>
    <a href="/admin/appearance/blog?q=Facebook" class="filter-chip <?php if (($q ?? '') === 'Facebook'): ?>active<?php endif; ?>">
      <i class="ri-facebook-circle-fill" style="color:#1877f2"></i> Facebook
    </a>
    <a href="/admin/appearance/blog?q=TikTok" class="filter-chip <?php if (($q ?? '') === 'TikTok'): ?>active<?php endif; ?>">
      <i class="ri-tiktok-fill"></i> TikTok
    </a>
    <a href="/admin/appearance/blog?q=Instagram" class="filter-chip <?php if (($q ?? '') === 'Instagram'): ?>active<?php endif; ?>">
      <i class="ri-instagram-fill" style="color:#e1306c"></i> Instagram
    </a>
    <a href="/admin/appearance/blog?q=YouTube" class="filter-chip <?php if (($q ?? '') === 'YouTube'): ?>active<?php endif; ?>">
      <i class="ri-youtube-fill" style="color:#ff0000"></i> YouTube
    </a>
    <a href="/admin/appearance/blog?q=การตลาด" class="filter-chip <?php if (($q ?? '') === 'การตลาด'): ?>active<?php endif; ?>">
      <i class="ri-line-chart-line" style="color:#38bdf8"></i> การตลาดออนไลน์
    </a>
    <a href="/admin/appearance/blog?q=ปั้มไลค์" class="filter-chip <?php if (($q ?? '') === 'ปั้มไลค์'): ?>active<?php endif; ?>">
      <i class="ri-thumb-up-fill" style="color:#f59e0b"></i> ปั้มไลค์
    </a>
    <a href="/admin/appearance/blog?q=SMM" class="filter-chip <?php if (($q ?? '') === 'SMM'): ?>active<?php endif; ?>">
      <i class="ri-server-line" style="color:#a855f7"></i> SMM Panel
    </a>
  </div>
</div>

<!-- Add / Edit Article Drawer Form -->
<div class="blog-form-card" id="blog-form-section" style="<?php if (!empty($show_form)): ?>display:block<?php else: ?>display:none<?php endif; ?>">
  <div class="blog-form-head">
    <div style="display:flex;align-items:center;gap:12px">
      <div class="form-badge-icon">
        <i class="<?php if (!empty($editing)): ?>ri-edit-2-line<?php else: ?>ri-edit-box-line<?php endif; ?>"></i>
      </div>
      <div>
        <h3 style="margin:0;font-size:1.15rem;color:#f8fafc">
          <?php if (!empty($editing)): ?>แก้ไขบทความ: <?= htmlspecialchars((string)($editing['title'] ?? '')) ?><?php else: ?>เขียนบทความใหม่ (New Blog Article)<?php endif; ?>
        </h3>
        <p class="la-muted" style="margin:3px 0 0;font-size:13px">
          สร้างเนื้อหาคุณภาพสำหรับ Search Engine, ลูกค้า และการตลาดโซเชียลมีเดีย
        </p>
      </div>
    </div>
    <button type="button" class="blog-close-btn" onclick="toggleBlogForm(false)" title="ปิดฟอร์ม">
      <i class="ri-close-line"></i>
    </button>
  </div>

  <form method="post" action="/admin/appearance/blog" onsubmit="return validateBlogForm(this)">
    <input type="hidden" name="pid" id="blogPid" value="<?= !empty($editing['id']) ? htmlspecialchars((string)$editing['id']) : '' ?>">
    
    <div class="blog-editor-grid">
      <!-- Main Content Column -->
      <div class="blog-main-col">
        <!-- Title -->
        <div class="field-item">
          <label class="la-field" for="blogTitle">
            <span>หัวข้อบทความ (Title)</span> <span style="color:#ef4444">*</span>
          </label>
          <input class="la-input" name="title" id="blogTitle" value="<?= !empty($editing['title']) ? htmlspecialchars((string)$editing['title']) : '' ?>" placeholder="เช่น 10 เทคนิคเพิ่มยอด Reach และ Engagement บน Facebook ปี 2026" required oninput="autoSuggestSlug(this.value)">
          <span class="field-hint">ชื่อเรื่องที่ดึงดูดสายตาและมีคีย์เวิร์ดที่คนค้นหาบ่อย</span>
        </div>

        <!-- Slug & Live URL Preview -->
        <div class="field-item">
          <label class="la-field" for="blogSlug">
            <span>สลัก URL (Slug)</span>
          </label>
          <input class="la-input" name="slug" id="blogSlug" value="<?= !empty($editing['slug']) ? htmlspecialchars((string)$editing['slug']) : '' ?>" placeholder="facebook-reach-tips-2026" oninput="updateSlugPreview(this.value)">
          <div class="slug-live-preview">
            <span>ที่อยู่บทความจริง:</span>
            <code id="slug-preview-text">https://likes-auto.com/blog/<?= !empty($editing['slug']) ? htmlspecialchars((string)$editing['slug']) : '...' ?></code>
          </div>
        </div>

        <!-- Tags & Preset Chips -->
        <div class="field-item">
          <label class="la-field" for="blogTags">
            <span>แท็กและหมวดหมู่ (คั่นด้วยจุลภาค)</span>
          </label>
          <input class="la-input" name="tags" id="blogTags" value="<?= !empty($editing['tags']) ? htmlspecialchars((string)$editing['tags']) : '' ?>" placeholder="Facebook, เพิ่มไลค์, การตลาดออนไลน์">
          
          <div class="preset-tag-chips">
            <span style="font-size:12px;color:#64748b;align-self:center;margin-right:4px">+ คลิกเพื่อเพิ่มแท็ก:</span>
            <button type="button" class="ptag-chip" onclick="blogAddTag('Facebook')"><i class="ri-facebook-circle-fill" style="color:#1877f2"></i> Facebook</button>
            <button type="button" class="ptag-chip" onclick="blogAddTag('TikTok')"><i class="ri-tiktok-fill"></i> TikTok</button>
            <button type="button" class="ptag-chip" onclick="blogAddTag('Instagram')"><i class="ri-instagram-fill" style="color:#e1306c"></i> Instagram</button>
            <button type="button" class="ptag-chip" onclick="blogAddTag('YouTube')"><i class="ri-youtube-fill" style="color:#ff0000"></i> YouTube</button>
            <button type="button" class="ptag-chip" onclick="blogAddTag('ปั้มไลค์')">ปั้มไลค์</button>
            <button type="button" class="ptag-chip" onclick="blogAddTag('ปั้มฟอล')">ปั้มฟอล</button>
            <button type="button" class="ptag-chip" onclick="blogAddTag('ปั้มวิว')">ปั้มวิว</button>
            <button type="button" class="ptag-chip" onclick="blogAddTag('การตลาด')">การตลาด</button>
            <button type="button" class="ptag-chip" onclick="blogAddTag('ยิงแอด')">ยิงแอด</button>
            <button type="button" class="ptag-chip" onclick="blogAddTag('SEO')">SEO</button>
            <button type="button" class="ptag-chip" onclick="blogAddTag('พร้อมเพย์')">พร้อมเพย์</button>
          </div>
        </div>

        <!-- Excerpt -->
        <div class="field-item">
          <label class="la-field" for="blogExcerpt">
            <span>คำโปรยสรุปย่อ (Excerpt)</span>
          </label>
          <input class="la-input" name="excerpt" id="blogExcerpt" value="<?= !empty($editing['excerpt']) ? htmlspecialchars((string)$editing['excerpt']) : '' ?>" placeholder="สรุปเนื้อหาสั้นๆ 1-2 ประโยคสำหรับแสดงบนการ์ดและผลการค้นหา Google">
          <span class="field-hint">หากเว้นว่างไว้ ระบบจะตัดเนื้อหาย่อหน้าแรกไปเป็นคำโปรยให้อัตโนมัติ</span>
        </div>

        <!-- Editor with Formatting Toolbar -->
        <div class="field-item" style="margin-bottom:0">
          <label class="la-field" for="blogBody">
            <span>เนื้อหาบทความ (HTML / Text)</span> <span style="color:#ef4444">*</span>
          </label>
          
          <div class="format-toolbar">
            <button type="button" class="format-btn" onclick="insertFormat('<h3>','</h3>','หัวข้อย่อย H3')" title="หัวข้อย่อย"><b>H3</b></button>
            <button type="button" class="format-btn" onclick="insertFormat('<p>','</p>','ข้อความย่อหน้า')" title="ย่อหน้า"><i class="ri-paragraph"></i> P</button>
            <button type="button" class="format-btn" onclick="insertFormat('<strong>','</strong>','ข้อความหนา')" title="ตัวหนา"><b>B</b></button>
            <button type="button" class="format-btn" onclick="insertFormat('<em>','</em>','ข้อความเอียง')" title="ตัวเอียง"><i>I</i></button>
            <button type="button" class="format-btn" onclick="blogLinkPrompt()" title="แทรก URL ลิงก์"><i class="ri-link"></i> ลิงก์</button>
            <button type="button" class="format-btn" onclick="insertFormat('<ul>\n  <li>','</li>\n  <li>รายการ</li>\n</ul>','ประเด็นสำคัญ')" title="รายการแบบจุด"><i class="ri-list-unordered"></i> รายการ</button>
            <button type="button" class="format-btn" onclick="insertFormat('<div class=\"blog-callout\">\n  <strong>💡 เคล็ดลับจาก LIKES AUTO:</strong> ','\n</div>','คำแนะนำสำคัญ')" title="กล่องไฮไลต์ข้อความ"><i class="ri-lightbulb-line"></i> กล่องทริค</button>
            <button type="button" class="format-btn" onclick="blogImgPrompt()" title="แทรกรูปลิงก์ภายนอก"><i class="ri-image-line"></i> ใส่รูป</button>
          </div>

          <textarea class="la-input blog-textarea" name="body" id="blogBody" placeholder="เขียนเนื้อหาบทความที่นี่..." oninput="updateWordCount()"><?= !empty($editing['body']) ? htmlspecialchars((string)$editing['body']) : '' ?></textarea>
          
          <div class="textarea-footer">
            <span id="word-counter">0 ตัวอักษร · 0 คำ</span>
            <span id="reading-time">เวลาอ่านโดยประมาณ: ~1 นาที</span>
          </div>
        </div>
      </div>

      <!-- Settings Sidebar Column -->
      <div class="blog-sidebar-col">
        <!-- Publishing Status -->
        <div class="blog-side-box">
          <div class="blog-side-title"><i class="ri-settings-4-line" style="color:#38bdf8"></i> การตั้งค่าเผยแพร่</div>
          
          <label class="adm-check" style="margin-bottom:14px;display:flex;align-items:center;gap:10px;cursor:pointer">
            <input type="checkbox" name="published" value="1" <?php if (empty($editing) || (isset($editing['published']) && $editing['published'] != 0)): ?>checked<?php endif; ?> style="width:18px;height:18px">
            <div>
              <strong style="color:#f8fafc;display:block">เผยแพร่บนเว็บทันที</strong>
              <span style="font-size:12px;color:#94a3b8">เปิดให้ผู้ใช้งานทั่วไปสามารถเข้าอ่านได้</span>
            </div>
          </label>

          <div class="field-item" style="margin-bottom:0">
            <label class="la-field" for="blogCreated">วันเวลาที่ลงบทความ</label>
            <input class="la-input" name="created_at" id="blogCreated" value="<?= !empty($editing['created_at']) ? htmlspecialchars((string)$editing['created_at']) : '' ?>" placeholder="2026-11-04 10:00">
          </div>
        </div>

        <!-- Media Gallery -->
        <div class="blog-side-box">
          <div class="blog-side-title" style="justify-content:space-between">
            <span><i class="ri-gallery-line" style="color:#a855f7"></i> คลังภาพบทความ</span>
            <span style="font-size:11px;color:#64748b"><?= count($media ?? []) ?> ภาพ</span>
          </div>
          <p style="font-size:12px;color:#94a3b8;margin:0 0 10px">คลิกภาพเพื่อแทรกแท็กรูปภาพลงในตำแหน่งเคอร์เซอร์</p>
          
          <div class="blog-gallery-grid">
            <?php if (!empty($media)): foreach ($media as $src): ?>
            <button type="button" class="blog-thumb-btn" onclick="blogImg('<?= htmlspecialchars((string)$src) ?>')" title="<?= htmlspecialchars((string)$src) ?>">
              <img src="<?= htmlspecialchars((string)$src) ?>" alt="" loading="lazy">
            </button>
            <?php endforeach; else: ?>
            <p class="la-muted" style="grid-column:1/-1;text-align:center;padding:15px">ยังไม่มีภาพในคลัง</p>
            <?php endif; ?>
          </div>
        </div>

        <!-- Quick Upload Image -->
        <div class="blog-side-box" style="margin-bottom:0">
          <div class="blog-side-title"><i class="ri-upload-cloud-line" style="color:#22c55e"></i> อัปโหลดรูปภาพใหม่</div>
          <form method="post" action="/admin/appearance/blog/upload" enctype="multipart/form-data" style="margin:0">
            <input type="hidden" name="pid" value="<?= !empty($editing['id']) ? htmlspecialchars((string)$editing['id']) : '' ?>">
            <input class="la-input" type="file" name="upload" accept="image/*" required style="padding:6px;font-size:12px;margin-bottom:8px">
            <button class="la-btn la-btn-mini la-btn-ghost" type="submit" style="width:100%;justify-content:center">
              <i class="ri-upload-2-line"></i> อัปโหลดเข้าบทความ
            </button>
          </form>
        </div>
      </div>
    </div>

    <!-- Form Footer Actions -->
    <div class="adm-actions" style="margin-top:22px;padding-top:16px;border-top:1px solid rgba(255,255,255,0.08);display:flex;align-items:center;gap:10px">
      <button class="la-btn la-btn-primary" type="submit" style="padding:10px 24px;font-size:14px">
        <i class="ri-save-line"></i> <?php if (!empty($editing)): ?>บันทึกการแก้ไข<?php else: ?>บันทึกและเผยแพร่บทความ<?php endif; ?>
      </button>
      <button type="button" class="la-btn la-btn-ghost" onclick="toggleBlogForm(false)">ยกเลิก</button>
      
      <?php if (!empty($editing['slug'])): ?>
      <a class="la-btn la-btn-ghost" href="/blog/<?= htmlspecialchars((string)$editing['slug']) ?>" target="_blank" rel="noopener" style="margin-left:auto">
        <i class="ri-external-link-line"></i> เปิดดูบนหน้าเว็บจริง
      </a>
      <?php endif; ?>
    </div>
  </form>
</div>

<!-- 1. Rich Blog Cards View (Active by default) -->
<div class="blog-cards-grid" id="blog-cards-view">
  <?php if (!empty($posts)): foreach ($posts as $r): ?>
  <div class="blog-card-item">
    <!-- Card Cover -->
    <div class="blog-card-cover-wrap">
      <span class="card-id-pill">#<?= htmlspecialchars((string)($r['id'] ?? '')) ?></span>
      <div class="blog-badge-overlay">
        <?php if (isset($r['published']) && (int)$r['published'] === 0): ?>
        <span class="status-pill draft"><i class="ri-draft-line"></i> ฉบับร่าง</span>
        <?php else: ?>
        <span class="status-pill published"><i class="ri-checkbox-circle-fill"></i> เผยแพร่</span>
        <?php endif; ?>
      </div>
      <?php if (!empty($r['cover'])): ?>
      <img class="blog-card-cover" src="<?= htmlspecialchars((string)$r['cover']) ?>" alt="<?= htmlspecialchars((string)($r['title'] ?? '')) ?>" loading="lazy">
      <?php else: ?>
      <div class="blog-card-fallback-cover">
        <i class="ri-article-line"></i>
      </div>
      <?php endif; ?>
    </div>

    <!-- Card Content -->
    <div class="blog-card-content">
      <div class="blog-card-tags">
        <?php if (!empty($r['tags'])): 
          $tArr = explode(',', (string)$r['tags']);
          foreach ($tArr as $t): 
            $t = trim($t);
            if ($t !== ''):
        ?>
          <span class="tag-badge"><?= htmlspecialchars($t) ?></span>
        <?php endif; endforeach; else: ?>
          <span class="tag-badge" style="background:rgba(255,255,255,0.05);color:#94a3b8">บทความทั่วไป</span>
        <?php endif; ?>
      </div>

      <a href="/blog/<?= htmlspecialchars((string)($r['slug'] ?? $r['id'] ?? '')) ?>" target="_blank" rel="noopener" style="text-decoration:none">
        <h4 class="blog-card-title" title="<?= htmlspecialchars((string)($r['title'] ?? '')) ?>"><?= htmlspecialchars((string)($r['title'] ?? '')) ?></h4>
      </a>

      <div class="blog-card-url">
        <i class="ri-link" style="color:#64748b"></i>
        <code>/blog/<?= htmlspecialchars((string)($r['slug'] ?? $r['id'] ?? '')) ?></code>
        <button type="button" class="la-btn la-btn-mini la-btn-ghost" style="padding:2px 6px;height:auto" onclick="copyBlogUrl('https://likes-auto.com/blog/<?= htmlspecialchars((string)($r['slug'] ?? $r['id'] ?? '')) ?>', this)" title="คัดลอกลิงก์">
          <i class="ri-file-copy-line"></i>
        </button>
      </div>

      <p class="blog-card-excerpt">
        <?= htmlspecialchars((string)($r['excerpt'] ?? 'บทความคุณภาพจาก LIKES AUTO ผู้ให้บริการระบบการตลาดโซเชียลมีเดียอันดับ 1 ในไทย')) ?>
      </p>

      <div class="blog-card-meta">
        <span><i class="ri-calendar-line"></i> <?= htmlspecialchars((string)($r['created_at'] ?? 'เพิ่งอัปเดต')) ?></span>
        <span><i class="ri-time-line"></i> อ่าน ~2 นาที</span>
      </div>
    </div>

    <!-- Card Actions Footer -->
    <div class="blog-card-actions">
      <a class="la-btn la-btn-mini la-btn-primary" href="/blog/<?= htmlspecialchars((string)($r['slug'] ?? $r['id'] ?? '')) ?>" target="_blank" rel="noopener" title="เปิดดูหน้าจริง">
        <i class="ri-external-link-line"></i> เปิด
      </a>
      <a class="la-btn la-btn-mini la-btn-ghost" href="/admin/appearance/blog?edit=<?= htmlspecialchars((string)($r['id'] ?? '')) ?>" title="แก้ไขบทความ">
        <i class="ri-edit-line"></i> แก้
      </a>
      <form method="post" action="/admin/appearance/blog/<?= htmlspecialchars((string)($r['id'] ?? '')) ?>/toggle" style="margin:0;flex:1;display:flex">
        <button class="la-btn la-btn-mini la-btn-ghost" type="submit" style="width:100%" title="สลับสถานะ">
          <?php if (isset($r['published']) && (int)$r['published'] === 0): ?><i class="ri-eye-line"></i> แสดง<?php else: ?><i class="ri-eye-off-line"></i> ซ่อน<?php endif; ?>
        </button>
      </form>
      <form method="post" action="/admin/appearance/blog/<?= htmlspecialchars((string)($r['id'] ?? '')) ?>/copy" style="margin:0">
        <button class="la-btn la-btn-mini la-btn-ghost" type="submit" title="ทำสำเนาบทความ">
          <i class="ri-file-copy-line"></i>
        </button>
      </form>
      <form method="post" action="/admin/appearance/blog/<?= htmlspecialchars((string)($r['id'] ?? '')) ?>/delete" onsubmit="return confirm('ยืนยันลบบทความ <?= htmlspecialchars((string)($r['title'] ?? '')) ?> ถาวร?')" style="margin:0">
        <button class="la-btn la-btn-mini la-btn-danger" type="submit" title="ลบถาวร">
          <i class="ri-delete-bin-line"></i>
        </button>
      </form>
    </div>
  </div>
  <?php endforeach; else: ?>
  <div style="grid-column:1/-1;text-align:center;padding:50px 20px;background:rgba(15,23,42,0.5);border:1px dashed rgba(255,255,255,0.1);border-radius:14px">
    <i class="ri-file-search-line" style="font-size:42px;color:#64748b"></i>
    <h4 style="margin:12px 0 6px;color:#f8fafc">ไม่พบบทความ<?php if (!empty($q)): ?> ที่ตรงกับคำค้น "<?= htmlspecialchars((string)$q) ?>"<?php endif; ?></h4>
    <p class="la-muted" style="margin-bottom:16px">ลองค้นหาด้วยคำอื่น หรือกดปุ่มเขียนบทความใหม่ด้านบน</p>
    <a href="/admin/appearance/blog" class="la-btn la-btn-ghost">ดูบทความทั้งหมด</a>
  </div>
  <?php endif; ?>
</div>

<!-- 2. Detailed Table View (Hidden by default, toggleable) -->
<div class="adm-table-wrap" id="blog-table-view" style="display:none;margin-bottom:30px">
  <table class="adm-table">
    <thead>
      <tr>
        <th style="width:70px">ID</th>
        <th>บทความ</th>
        <th>แท็ก / หมวดหมู่</th>
        <th>สถานะ</th>
        <th>วันที่สร้าง</th>
        <th style="text-align:right">จัดการ</th>
      </tr>
    </thead>
    <tbody>
      <?php if (!empty($posts)): foreach ($posts as $r): ?>
      <tr>
        <td><span class="card-id-pill" style="position:static">#<?= htmlspecialchars((string)($r['id'] ?? '')) ?></span></td>
        <td class="wrap">
          <div style="display:flex;align-items:center">
            <?php if (!empty($r['cover'])): ?>
            <img class="blog-table-cover" src="<?= htmlspecialchars((string)$r['cover']) ?>" alt="">
            <?php endif; ?>
            <div>
              <strong style="color:#f8fafc;display:block"><?= htmlspecialchars((string)($r['title'] ?? '')) ?></strong>
              <code style="font-size:11px;color:#38bdf8">/blog/<?= htmlspecialchars((string)($r['slug'] ?? $r['id'] ?? '')) ?></code>
            </div>
          </div>
        </td>
        <td class="wrap">
          <?php if (!empty($r['tags'])): 
            $tArr = explode(',', (string)$r['tags']);
            foreach ($tArr as $t): 
              $t = trim($t);
              if ($t !== ''):
          ?>
            <span class="tag-badge" style="font-size:10px"><?= htmlspecialchars($t) ?></span>
          <?php endif; endforeach; else: ?>
            <span class="la-muted">-</span>
          <?php endif; ?>
        </td>
        <td>
          <?php if (isset($r['published']) && (int)$r['published'] === 0): ?>
          <span class="status-pill draft"><i class="ri-draft-line"></i> ฉบับร่าง</span>
          <?php else: ?>
          <span class="status-pill published"><i class="ri-checkbox-circle-fill"></i> เผยแพร่</span>
          <?php endif; ?>
        </td>
        <td style="font-size:12px;color:#94a3b8"><?= htmlspecialchars((string)($r['created_at'] ?? '')) ?></td>
        <td>
          <div class="adm-actions" style="justify-content:flex-end">
            <a class="la-btn la-btn-mini" href="/blog/<?= htmlspecialchars((string)($r['slug'] ?? $r['id'] ?? '')) ?>" target="_blank" rel="noopener"><i class="ri-external-link-line"></i></a>
            <a class="la-btn la-btn-mini la-btn-ghost" href="/admin/appearance/blog?edit=<?= htmlspecialchars((string)($r['id'] ?? '')) ?>"><i class="ri-edit-line"></i></a>
            <form method="post" action="/admin/appearance/blog/<?= htmlspecialchars((string)($r['id'] ?? '')) ?>/toggle" style="display:inline">
              <button class="la-btn la-btn-mini la-btn-ghost" type="submit"><?php if (isset($r['published']) && (int)$r['published'] === 0): ?>แสดง<?php else: ?>ซ่อน<?php endif; ?></button>
            </form>
            <form method="post" action="/admin/appearance/blog/<?= htmlspecialchars((string)($r['id'] ?? '')) ?>/copy" style="display:inline">
              <button class="la-btn la-btn-mini la-btn-ghost" type="submit" title="ทำสำเนา"><i class="ri-file-copy-line"></i></button>
            </form>
            <form method="post" action="/admin/appearance/blog/<?= htmlspecialchars((string)($r['id'] ?? '')) ?>/delete" onsubmit="return confirm('ยืนยันลบ?')" style="display:inline">
              <button class="la-btn la-btn-mini la-btn-danger" type="submit"><i class="ri-delete-bin-line"></i></button>
            </form>
          </div>
        </td>
      </tr>
      <?php endforeach; else: ?>
      <tr><td colspan="6" style="text-align:center;padding:30px">ยังไม่มีบทความในระบบ</td></tr>
      <?php endif; ?>
    </tbody>
  </table>
</div>

<!-- Operational & SEO Strategy Guide Cards -->
<div class="blog-guide-grid">
  <div class="blog-guide-card">
    <div class="guide-icon"><i class="ri-search-2-line"></i></div>
    <div>
      <h4>กลยุทธ์ Social SEO & Search Engine</h4>
      <p>การใส่คีย์เวิร์ดในหัวข้อ ย่อหน้าแรก และแท็ก จะช่วยให้บทความติดอันดับหน้าแรกของการค้นหาบน Google, TikTok และ Instagram ดึงดูดลูกค้าเป้าหมายเข้ามาอย่างต่อเนื่องโดยไม่ต้องเสียเงินยิงแอด</p>
    </div>
  </div>
  <div class="blog-guide-card">
    <div class="guide-icon"><i class="ri-links-line"></i></div>
    <div>
      <h4>การทำ Internal Link เชื่อมโยงบริการ</h4>
      <p>ในทุกบทความควรมีการแทรกลิงก์แนะนำบริการ เช่น ลิงก์ไปยังหน้า <a href="/services" style="color:#60a5fa">บริการทั้งหมด (/services)</a> หรือ <a href="/faq" style="color:#60a5fa">คำถามที่พบบ่อย (/faq)</a> เพื่อเปลี่ยนผู้อ่านให้กลายเป็นลูกค้าสั่งซื้อทันที</p>
    </div>
  </div>
</div>

<script>
function blogBody() { return document.getElementById("blogBody"); }

function toggleBlogForm(show) {
  var formSec = document.getElementById("blog-form-section");
  if (!formSec) return;
  if (show === undefined) {
    show = formSec.style.display === "none";
  }
  formSec.style.display = show ? "block" : "none";
  if (show) {
    formSec.scrollIntoView({ behavior: 'smooth', block: 'start' });
    var tInp = document.getElementById("blogTitle");
    if (tInp && !tInp.value) tInp.focus();
  }
}

function setBlogViewMode(mode) {
  var cardsView = document.getElementById("blog-cards-view");
  var tableView = document.getElementById("blog-table-view");
  var btnCards = document.getElementById("view-card-btn");
  var btnTable = document.getElementById("view-table-btn");
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

function autoSuggestSlug(title) {
  var sInp = document.getElementById("blogSlug");
  if (!sInp || sInp.getAttribute('data-touched') === 'true') return;
  if (!title) { updateSlugPreview(''); return; }
  var slug = title.toLowerCase().trim()
    .replace(/[^\w\s\u0E00-\u0E7F-]/g, '')
    .replace(/[\s_-]+/g, '-')
    .replace(/^-+|-+$/g, '');
  sInp.value = slug;
  updateSlugPreview(slug);
}

function updateSlugPreview(val) {
  var preview = document.getElementById("slug-preview-text");
  if (preview) {
    var clean = (val || '').trim();
    preview.textContent = 'https://likes-auto.com/blog/' + (clean || '...');
  }
}

function copyBlogUrl(url, btn) {
  navigator.clipboard.writeText(url).then(function() {
    var orig = btn.innerHTML;
    btn.innerHTML = '<i class="ri-check-line" style="color:#22c55e"></i>';
    setTimeout(function() { btn.innerHTML = orig; }, 1500);
  });
}

function blogAddTag(tag) {
  var el = document.getElementById("blogTags");
  if (!el) return;
  var cur = (el.value || "").split(",").map(function(x){ return x.trim(); }).filter(Boolean);
  if (cur.indexOf(tag) < 0) cur.push(tag);
  el.value = cur.join(", ");
}

function insertFormat(openTag, closeTag, placeholder) {
  var t = blogBody();
  if (!t) return;
  var s = t.selectionStart, e = t.selectionEnd;
  var sel = t.value.substring(s, e) || placeholder;
  t.value = t.value.slice(0, s) + openTag + sel + closeTag + t.value.slice(e);
  t.focus();
  t.setSelectionRange(s + openTag.length, s + openTag.length + sel.length);
  updateWordCount();
}

function blogLinkPrompt() {
  var href = prompt("กรอกที่อยู่ URL ลิงก์ปลายทาง:", "/services");
  if (!href) return;
  insertFormat('<a href="' + href + '">', '</a>', 'ข้อความลิงก์');
}

function blogImg(src) {
  if (!src) return;
  var t = document.getElementById("blogTitle");
  var alt = t ? t.value : "ภาพประกอบบทความ";
  var html = '\n<figure class="la-blog-fig">\n  <img src="' + src + '" alt="' + alt + '" width="1280" height="720" loading="lazy">\n</figure>\n';
  var box = blogBody();
  if (!box) return;
  box.value = box.value + html;
  box.focus();
  updateWordCount();
}

function blogImgPrompt() {
  var src = prompt("ระบุที่อยู่รูปภาพ URL:", "/static/assets/blog/blog-likes.jpg");
  if (src) blogImg(src);
}

function updateWordCount() {
  var t = blogBody();
  var counter = document.getElementById("word-counter");
  var reading = document.getElementById("reading-time");
  if (!t || !counter) return;
  var val = t.value || '';
  var chars = val.length;
  var words = val.trim() ? val.trim().split(/\s+/).length : 0;
  counter.textContent = chars.toLocaleString() + ' ตัวอักษร · ' + words.toLocaleString() + ' คำ';
  if (reading) {
    var mins = Math.max(1, Math.round(words / 200));
    reading.textContent = 'เวลาอ่านโดยประมาณ: ~' + mins + ' นาที';
  }
}

function validateBlogForm(form) {
  var title = form.title ? form.title.value.trim() : '';
  if (!title) {
    alert('กรุณากรอกหัวข้อบทความ (Title)');
    return false;
  }
  return true;
}

document.addEventListener('DOMContentLoaded', function() {
  var sInp = document.getElementById("blogSlug");
  if (sInp) {
    sInp.addEventListener('input', function() {
      sInp.setAttribute('data-touched', 'true');
    });
  }
  updateWordCount();
});
</script>
