<?php
/**
 * LIKES AUTO BLOG ADMIN - REORGANIZED & TIDY UI/UX 2026
 * Clean, organized, paginated, responsive article management system
 */
$allCount = count($posts);
$publishedCount = 0;
$draftCount = 0;
foreach ($posts as $p) {
    if (!empty($p['published'])) {
        $publishedCount++;
    } else {
        $draftCount++;
    }
}
$isEditing = !empty($editing);
$showForm = $isEditing || (!empty($show_form));
?>

<style>
/* ========================================================
   LIKES AUTO ORGANIZED BLOG ADMIN (TIDY & PROFESSIONAL UI)
   ======================================================== */

.blog-admin-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
  margin-top: 10px;
}

/* 1. Compact KPI Header */
.blog-kpi-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 14px;
}
.blog-kpi-box {
  background: linear-gradient(135deg, rgba(30, 41, 59, 0.75), rgba(15, 23, 42, 0.85));
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  padding: 14px 18px;
  display: flex;
  align-items: center;
  gap: 14px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
  cursor: pointer;
  transition: all 0.2s ease;
}
.blog-kpi-box:hover {
  transform: translateY(-2px);
  border-color: rgba(99, 102, 241, 0.4);
}
.blog-kpi-box.is-active {
  border-color: #3b82f6;
  background: linear-gradient(135deg, rgba(37, 99, 235, 0.15), rgba(15, 23, 42, 0.9));
}
.kpi-icon-mini {
  width: 44px;
  height: 44px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  flex-shrink: 0;
}
.kpi-icon-mini.blue { background: rgba(59, 130, 246, 0.15); color: #60a5fa; border: 1px solid rgba(59, 130, 246, 0.3); }
.kpi-icon-mini.green { background: rgba(16, 185, 129, 0.15); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.3); }
.kpi-icon-mini.amber { background: rgba(245, 158, 11, 0.15); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.3); }
.kpi-icon-mini.purple { background: rgba(168, 85, 247, 0.15); color: #c084fc; border: 1px solid rgba(168, 85, 247, 0.3); }
.kpi-info-mini { display: flex; flex-direction: column; }
.kpi-lbl-mini { font-size: 11.5px; color: #94a3b8; font-weight: 600; text-transform: uppercase; letter-spacing: 0.03em; }
.kpi-val-mini { font-size: 22px; font-weight: 800; color: #f8fafc; line-height: 1.2; }
.kpi-sub-mini { font-size: 11px; color: #64748b; }

/* 2. Organized Control & Filter Bar */
.blog-panel-card {
  background: rgba(18, 24, 38, 0.85);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 14px;
  padding: 16px 20px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);
}
.blog-toolbar-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
  padding-bottom: 14px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}
.blog-status-tabs {
  display: flex;
  gap: 6px;
  background: rgba(10, 14, 26, 0.6);
  padding: 4px;
  border-radius: 10px;
  border: 1px solid rgba(255, 255, 255, 0.06);
}
.blog-status-tab {
  padding: 7px 14px;
  border-radius: 8px;
  border: none;
  background: transparent;
  color: #94a3b8;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  transition: all 0.18s ease;
}
.blog-status-tab:hover {
  color: #fff;
  background: rgba(255, 255, 255, 0.05);
}
.blog-status-tab.is-active {
  background: #2563eb;
  color: #fff;
  box-shadow: 0 2px 10px rgba(37, 99, 235, 0.4);
}
.tab-badge {
  font-size: 11px;
  padding: 1px 6px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.18);
}

.blog-toolbar-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}
.view-switch-btns {
  display: flex;
  background: rgba(10, 14, 26, 0.6);
  padding: 3px;
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.06);
}
.view-btn {
  padding: 6px 10px;
  border: none;
  background: transparent;
  color: #94a3b8;
  border-radius: 6px;
  cursor: pointer;
  font-size: 12.5px;
  font-weight: 600;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  transition: all 0.18s ease;
}
.view-btn:hover { color: #fff; }
.view-btn.is-active {
  background: rgba(255, 255, 255, 0.12);
  color: #38bdf8;
}

/* Secondary Filter & Search Row */
.blog-toolbar-search {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
  padding-top: 14px;
}
.search-wrapper {
  position: relative;
  min-width: 280px;
  flex: 1;
  max-width: 440px;
}
.search-wrapper i {
  position: absolute;
  left: 12px;
  top: 50%;
  transform: translateY(-50%);
  color: #64748b;
  font-size: 15px;
}
.search-wrapper input {
  padding-left: 36px !important;
  height: 38px;
  font-size: 13.5px;
  background: rgba(15, 23, 42, 0.7) !important;
  border: 1px solid rgba(255, 255, 255, 0.1) !important;
  border-radius: 8px !important;
  color: #f8fafc !important;
  width: 100%;
}
.search-wrapper input:focus {
  border-color: #3b82f6 !important;
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.25) !important;
}

.category-chips-row {
  display: flex;
  align-items: center;
  gap: 6px;
  overflow-x: auto;
  scrollbar-width: none;
  padding: 2px 0;
}
.category-chips-row::-webkit-scrollbar { display: none; }
.cat-chip {
  padding: 5px 11px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
  font-size: 12px;
  font-weight: 500;
  color: #94a3b8;
  cursor: pointer;
  white-space: nowrap;
  display: inline-flex;
  align-items: center;
  gap: 5px;
  transition: all 0.18s ease;
}
.cat-chip:hover, .cat-chip.is-active {
  background: rgba(59, 130, 246, 0.15);
  border-color: rgba(59, 130, 246, 0.4);
  color: #60a5fa;
}

/* 3. Editor Drawer Form */
.blog-editor-drawer {
  background: linear-gradient(135deg, rgba(22, 28, 45, 0.95), rgba(15, 23, 42, 0.98));
  border: 1px solid rgba(59, 130, 246, 0.3);
  border-radius: 14px;
  padding: 22px;
  box-shadow: 0 10px 35px rgba(0, 0, 0, 0.4);
  position: relative;
  overflow: hidden;
  margin-bottom: 20px;
}
.blog-editor-drawer::before {
  content: "";
  position: absolute;
  top: 0; left: 0; right: 0; height: 3px;
  background: linear-gradient(90deg, #3b82f6, #10b981, #f59e0b);
}
.drawer-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
  padding-bottom: 14px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}
