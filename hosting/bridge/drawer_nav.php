<?php
/**
 * Peakerr-Inspired Modern Responsive Navigation System for Likes Auto
 * High-Converting, Ultra-Modern Dark Theme with Signature Neon Lime Glow
 * Universal Off-Canvas Drawer for Mobile, Tablet & Desktop
 */
$isLoggedIn = !empty($isUser);
$userInitial = !empty($username) ? mb_strtoupper(mb_substr($username, 0, 1, 'UTF-8')) : 'U';
$userBalFormatted = isset($balance) ? number_format((float)$balance, 2) : '0.00';
$cur = $currentPage ?? '';
?>
<!-- Universal Peakerr Off-Canvas Drawer Navigation (Mobile, Tablet & Desktop) -->
<nav class="la-nav la-drawer-revamp pk-drawer" id="laNav" aria-label="เมนูหลัก">
  <!-- Peakerr Drawer Top Bar -->
  <div class="la-drawer-top pk-drawer-top">
    <div class="la-drawer-brand">
      <span class="la-brand-mark pk-brand-mark" aria-hidden="true"><i class="ri-flashlight-fill"></i></span>
      <span class="la-drawer-title pk-brand-text">Likes<span>Auto</span></span>
    </div>
    <div class="la-drawer-top-actions">
      <span class="la-drawer-status-pill pk-status-pill"><span class="la-live-pulse-dot pk-pulse-dot"></span> ออนไลน์ 24 ชม.</span>
      <button type="button" class="la-drawer-close pk-drawer-close" onclick="laCloseNav()" aria-label="ปิดเมนู">
        <i class="ri-close-line"></i>
      </button>
    </div>
  </div>

  <div class="la-drawer-scroll">
    <?php if ($isLoggedIn): ?>
    <!-- Logged-in User Profile Card -->
    <div class="la-drawer-user-card pk-user-card">
      <div class="la-drawer-user-row">
        <div class="la-drawer-avatar pk-avatar"><?= htmlspecialchars($userInitial) ?></div>
        <div class="la-drawer-uinfo">
          <div class="la-drawer-uname"><?= htmlspecialchars($username) ?></div>
          <div class="la-drawer-ubadge pk-ubadge"><i class="ri-shield-check-fill"></i> สมาชิก Verified</div>
        </div>
      </div>
      <div class="la-drawer-bal-row">
        <div>
          <span class="la-drawer-bal-lbl">ยอดเงินคงเหลือ</span>
          <span class="la-drawer-bal-val pk-bal-val">฿<?= $userBalFormatted ?></span>
        </div>
        <a href="/addfunds" class="la-btn pk-addfunds-btn">
          <i class="ri-wallet-3-line"></i> เติมเงิน
        </a>
      </div>
    </div>
    <?php else: ?>
    <!-- Peakerr Guest Welcome Card (Guaranteed never to shrink or clip) -->
    <div class="la-drawer-guest-card pk-guest-card" style="flex-shrink:0 !important; min-height:auto !important;">
      <div class="la-drawer-guest-top">
        <div class="la-drawer-guest-badge pk-guest-badge">
          <span class="la-live-pulse-dot pk-pulse-dot"></span> แผงปั๊มไลค์อันดับ 1
        </div>
        <span class="la-drawer-guest-subtag pk-guest-subtag"><i class="ri-shield-check-fill"></i> ปลอดภัย 100%</span>
      </div>
      <h3 class="la-drawer-guest-h" style="font-size:15px; font-weight:800; color:#fff; margin:4px 0 6px;">ปั๊มไลค์ &amp; ฟอล ราคาถูกที่สุด</h3>
      <p class="la-drawer-guest-p" style="font-size:12px; color:#94a3b8; line-height:1.45; margin:0 0 12px;">บริการปั๊มไลค์ทุกแพลตฟอร์ม ยอดขึ้นไว ปลอดภัย อัตโนมัติ 24 ชม. ไม่ใช้รหัสผ่าน</p>
      <div class="la-drawer-cta-grid" style="display:flex; flex-direction:column; gap:8px;">
        <a href="/signup" class="la-btn pk-drawer-signup-btn">
          <i class="ri-rocket-fill"></i> <span>สมัครสมาชิกฟรี</span>
        </a>
        <a href="/signin" onclick="laOpenLogin(event)" class="la-btn pk-drawer-signin-btn">
          <i class="ri-login-box-line"></i> <span>เข้าสู่ระบบ</span>
        </a>
      </div>
    </div>
    <?php endif; ?>

    <!-- Quick Social Platform Shortcuts -->
    <div class="la-drawer-section">
      <div class="la-drawer-sec-header">
        <span>แพลตฟอร์มยอดนิยม</span>
        <a href="/services" class="la-drawer-sec-link pk-sec-link">ดูทั้งหมด <i class="ri-arrow-right-s-line"></i></a>
      </div>
      <div class="la-drawer-plat-grid">
        <a href="/tiktok" class="la-drawer-plat-item pk-plat-item plat-tiktok">
          <div class="plat-ico"><i class="ri-tiktok-fill"></i></div>
          <div class="plat-meta">
            <span class="plat-name">TikTok</span>
            <span class="plat-sub">วิว / ฟอล / ไลค์</span>
          </div>
        </a>
        <a href="/instagram" class="la-drawer-plat-item pk-plat-item plat-ig">
          <div class="plat-ico"><i class="ri-instagram-fill"></i></div>
          <div class="plat-meta">
            <span class="plat-name">Instagram</span>
            <span class="plat-sub">ไลค์ / ผู้ติดตาม</span>
          </div>
        </a>
        <a href="/facebook" class="la-drawer-plat-item pk-plat-item plat-fb">
          <div class="plat-ico"><i class="ri-facebook-fill"></i></div>
          <div class="plat-meta">
            <span class="plat-name">Facebook</span>
            <span class="plat-sub">เพจ / ปั้มโพสต์</span>
          </div>
        </a>
        <a href="/youtube" class="la-drawer-plat-item pk-plat-item plat-yt">
          <div class="plat-ico"><i class="ri-youtube-fill"></i></div>
          <div class="plat-meta">
            <span class="plat-name">YouTube</span>
            <span class="plat-sub">วิว / ซับสไครบ์</span>
          </div>
        </a>
      </div>
      <!-- Secondary Platform Badges -->
      <div class="la-drawer-plat-chips">
        <a href="/twitter" class="plat-chip pk-chip"><i class="ri-twitter-x-fill"></i> X (Twitter)</a>
        <a href="/shopee" class="plat-chip pk-chip"><i class="ri-shopping-bag-2-line"></i> Shopee</a>
        <a href="/telegram" class="plat-chip pk-chip"><i class="ri-telegram-fill"></i> Telegram</a>
        <a href="/spotify" class="plat-chip pk-chip"><i class="ri-spotify-fill"></i> Spotify</a>
      </div>
    </div>

    <!-- Navigation Menu List -->
    <div class="la-drawer-section">
      <div class="la-drawer-sec-header">
        <span>เมนูนำทาง</span>
      </div>
      <div class="la-drawer-nav-list">
        <?php if ($isLoggedIn): ?>
        <a href="/neworder" class="la-drawer-nav-item pk-nav-item <?= ($cur==='neworder')?'active':'' ?>">
          <i class="ri-add-circle-fill pk-icon-accent"></i>
          <span>สั่งซื้อใหม่</span>
          <span class="la-nav-pill-badge hot">ด่วน</span>
        </a>
        <a href="/orders" class="la-drawer-nav-item pk-nav-item <?= ($cur==='orders')?'active':'' ?>">
          <i class="ri-file-list-3-line"></i>
          <span>ประวัติคำสั่งซื้อ</span>
        </a>
        <a href="/services" class="la-drawer-nav-item pk-nav-item <?= ($cur==='services')?'active':'' ?>">
          <i class="ri-store-2-line"></i>
          <span>บริการและราคา</span>
        </a>
        <a href="/addfunds" class="la-drawer-nav-item pk-nav-item <?= ($cur==='addfunds')?'active':'' ?>">
          <i class="ri-wallet-3-line"></i>
          <span>เติมเงิน</span>
        </a>
        <a href="/tickets" class="la-drawer-nav-item pk-nav-item <?= ($cur==='tickets')?'active':'' ?>">
          <i class="ri-customer-service-2-line"></i>
          <span>ตั๋วช่วยเหลือ</span>
        </a>
        <a href="/blog" class="la-drawer-nav-item pk-nav-item <?= ($cur==='blog')?'active':'' ?>">
          <i class="ri-article-line"></i>
          <span>บทความ &amp; สาระน่ารู้</span>
        </a>
        <a href="/logout" class="la-drawer-nav-item pk-nav-item" style="color:#f87171;">
          <i class="ri-logout-box-r-line"></i>
          <span>ออกจากระบบ</span>
        </a>
        <?php else: ?>
        <a href="/" class="la-drawer-nav-item pk-nav-item <?= ($cur===''||$cur==='home')?'active':'' ?>">
          <i class="ri-home-5-line"></i>
          <span>หน้าแรก</span>
        </a>
        <a href="/services" class="la-drawer-nav-item pk-nav-item <?= ($cur==='services')?'active':'' ?>">
          <i class="ri-store-2-line"></i>
          <span>บริการและราคา</span>
          <span class="la-nav-pill-badge hot">ยอดนิยม</span>
        </a>
        <a href="/blog" class="la-drawer-nav-item pk-nav-item <?= ($cur==='blog')?'active':'' ?>">
          <i class="ri-article-line"></i>
          <span>บทความ &amp; สาระน่ารู้</span>
          <span class="la-nav-pill-badge new">68 บทความ</span>
        </a>
        <a href="/faq" class="la-drawer-nav-item pk-nav-item <?= ($cur==='faq')?'active':'' ?>">
          <i class="ri-question-line"></i>
          <span>คำถามที่พบบ่อย (FAQ)</span>
        </a>
        <a href="/api" class="la-drawer-nav-item pk-nav-item <?= ($cur==='api')?'active':'' ?>">
          <i class="ri-code-box-line"></i>
          <span>API สำหรับนักพัฒนา</span>
        </a>
        <a href="/#contact" class="la-drawer-nav-item pk-nav-item">
          <i class="ri-customer-service-2-line"></i>
          <span>ติดต่อเรา</span>
        </a>
        <?php endif; ?>
      </div>
    </div>

    <!-- Trust & Guarantees -->
    <div class="la-drawer-trust-box pk-trust-box">
      <div class="la-drawer-trust-item">
        <i class="ri-flashlight-line pk-icon-accent"></i>
        <div>
          <strong>ระบบอัตโนมัติ 100%</strong>
          <span>ส่งยอดไวใน 1-5 นาทีหลังสั่งซื้อ</span>
        </div>
      </div>
      <div class="la-drawer-trust-item">
        <i class="ri-shield-keyhole-line pk-icon-accent"></i>
        <div>
          <strong>ปลอดภัยสูงสุด</strong>
          <span>ใช้เพียงลิงก์ ไม่ขอรหัสผ่านเด็ดขาด</span>
        </div>
      </div>
      <div class="la-drawer-trust-item">
        <i class="ri-qr-code-line pk-icon-accent"></i>
        <div>
          <strong>สแกน QR พร้อมเพย์</strong>
          <span>เติมเงินได้ตลอด 24 ชั่วโมง</span>
        </div>
      </div>
    </div>

    <!-- Direct Support CTA -->
    <div class="la-drawer-support-card pk-support-card">
      <div style="display:flex; align-items:center; gap:10px;">
        <div class="support-icon pk-support-ico"><i class="ri-customer-service-2-line"></i></div>
        <div class="support-text">
          <strong>ติดต่อฝ่ายบริการลูกค้า</strong>
          <span>มีข้อสงสัยหรือติดปัญหา แชทได้ 24 ชม.</span>
        </div>
      </div>
      <a href="/tickets" class="la-btn pk-support-btn">
        <i class="ri-chat-3-line"></i> <span>เปิดตั๋วติดต่อแอดมิน</span>
      </a>
    </div>

        <!-- Theme Switcher in Drawer (Professional 2x2 Grid) -->
    <div class="la-drawer-theme-box pk-theme-box" style="display:flex !important; flex-direction:column !important; align-items:stretch !important; gap:10px !important;">
      <div style="display:flex; align-items:center; justify-content:space-between;">
        <span class="theme-lbl" style="font-size:12px; font-weight:700; color:#94a3b8; text-transform:uppercase;"><i class="ri-palette-line" style="color:var(--pk-green, #8ee31f); margin-right:4px;"></i> ธีมการแสดงผล</span>
      </div>
      <div class="la-drawer-theme-grid" style="display:grid; grid-template-columns:1fr 1fr; gap:8px;">
        <button type="button" class="pk-theme-card" onclick="laSelectTheme('peak', event)" style="display:flex; align-items:center; gap:8px; padding:9px 12px; border-radius:10px; background:rgba(255,255,255,0.04); border:1px solid rgba(255,255,255,0.1); color:#fff; cursor:pointer; text-align:left;">
          <span style="width:18px; height:18px; border-radius:50%; background:linear-gradient(135deg, #051408 0%, #4da813 60%, #8ee31f 100%); border:1px solid rgba(255,255,255,0.2); flex-shrink:0;"></span>
          <span style="font-size:12.5px; font-weight:600;">Peakerr</span>
        </button>
        <button type="button" class="pk-theme-card" onclick="laSelectTheme('violet', event)" style="display:flex; align-items:center; gap:8px; padding:9px 12px; border-radius:10px; background:rgba(255,255,255,0.04); border:1px solid rgba(255,255,255,0.1); color:#fff; cursor:pointer; text-align:left;">
          <span style="width:18px; height:18px; border-radius:50%; background:linear-gradient(135deg, #120822 0%, #7c25d8 60%, #b862f8 100%); border:1px solid rgba(255,255,255,0.2); flex-shrink:0;"></span>
          <span style="font-size:12.5px; font-weight:600;">Violet</span>
        </button>
        <button type="button" class="pk-theme-card" onclick="laSelectTheme('navy', event)" style="display:flex; align-items:center; gap:8px; padding:9px 12px; border-radius:10px; background:rgba(255,255,255,0.04); border:1px solid rgba(255,255,255,0.1); color:#fff; cursor:pointer; text-align:left;">
          <span style="width:18px; height:18px; border-radius:50%; background:linear-gradient(135deg, #071329 0%, #1d5ec9 60%, #3b82f6 100%); border:1px solid rgba(255,255,255,0.2); flex-shrink:0;"></span>
          <span style="font-size:12.5px; font-weight:600;">Navy</span>
        </button>
        <button type="button" class="pk-theme-card" onclick="laSelectTheme('light', event)" style="display:flex; align-items:center; gap:8px; padding:9px 12px; border-radius:10px; background:rgba(255,255,255,0.04); border:1px solid rgba(255,255,255,0.1); color:#fff; cursor:pointer; text-align:left;">
          <span style="width:18px; height:18px; border-radius:50%; background:linear-gradient(135deg, #ffffff 0%, #86efac 55%, #38a11b 100%); border:1px solid rgba(255,255,255,0.2); flex-shrink:0;"></span>
          <span style="font-size:12.5px; font-weight:600;">Light</span>
        </button>
      </div>
    </div>

    <!-- Footer Copyright -->
    <div class="la-drawer-foot">
      <span>Likes-Auto.com &copy; 2026 &middot; แผงปั้มไลค์อันดับ 1 ในไทย</span>
      <div class="la-drawer-legal-links">
        <a href="/terms">ข้อกำหนด</a> &middot; <a href="/privacy">นโยบายความเป็นส่วนตัว</a> &middot; <a href="/site-map">แผนผังเว็บ</a>
      </div>
    </div>
  </div>
</nav>