.drawer-title-group h3 {
  margin: 0 0 4px;
  font-size: 1.15rem;
  font-weight: 700;
  color: #fff;
  display: flex;
  align-items: center;
  gap: 8px;
}
.drawer-title-group p {
  margin: 0;
  font-size: 13px;
  color: #94a3b8;
}
.drawer-close-btn {
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: #cbd5e1;
  padding: 6px 12px;
  border-radius: 8px;
  font-size: 13px;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  transition: all 0.18s ease;
}
.drawer-close-btn:hover {
  background: rgba(239, 68, 68, 0.15);
  border-color: rgba(239, 68, 68, 0.4);
  color: #f87171;
}

.editor-grid-2col {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 24px;
}
@media (max-width: 900px) {
  .editor-grid-2col { grid-template-columns: 1fr; }
}

/* 4. Table View (Clean, Tidy, Super Organized) */
.blog-table-container {
  overflow-x: auto;
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  background: rgba(15, 23, 42, 0.6);
}
.blog-tidy-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13.5px;
  text-align: left;
}
.blog-tidy-table th {
  background: rgba(30, 41, 59, 0.8);
  color: #94a3b8;
  font-weight: 600;
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  padding: 12px 14px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  white-space: nowrap;
}
.blog-tidy-table td {
  padding: 12px 14px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  color: #cbd5e1;
  vertical-align: middle;
}
.blog-tidy-table tr:hover td {
  background: rgba(255, 255, 255, 0.03);
}

.cell-thumb {
  width: 52px;
  height: 34px;
  border-radius: 6px;
  object-fit: cover;
  background: #1e293b;
  display: block;
}
.cell-title-wrap {
  display: flex;
  flex-direction: column;
  gap: 3px;
  max-width: 440px;
}
.cell-title-link {
  color: #f8fafc;
  font-weight: 600;
  font-size: 14px;
  text-decoration: none;
  line-height: 1.35;
  display: inline;
}
.cell-title-link:hover {
  color: #38bdf8;
  text-decoration: underline;
}
.cell-slug {
  font-size: 11.5px;
  color: #64748b;
  display: flex;
  align-items: center;
  gap: 4px;
}
.cell-slug code {
  color: #38bdf8;
  background: transparent;
  padding: 0;
}

.status-pill {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 11.5px;
  font-weight: 700;
  padding: 3px 9px;
  border-radius: 999px;
  white-space: nowrap;
}
.status-pill.published {
  background: rgba(16, 185, 129, 0.15);
  color: #34d399;
  border: 1px solid rgba(16, 185, 129, 0.3);
}
.status-pill.draft {
  background: rgba(245, 158, 11, 0.15);
  color: #fbbf24;
  border: 1px solid rgba(245, 158, 11, 0.3);
}
.tag-pill {
  display: inline-block;
  font-size: 11px;
  padding: 2px 7px;
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.06);
  color: #94a3b8;
  margin: 1px;
}

.action-btn-group {
  display: flex;
  align-items: center;
  gap: 6px;
  white-space: nowrap;
}
.btn-act {
  padding: 5px 9px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
  text-decoration: none !important;
  cursor: pointer;
  border: 1px solid transparent;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  transition: all 0.15s ease;
}
.btn-act.edit {
  background: rgba(59, 130, 246, 0.12);
  border-color: rgba(59, 130, 246, 0.3);
  color: #60a5fa;
}
.btn-act.edit:hover { background: #2563eb; color: #fff; }
.btn-act.view {
  background: rgba(255, 255, 255, 0.05);
  border-color: rgba(255, 255, 255, 0.1);
  color: #94a3b8;
}
.btn-act.view:hover { background: rgba(255, 255, 255, 0.12); color: #fff; }
.btn-act.del {
  background: rgba(239, 68, 68, 0.1);
  border-color: rgba(239, 68, 68, 0.25);
  color: #f87171;
}
.btn-act.del:hover { background: #dc2626; color: #fff; }

/* 5. Cards View (Structured 3-column Grid) */
.blog-cards-grid-tidy {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 16px;
}
.blog-card-item-tidy {
  background: linear-gradient(135deg, rgba(30, 41, 59, 0.7), rgba(15, 23, 42, 0.85));
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  transition: all 0.2s ease;
}
.blog-card-item-tidy:hover {
  transform: translateY(-2px);
  border-color: rgba(59, 130, 246, 0.4);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
}
.card-thumb-wrap {
  width: 100%;
  aspect-ratio: 16/9;
  background: #0f172a;
  position: relative;
  overflow: hidden;
}
.card-thumb-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.3s ease;
}
.blog-card-item-tidy:hover .card-thumb-img {
  transform: scale(1.03);
}
.card-id-badge {
  position: absolute;
  top: 10px;
  left: 10px;
  background: rgba(0, 0, 0, 0.75);
  backdrop-filter: blur(4px);
  color: #fff;
  font-size: 11px;
  font-weight: 700;
  padding: 3px 8px;
  border-radius: 6px;
  border: 1px solid rgba(255, 255, 255, 0.15);
}
.card-status-badge {
  position: absolute;
  top: 10px;
  right: 10px;
}
.card-content-tidy {
  padding: 14px;
  display: flex;
  flex-direction: column;
  flex: 1;
}
.card-title-tidy {
  font-size: 14.5px;
  font-weight: 700;
  color: #f8fafc;
  line-height: 1.4;
  margin: 0 0 6px;
}
.card-url-tidy {
  font-size: 11.5px;
  color: #38bdf8;
  margin-bottom: 10px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.card-footer-tidy {
  margin-top: auto;
  padding-top: 10px;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
  display: flex;
  align-items: center;
  justify-content: space-between;
}

/* 6. Smart Pagination Bar */
.blog-pagination-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
  padding: 14px 18px;
  background: rgba(15, 23, 42, 0.8);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  font-size: 13px;
  color: #94a3b8;
}
.pagination-controls {
  display: flex;
  align-items: center;
  gap: 4px;
}
.page-btn {
  min-width: 32px;
  height: 32px;
  padding: 0 8px;
  border-radius: 6px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  background: rgba(255, 255, 255, 0.04);
  color: #cbd5e1;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s ease;
}
.page-btn:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
}
.page-btn.is-active {
  background: #2563eb;
  border-color: #3b82f6;
  color: #fff;
  box-shadow: 0 2px 8px rgba(37, 99, 235, 0.4);
}
.page-btn:disabled {
  opacity: 0.35;
  cursor: not-allowed;
}

/* Media Thumbnails Mini Grid */
.media-mini-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(70px, 1fr));
  gap: 6px;
  max-height: 160px;
  overflow-y: auto;
  padding: 4px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 8px;
  background: rgba(0, 0, 0, 0.2);
}
.media-mini-thumb {
  aspect-ratio: 16/9;
  border-radius: 4px;
  overflow: hidden;
  border: 1px solid rgba(255, 255, 255, 0.1);
  cursor: pointer;
  transition: transform 0.15s ease, border-color 0.15s ease;
}
.media-mini-thumb:hover {
  transform: scale(1.05);
  border-color: #38bdf8;
}
.media-mini-thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}
</style>

<div class="blog-admin-container">

  <!-- 1. Compact KPI Header -->
  <div class="blog-kpi-row">
    <div class="blog-kpi-box is-active" onclick="filterByStatus('all', this)">
      <div class="kpi-icon-mini blue"><i class="ri-article-line"></i></div>
      <div class="kpi-info-mini">
        <span class="kpi-lbl-mini">บทความทั้งหมด</span>
        <span class="kpi-val-mini"><?= $allCount ?></span>
        <span class="kpi-sub-mini">ในฐานข้อมูลระบบ</span>
      </div>
    </div>

    <div class="blog-kpi-box" onclick="filterByStatus('published', this)">
      <div class="kpi-icon-mini green"><i class="ri-checkbox-circle-line"></i></div>
      <div class="kpi-info-mini">
        <span class="kpi-lbl-mini">เผยแพร่แล้ว (Live)</span>
        <span class="kpi-val-mini" style="color:#34d399"><?= $publishedCount ?></span>
        <span class="kpi-sub-mini">พร้อมขึ้น Google</span>
      </div>
    </div>

    <div class="blog-kpi-box" onclick="filterByStatus('draft', this)">
      <div class="kpi-icon-mini amber"><i class="ri-draft-line"></i></div>
      <div class="kpi-info-mini">
        <span class="kpi-lbl-mini">ฉบับร่าง (Draft)</span>
        <span class="kpi-val-mini" style="color:#fbbf24"><?= $draftCount ?></span>
        <span class="kpi-sub-mini">รอตรวจสอบ/แก้ไข</span>
      </div>
    </div>

    <div class="blog-kpi-box" onclick="window.open('/sitemap-blog.xml', '_blank')">
      <div class="kpi-icon-mini purple"><i class="ri-route-line"></i></div>
      <div class="kpi-info-mini">
        <span class="kpi-lbl-mini">Sitemap Blog</span>
        <span class="kpi-val-mini" style="color:#c084fc">100%</span>
        <span class="kpi-sub-mini">เชื่อมต่อบอทค้นหา ↗</span>
      </div>
    </div>
  </div>

  <!-- 2. Reorganized Toolbar Panel -->
  <div class="blog-panel-card">
    <!-- Top Toolbar Row -->
    <div class="blog-toolbar-top">
      <!-- Status Tabs -->
      <div class="blog-status-tabs">
        <button type="button" class="blog-status-tab is-active" id="tab-stat-all" onclick="filterByStatus('all', this)">
          <span>ทั้งหมด</span> <span class="tab-badge"><?= $allCount ?></span>
        </button>
        <button type="button" class="blog-status-tab" id="tab-stat-pub" onclick="filterByStatus('published', this)">
          <span>เผยแพร่แล้ว</span> <span class="tab-badge" style="background:#10b981;color:#fff"><?= $publishedCount ?></span>
        </button>
        <button type="button" class="blog-status-tab" id="tab-stat-draft" onclick="filterByStatus('draft', this)">
          <span>ฉบับร่าง</span> <span class="tab-badge" style="background:#f59e0b;color:#fff"><?= $draftCount ?></span>
        </button>
      </div>

      <!-- Right Actions: View Toggles & Add Button -->
      <div class="blog-toolbar-actions">
        <div class="view-switch-btns">
          <button type="button" class="view-btn is-active" id="btn-view-table" onclick="switchTidyView('table')">
            <i class="ri-table-line"></i> <span>ตาราง</span>
          </button>
          <button type="button" class="view-btn" id="btn-view-cards" onclick="switchTidyView('cards')">
            <i class="ri-grid-fill"></i> <span>การ์ด</span>
          </button>
        </div>

        <button type="button" class="la-btn la-btn-primary" onclick="toggleEditorDrawer(true)" style="gap:6px">
          <i class="ri-add-line"></i> <span>เขียนบทความใหม่</span>
        </button>
      </div>
    </div>

    <!-- Secondary Filter & Search Row -->
    <div class="blog-toolbar-search">
      <div class="search-wrapper">
        <i class="ri-search-line"></i>
        <input type="text" id="live-blog-search" oninput="handleInstantSearch(this.value)" placeholder="ค้นหาบทความด้วยชื่อ, แท็ก หรือ URL...">
      </div>

      <!-- Category Filter Chips -->
      <div class="category-chips-row">
        <span style="font-size:12px;color:#64748b;font-weight:600;"><i class="ri-filter-3-line"></i> แท็ก:</span>
        <div class="cat-chip is-active" onclick="filterByTag('', this)">ทั้งหมด</div>
        <div class="cat-chip" onclick="filterByTag('TikTok', this)"><i class="ri-tiktok-fill"></i> TikTok</div>
        <div class="cat-chip" onclick="filterByTag('Instagram', this)"><i class="ri-instagram-fill" style="color:#e1306c"></i> Instagram</div>
        <div class="cat-chip" onclick="filterByTag('Facebook', this)"><i class="ri-facebook-circle-fill" style="color:#1877f2"></i> Facebook</div>
        <div class="cat-chip" onclick="filterByTag('YouTube', this)"><i class="ri-youtube-fill" style="color:#ef4444"></i> YouTube</div>
        <div class="cat-chip" onclick="filterByTag('SEO', this)">SEO &amp; การตลาด</div>
        <div class="cat-chip" onclick="filterByTag('เคล็ดลับ', this)">เทคนิค</div>
      </div>
    </div>
  </div>

  <!-- 3. Collapsible Editor Drawer (Open only when needed) -->
  <div id="blog-editor-drawer" class="blog-editor-drawer" style="<?= $showForm ? 'display:block;' : 'display:none;' ?>">
    <div class="drawer-head">
      <div class="drawer-title-group">
        <h3>
          <i class="ri-edit-box-line" style="color:#38bdf8"></i>
          <span><?= $isEditing ? 'แก้ไขบทความ #' . htmlspecialchars((string)($editing['id'] ?? '')) : 'เขียนบทความใหม่ (New Article)' ?></span>
        </h3>
        <p>สร้างคอนเทนต์คุณภาพเพื่อดันคีย์เวิร์ด SEO และเพิ่มความน่าเชื่อถือให้กับร้านค้า</p>
      </div>
      <button type="button" class="drawer-close-btn" onclick="toggleEditorDrawer(false)">
        <i class="ri-close-line"></i> <span>ปิดหน้าต่าง</span>
      </button>
    </div>

    <form method="post" action="<?= $isEditing ? '/admin/appearance/blog/' . htmlspecialchars((string)$editing['id']) . '/edit' : '/admin/appearance/blog/add' ?>">
      <?php if ($isEditing): ?>
      <input type="hidden" name="pid" value="<?= htmlspecialchars((string)$editing['id']) ?>">
      <?php endif; ?>

      <div class="editor-grid-2col">
        <!-- Left: Main Content -->
        <div style="display:flex;flex-direction:column;gap:14px;">
          <div>
            <label class="la-field" style="font-weight:700">ชื่อบทความ (Title) *</label>
            <input class="la-input" id="ed-title" name="title" required value="<?= htmlspecialchars((string)($editing['title'] ?? '')) ?>" placeholder="เช่น อัลกอริทึม TikTok 2026 ดันคลิปขึ้นหน้าฟีด FYP ไวที่สุด" oninput="autoGenSlug(this.value)">
          </div>

          <div>
            <label class="la-field" style="font-weight:700">URL Slug (ภาษาอังกฤษคั่นด้วยขีดกลาง) *</label>
            <input class="la-input" id="ed-slug" name="slug" required value="<?= htmlspecialchars((string)($editing['slug'] ?? '')) ?>" placeholder="tiktok-algorithm-fyp-guide-2026" oninput="updateUrlPreview(this.value)">
            <div style="font-size:12px;color:#94a3b8;margin-top:4px;">
              ลิงก์หน้าเว็บจริง: <code id="live-slug-preview" style="color:#38bdf8">https://likes-auto.com/blog/<?= htmlspecialchars((string)($editing['slug'] ?? 'example-slug')) ?></code>
            </div>
          </div>

          <div>
            <label class="la-field" style="font-weight:700">แท็ก / หมวดหมู่ (คั่นด้วยจุลภาค)</label>
            <input class="la-input" id="ed-tags" name="tags" value="<?= htmlspecialchars((string)($editing['tags'] ?? '')) ?>" placeholder="TikTok, ปั้มวิว, ดันคลิป, เทคนิคการตลาด">
            <div style="display:flex;gap:5px;flex-wrap:wrap;margin-top:6px;">
              <span style="font-size:11px;color:#64748b;">คลิกเพื่อเพิ่ม:</span>
              <button type="button" class="cat-chip" style="font-size:10.5px;padding:2px 7px" onclick="appendTag('TikTok')">+ TikTok</button>
              <button type="button" class="cat-chip" style="font-size:10.5px;padding:2px 7px" onclick="appendTag('Instagram')">+ Instagram</button>
              <button type="button" class="cat-chip" style="font-size:10.5px;padding:2px 7px" onclick="appendTag('Facebook')">+ Facebook</button>
              <button type="button" class="cat-chip" style="font-size:10.5px;padding:2px 7px" onclick="appendTag('YouTube')">+ YouTube</button>
              <button type="button" class="cat-chip" style="font-size:10.5px;padding:2px 7px" onclick="appendTag('ปั้มไลค์')">+ ปั้มไลค์</button>
              <button type="button" class="cat-chip" style="font-size:10.5px;padding:2px 7px" onclick="appendTag('SEO')">+ SEO</button>
            </div>
          </div>

          <div>
            <label class="la-field" style="font-weight:700">คำโปรยสั้น (Excerpt)</label>
            <input class="la-input" name="excerpt" value="<?= htmlspecialchars((string)($editing['excerpt'] ?? '')) ?>" placeholder="สรุปเนื้อหาสั้น 1-2 บรรทัด สำหรับแสดงในการ์ดและ Google Meta Description">
          </div>

          <div>
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">
              <label class="la-field" style="font-weight:700;margin:0">เนื้อหาบทความ (HTML / Markdown) *</label>
              <div style="display:flex;gap:4px;">
                <button type="button" class="la-btn la-btn-mini la-btn-ghost" style="padding:2px 8px;font-size:11px" onclick="insertFmt('<h3>', '</h3>')">H3</button>
                <button type="button" class="la-btn la-btn-mini la-btn-ghost" style="padding:2px 8px;font-size:11px" onclick="insertFmt('<strong>', '</strong>')"><b>B</b></button>
                <button type="button" class="la-btn la-btn-mini la-btn-ghost" style="padding:2px 8px;font-size:11px" onclick="insertFmt('<em>', '</em>')"><i>I</i></button>
                <button type="button" class="la-btn la-btn-mini la-btn-ghost" style="padding:2px 8px;font-size:11px" onclick="insertFmt('<ul>\n  <li>', '</li>\n</ul>')">List</button>
                <button type="button" class="la-btn la-btn-mini la-btn-ghost" style="padding:2px 8px;font-size:11px" onclick="insertFmt('<div class=\"blog-callout\">\n  ', '\n</div>')">Callout</button>
              </div>
            </div>
            <textarea class="la-input" id="ed-body" name="body" rows="12" style="font-family:monospace;font-size:13px;line-height:1.5" required placeholder="เขียนเนื้อหาบทความที่นี่..."><?= htmlspecialchars((string)($editing['body'] ?? '')) ?></textarea>
          </div>
        </div>

        <!-- Right: Settings Sidebar -->
        <div style="display:flex;flex-direction:column;gap:16px;">
          <!-- Status Switch -->
          <div style="background:rgba(15,23,42,0.6);border:1px solid rgba(255,255,255,0.08);border-radius:10px;padding:14px;">
            <label style="display:flex;align-items:center;gap:10px;cursor:pointer;margin:0">
              <input type="checkbox" name="published" value="1" <?= (!isset($editing['published']) || !empty($editing['published'])) ? 'checked' : '' ?> style="width:18px;height:18px;accent-color:#10b981;">
              <div>
                <strong style="display:block;font-size:13.5px;color:#f8fafc">เผยแพร่ทันที (Published)</strong>
                <span style="font-size:11.5px;color:#94a3b8">ถ้าเอาเครื่องหมายออก จะบันทึกเป็นแบบร่าง</span>
              </div>
            </label>
          </div>

          <!-- Cover Image -->
          <div style="background:rgba(15,23,42,0.6);border:1px solid rgba(255,255,255,0.08);border-radius:10px;padding:14px;">
            <label class="la-field" style="font-weight:700">URL ภาพหน้าปก (Cover Image)</label>
            <input class="la-input" id="ed-cover" name="cover" value="<?= htmlspecialchars((string)($editing['cover'] ?? '/static/assets/blog/blog-facebook.jpg')) ?>" oninput="updateCoverPreview(this.value)">
            
            <div style="margin-top:10px;aspect-ratio:16/9;border-radius:6px;overflow:hidden;background:#0f172a;border:1px solid rgba(255,255,255,0.1)">
              <img id="ed-cover-preview" src="<?= htmlspecialchars((string)($editing['cover'] ?? '/static/assets/blog/blog-facebook.jpg')) ?>" style="width:100%;height:100%;object-fit:cover;" onerror="this.src='/static/assets/blog/blog-facebook.jpg'">
            </div>

            <!-- Media Gallery Thumbnails -->
            <label class="la-field" style="margin-top:12px;font-size:11.5px;">เลือกรูปภาพจากคลังด่วน (คลิกเพื่อใช้):</label>
            <div class="media-mini-grid">
              <?php foreach ($media as $mPath): ?>
              <div class="media-mini-thumb" onclick="pickCoverImg('<?= $mPath ?>')">
                <img src="<?= $mPath ?>" alt="thumb" loading="lazy">
              </div>
              <?php endforeach; ?>
            </div>
          </div>

          <!-- Save Button -->
          <div style="display:flex;flex-direction:column;gap:8px;">
            <button class="la-btn la-btn-primary" type="submit" style="width:100%;height:44px;font-size:14.5px;font-weight:700">
              <i class="ri-save-3-line"></i> <span><?= $isEditing ? 'บันทึกการแก้ไข' : 'บันทึกและเผยแพร่' ?></span>
            </button>
            <?php if ($isEditing): ?>
            <a href="/admin/appearance/blog" class="la-btn la-btn-ghost" style="width:100%;justify-content:center;text-decoration:none">
              ยกเลิกการแก้ไข
            </a>
            <?php endif; ?>
          </div>
        </div>
      </div>
    </form>
  </div>

  <!-- 4. Table View (Clean, Tidy, Super Organized - Default View) -->
  <div id="blog-view-table-wrapper" class="blog-table-container">
    <table class="blog-tidy-table" id="blog-master-table">
      <thead>
        <tr>
          <th style="width:50px">ID</th>
          <th style="width:65px">ภาพปก</th>
          <th>ชื่อบทความ / URL Slug</th>
          <th style="width:180px">หมวดหมู่ &amp; แท็ก</th>
          <th style="width:110px">สถานะ</th>
          <th style="width:120px">วันที่สร้าง</th>
          <th style="width:170px;text-align:right">จัดการ</th>
        </tr>
      </thead>
      <tbody id="blog-table-tbody">
        <?php foreach ($posts as $idx => $p): 
          $isPub = !empty($p['published']);
          $pCover = !empty($p['cover']) ? $p['cover'] : '/static/assets/blog/blog-facebook.jpg';
          $pSlug = !empty($p['slug']) ? $p['slug'] : '';
          $pId = !empty($p['id']) ? $p['id'] : ($idx + 1);
          $tagsArr = array_filter(array_map('trim', explode(',', $p['tags'] ?? '')));
        ?>
        <tr class="blog-row-item" 
            data-index="<?= $idx ?>"
            data-id="<?= $pId ?>" 
            data-status="<?= $isPub ? 'published' : 'draft' ?>"
            data-title="<?= htmlspecialchars(mb_strtolower($p['title'] ?? '', 'UTF-8')) ?>"
            data-tags="<?= htmlspecialchars(mb_strtolower($p['tags'] ?? '', 'UTF-8')) ?>"
            data-slug="<?= htmlspecialchars(mb_strtolower($pSlug, 'UTF-8')) ?>">
          <td>
            <strong style="color:#64748b">#<?= $pId ?></strong>
          </td>
          <td>
            <img class="cell-thumb" src="<?= htmlspecialchars($pCover) ?>" alt="thumb" loading="lazy" onerror="this.src='/static/assets/blog/blog-facebook.jpg'">
          </td>
          <td>
            <div class="cell-title-wrap">
              <a href="/admin/appearance/blog?edit=<?= $pId ?>" class="cell-title-link">
                <?= htmlspecialchars($p['title'] ?? 'ไม่มีชื่อบทความ') ?>
              </a>
              <div class="cell-slug">
                <i class="ri-link"></i>
                <a href="/blog/<?= htmlspecialchars($pSlug) ?>" target="_blank" rel="noopener" style="color:#38bdf8;text-decoration:none;">
                  /blog/<?= htmlspecialchars($pSlug) ?> <i class="ri-external-link-line" style="font-size:10px"></i>
                </a>
              </div>
            </div>
          </td>
          <td>
            <div>
              <?php if (!empty($tagsArr)): ?>
                <?php foreach (array_slice($tagsArr, 0, 3) as $tg): ?>
                <span class="tag-pill"><?= htmlspecialchars($tg) ?></span>
                <?php endforeach; ?>
                <?php if (count($tagsArr) > 3): ?>
                <span class="tag-pill">+<?= count($tagsArr) - 3 ?></span>
                <?php endif; ?>
              <?php else: ?>
                <span style="color:#64748b;font-size:11px">-</span>
              <?php endif; ?>
            </div>
          </td>
          <td>
            <?php if ($isPub): ?>
            <span class="status-pill published"><i class="ri-checkbox-circle-fill"></i> เผยแพร่แล้ว</span>
            <?php else: ?>
            <span class="status-pill draft"><i class="ri-draft-line"></i> ฉบับร่าง</span>
            <?php endif; ?>
          </td>
          <td>
            <span style="font-size:12px;color:#94a3b8;white-space:nowrap;">
              <?= htmlspecialchars(substr($p['created_at'] ?? '', 0, 10)) ?>
            </span>
          </td>
          <td style="text-align:right">
            <div class="action-btn-group" style="justify-content:flex-end">
              <a href="/admin/appearance/blog?edit=<?= $pId ?>" class="btn-act edit" title="แก้ไขบทความ">
                <i class="ri-edit-line"></i> <span>แก้ไข</span>
              </a>
              <a href="/blog/<?= htmlspecialchars($pSlug) ?>" target="_blank" rel="noopener" class="btn-act view" title="ดูหน้าเว็บจริง">
                <i class="ri-external-link-line"></i>
              </a>
              <form method="post" action="/admin/appearance/blog/<?= $pId ?>/delete" style="margin:0;display:inline" onsubmit="return confirm('ยืนยันลบบทความนี้?')">
                <button type="submit" class="btn-act del" title="ลบบทความ">
                  <i class="ri-delete-bin-line"></i>
                </button>
              </form>
            </div>
          </td>
        </tr>
        <?php endforeach; ?>
      </tbody>
    </table>
  </div>

  <!-- 5. Cards View (Structured 3-column Grid - Alternative View) -->
  <div id="blog-view-cards-wrapper" class="blog-cards-grid-tidy" style="display:none;">
    <?php foreach ($posts as $idx => $p): 
      $isPub = !empty($p['published']);
      $pCover = !empty($p['cover']) ? $p['cover'] : '/static/assets/blog/blog-facebook.jpg';
      $pSlug = !empty($p['slug']) ? $p['slug'] : '';
      $pId = !empty($p['id']) ? $p['id'] : ($idx + 1);
      $tagsArr = array_filter(array_map('trim', explode(',', $p['tags'] ?? '')));
    ?>
    <div class="blog-card-item-tidy blog-card-element"
         data-index="<?= $idx ?>"
         data-id="<?= $pId ?>" 
         data-status="<?= $isPub ? 'published' : 'draft' ?>"
         data-title="<?= htmlspecialchars(mb_strtolower($p['title'] ?? '', 'UTF-8')) ?>"
         data-tags="<?= htmlspecialchars(mb_strtolower($p['tags'] ?? '', 'UTF-8')) ?>"
         data-slug="<?= htmlspecialchars(mb_strtolower($pSlug, 'UTF-8')) ?>">
      <div class="card-thumb-wrap">
        <span class="card-id-badge">#<?= $pId ?></span>
        <div class="card-status-badge">
          <?php if ($isPub): ?>
          <span class="status-pill published"><i class="ri-checkbox-circle-fill"></i> เผยแพร่แล้ว</span>
          <?php else: ?>
          <span class="status-pill draft"><i class="ri-draft-line"></i> ฉบับร่าง</span>
          <?php endif; ?>
        </div>
        <img class="card-thumb-img" src="<?= htmlspecialchars($pCover) ?>" alt="cover" loading="lazy" onerror="this.src='/static/assets/blog/blog-facebook.jpg'">
      </div>

      <div class="card-content-tidy">
        <div style="margin-bottom:6px;">
          <?php foreach (array_slice($tagsArr, 0, 3) as $tg): ?>
          <span class="tag-pill"><?= htmlspecialchars($tg) ?></span>
          <?php endforeach; ?>
        </div>

        <h4 class="card-title-tidy">
          <a href="/admin/appearance/blog?edit=<?= $pId ?>" style="color:#f8fafc;text-decoration:none">
            <?= htmlspecialchars($p['title'] ?? 'ไม่มีชื่อบทความ') ?>
          </a>
        </h4>

        <div class="card-url-tidy">
          <i class="ri-link"></i> /blog/<?= htmlspecialchars($pSlug) ?>
        </div>

        <div class="card-footer-tidy">
          <span style="font-size:11.5px;color:#64748b;">
            <i class="ri-calendar-line"></i> <?= htmlspecialchars(substr($p['created_at'] ?? '', 0, 10)) ?>
          </span>
          <div class="action-btn-group">
            <a href="/admin/appearance/blog?edit=<?= $pId ?>" class="btn-act edit">
              <i class="ri-edit-line"></i> <span>แก้ไข</span>
            </a>
            <a href="/blog/<?= htmlspecialchars($pSlug) ?>" target="_blank" rel="noopener" class="btn-act view">
              <i class="ri-external-link-line"></i>
            </a>
            <form method="post" action="/admin/appearance/blog/<?= $pId ?>/delete" style="margin:0;display:inline" onsubmit="return confirm('ยืนยันลบบทความนี้?')">
              <button type="submit" class="btn-act del">
                <i class="ri-delete-bin-line"></i>
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
    <?php endforeach; ?>
  </div>

  <!-- 6. Smart Pagination Bar -->
  <div class="blog-pagination-bar">
    <div>
      <span id="page-summary-text">แสดง 1-15 จาก <?= $allCount ?> รายการ</span>
    </div>

    <div class="pagination-controls" id="pagination-controls">
      <!-- Generated dynamically by JavaScript -->
    </div>

    <div style="display:flex;align-items:center;gap:8px;">
      <span>แสดงหน้าละ:</span>
      <select id="page-size-select" onchange="changePageSize(this.value)" style="background:rgba(10,14,26,0.6);border:1px solid rgba(255,255,255,0.1);color:#fff;border-radius:6px;padding:3px 8px;font-size:12px;">
        <option value="15" selected>15</option>
        <option value="30">30</option>
        <option value="50">50</option>
        <option value="100">ทั้งหมด</option>
      </select>
    </div>
  </div>

  <!-- 7. Collapsible SEO & Content Strategy Guide (Tucked away neatly) -->
  <details style="background:rgba(18,24,38,0.6);border:1px solid rgba(255,255,255,0.06);border-radius:12px;padding:12px 18px;">
    <summary style="cursor:pointer;font-weight:600;color:#94a3b8;font-size:13px;display:flex;align-items:center;gap:8px;">
      <i class="ri-lightbulb-line" style="color:#f59e0b"></i>
      <span>คำแนะนำกลยุทธ์ Content &amp; SEO ดันอันดับค้นหา (คลิกเพื่อเปิดดู)</span>
      <i class="ri-arrow-down-s-line" style="margin-left:auto"></i>
    </summary>
    <div style="display:grid;grid-template-columns:repeat(auto-fit, minmax(260px, 1fr));gap:14px;margin-top:14px;padding-top:14px;border-top:1px solid rgba(255,255,255,0.06);">
      <div style="font-size:12.5px;color:#cbd5e1;line-height:1.5;">
        <strong style="color:#38bdf8;display:block;margin-bottom:4px">🎯 1. ใส่คีย์เวิร์ดใน 100 คำแรก</strong>
        เปิดบทความด้วยการระบุปัญหาและใส่คำค้นหาหลัก เช่น "ปั้มไลค์เฟส", "เพิ่มวิว TikTok", "SMM Panel" ในย่อหน้าแรก
      </div>
      <div style="font-size:12.5px;color:#cbd5e1;line-height:1.5;">
        <strong style="color:#10b981;display:block;margin-bottom:4px">🔗 2. ทำ Internal Links</strong>
        ใส่ลิงก์ชวนคลิกไปหน้าบริการ <code>/services</code> หรือหน้าแพลตฟอร์ม <code>/tiktok</code> เพื่อเปลี่ยนผู้อ่านเป็นลูกค้า
      </div>
      <div style="font-size:12.5px;color:#cbd5e1;line-height:1.5;">
        <strong style="color:#f59e0b;display:block;margin-bottom:4px">⚡ 3. ใช้รูปภาพอัตราส่วน 16:9</strong>
        เลือกภาพหน้าปกที่มีความคมชัด ไม่เบลอ เพื่อให้แสดงบนหน้าผลการค้นหาของ Google อย่างโดดเด่น
      </div>
    </div>
  </details>

</div>

<script>
// === LIKES AUTO ORGANIZED BLOG SCRIPT 2026 ===
var currentStatusFilter = 'all';
var currentTagFilter = '';
var currentSearchQuery = '';
var currentPage = 1;
var pageSize = 15;
var currentViewMode = localStorage.getItem('la_blog_view') || 'table';

function initBlogAdmin() {
  switchTidyView(currentViewMode, false);
  applyFiltersAndPaginate();
}

function switchTidyView(mode, save) {
  currentViewMode = mode;
  if (save !== false) {
    try { localStorage.setItem('la_blog_view', mode); } catch(e){}
  }
  var tblWrap = document.getElementById('blog-view-table-wrapper');
  var crdWrap = document.getElementById('blog-view-cards-wrapper');
  var btnTbl = document.getElementById('btn-view-table');
  var btnCrd = document.getElementById('btn-view-cards');

  if (mode === 'cards') {
    if (tblWrap) tblWrap.style.display = 'none';
    if (crdWrap) crdWrap.style.display = 'grid';
    if (btnTbl) btnTbl.classList.remove('is-active');
    if (btnCrd) btnCrd.classList.add('is-active');
  } else {
    if (tblWrap) tblWrap.style.display = 'block';
    if (crdWrap) crdWrap.style.display = 'none';
    if (btnTbl) btnTbl.classList.add('is-active');
    if (btnCrd) btnCrd.classList.remove('is-active');
  }
  applyFiltersAndPaginate();
}

function filterByStatus(st, el) {
  currentStatusFilter = st;
  currentPage = 1;
  document.querySelectorAll('.blog-status-tab').forEach(function(b){ b.classList.remove('is-active'); });
  document.querySelectorAll('.blog-kpi-box').forEach(function(b){ b.classList.remove('is-active'); });
  
  if (st === 'all') {
    var t = document.getElementById('tab-stat-all'); if(t) t.classList.add('is-active');
  } else if (st === 'published') {
    var t = document.getElementById('tab-stat-pub'); if(t) t.classList.add('is-active');
  } else if (st === 'draft') {
    var t = document.getElementById('tab-stat-draft'); if(t) t.classList.add('is-active');
  }
  if (el && el.classList.contains('blog-kpi-box')) el.classList.add('is-active');

  applyFiltersAndPaginate();
}

function filterByTag(tag, el) {
  currentTagFilter = tag.toLowerCase().trim();
  currentPage = 1;
  document.querySelectorAll('.cat-chip').forEach(function(c){ c.classList.remove('is-active'); });
  if (el) el.classList.add('is-active');
  applyFiltersAndPaginate();
}

function handleInstantSearch(val) {
  currentSearchQuery = val.toLowerCase().trim();
  currentPage = 1;
  applyFiltersAndPaginate();
}

function changePageSize(size) {
  pageSize = parseInt(size, 10) || 15;
  currentPage = 1;
  applyFiltersAndPaginate();
}

function applyFiltersAndPaginate() {
  var rows = document.querySelectorAll('.blog-row-item');
  var cards = document.querySelectorAll('.blog-card-element');

  var matchedIndices = [];

  rows.forEach(function(row) {
    var idx = row.getAttribute('data-index');
    var st = row.getAttribute('data-status');
    var tit = row.getAttribute('data-title') || '';
    var tags = row.getAttribute('data-tags') || '';
    var slug = row.getAttribute('data-slug') || '';

    // Status check
    var passStatus = (currentStatusFilter === 'all') || (st === currentStatusFilter);

    // Tag check
    var passTag = (!currentTagFilter) || (tags.indexOf(currentTagFilter) !== -1) || (tit.indexOf(currentTagFilter) !== -1);

    // Search query check
    var passSearch = true;
    if (currentSearchQuery) {
      passSearch = (tit.indexOf(currentSearchQuery) !== -1) || 
                   (slug.indexOf(currentSearchQuery) !== -1) || 
                   (tags.indexOf(currentSearchQuery) !== -1);
    }

    if (passStatus && passTag && passSearch) {
      matchedIndices.push(idx);
    }
  });

  var totalMatched = matchedIndices.length;
  var totalPages = Math.ceil(totalMatched / pageSize) || 1;
  if (currentPage > totalPages) currentPage = totalPages;
  if (currentPage < 1) currentPage = 1;

  var startIndex = (currentPage - 1) * pageSize;
  var endIndex = startIndex + pageSize;
  var visibleSet = new Set(matchedIndices.slice(startIndex, endIndex));

  // Update Table Rows
  rows.forEach(function(row) {
    var idx = row.getAttribute('data-index');
    row.style.display = visibleSet.has(idx) ? '' : 'none';
  });

  // Update Cards
  cards.forEach(function(card) {
    var idx = card.getAttribute('data-index');
    card.style.display = visibleSet.has(idx) ? 'flex' : 'none';
  });

  // Update Summary text
  var sumText = document.getElementById('page-summary-text');
  if (sumText) {
    if (totalMatched === 0) {
      sumText.textContent = 'ไม่พบบทความที่ตรงกับเงื่อนไขการค้นหา';
    } else {
      var fromN = startIndex + 1;
      var toN = Math.min(endIndex, totalMatched);
      sumText.textContent = 'แสดง ' + fromN + '-' + toN + ' จากทั้งหมด ' + totalMatched + ' รายการ';
    }
  }

  // Render Pagination Buttons
  renderPaginationButtons(totalPages);
}

function renderPaginationButtons(totalPages) {
  var container = document.getElementById('pagination-controls');
  if (!container) return;
  container.innerHTML = '';

  if (totalPages <= 1) return;

  // Prev Button
  var prevBtn = document.createElement('button');
  prevBtn.className = 'page-btn';
  prevBtn.innerHTML = '<i class="ri-arrow-left-s-line"></i>';
  prevBtn.disabled = (currentPage === 1);
  prevBtn.onclick = function() { if (currentPage > 1) { currentPage--; applyFiltersAndPaginate(); } };
  container.appendChild(prevBtn);

  // Page Numbers
  var startP = Math.max(1, currentPage - 2);
  var endP = Math.min(totalPages, currentPage + 2);

  if (startP > 1) {
    var p1 = createPageBtn(1);
    container.appendChild(p1);
    if (startP > 2) {
      var dots = document.createElement('span');
      dots.style.padding = '0 4px';
      dots.style.color = '#64748b';
      dots.textContent = '...';
      container.appendChild(dots);
    }
  }

  for (var p = startP; p <= endP; p++) {
    container.appendChild(createPageBtn(p));
  }

  if (endP < totalPages) {
    if (endP < totalPages - 1) {
      var dots = document.createElement('span');
      dots.style.padding = '0 4px';
      dots.style.color = '#64748b';
      dots.textContent = '...';
      container.appendChild(dots);
    }
    container.appendChild(createPageBtn(totalPages));
  }

  // Next Button
  var nextBtn = document.createElement('button');
  nextBtn.className = 'page-btn';
  nextBtn.innerHTML = '<i class="ri-arrow-right-s-line"></i>';
  nextBtn.disabled = (currentPage === totalPages);
  nextBtn.onclick = function() { if (currentPage < totalPages) { currentPage++; applyFiltersAndPaginate(); } };
  container.appendChild(nextBtn);
}

function createPageBtn(pageNum) {
  var b = document.createElement('button');
  b.className = 'page-btn' + (pageNum === currentPage ? ' is-active' : '');
  b.textContent = pageNum;
  b.onclick = function() {
    currentPage = pageNum;
    applyFiltersAndPaginate();
  };
  return b;
}

// Drawer & Editor Helpers
function toggleEditorDrawer(open) {
  var d = document.getElementById('blog-editor-drawer');
  if (!d) return;
  d.style.display = open ? 'block' : 'none';
  if (open) {
    d.scrollIntoView({ behavior: 'smooth', block: 'start' });
    var t = document.getElementById('ed-title');
    if (t && !t.value) t.focus();
  }
}

function autoGenSlug(title) {
  var slugEl = document.getElementById('ed-slug');
  if (!slugEl || slugEl.dataset.touched === '1') return;
  var s = title.trim().toLowerCase()
    .replace(/[^\w\s-]/g, '')
    .replace(/[\s_-]+/g, '-')
    .replace(/^-+|-+$/g, '');
  if (s) {
    slugEl.value = s;
    updateUrlPreview(s);
  }
}

function updateUrlPreview(slug) {
  var prev = document.getElementById('live-slug-preview');
  if (prev) {
    prev.textContent = 'https://likes-auto.com/blog/' + (slug || 'example-slug');
  }
}

function updateCoverPreview(url) {
  var img = document.getElementById('ed-cover-preview');
  if (img) img.src = url || '/static/assets/blog/blog-facebook.jpg';
}

function pickCoverImg(url) {
  var inp = document.getElementById('ed-cover');
  if (inp) {
    inp.value = url;
    updateCoverPreview(url);
  }
}

function appendTag(tag) {
  var inp = document.getElementById('ed-tags');
  if (!inp) return;
  var cur = inp.value.trim();
  if (!cur) {
    inp.value = tag;
  } else {
    var parts = cur.split(',').map(function(s){ return s.trim(); });
    if (parts.indexOf(tag) === -1) {
      inp.value = cur + ', ' + tag;
    }
  }
}

function insertFmt(before, after) {
  var ta = document.getElementById('ed-body');
  if (!ta) return;
  var start = ta.selectionStart;
  var end = ta.selectionEnd;
  var sel = ta.value.substring(start, end);
  var rep = before + (sel || '') + after;
  ta.value = ta.value.substring(0, start) + rep + ta.value.substring(end);
  ta.focus();
  ta.selectionStart = start + before.length;
  ta.selectionEnd = start + before.length + (sel ? sel.length : 0);
}

// Mark slug as touched if edited manually
document.addEventListener('DOMContentLoaded', function(){
  initBlogAdmin();
  var slugEl = document.getElementById('ed-slug');
  if (slugEl) {
    slugEl.addEventListener('input', function(){ slugEl.dataset.touched = '1'; });
  }
});
// Execute init immediately if already loaded
if (document.readyState !== 'loading') {
  initBlogAdmin();
}
</script>
