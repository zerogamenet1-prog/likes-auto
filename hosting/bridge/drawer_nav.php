<?php
/**
 * Modern Responsive Navigation & Drawer Component for Likes Auto
 * Seamless Desktop Navbar + Mobile Drawer System
 */
$isLoggedIn = !empty($isUser);
$userInitial = !empty($username) ? mb_strtoupper(mb_substr($username, 0, 1, 'UTF-8')) : 'U';
$userBalFormatted = isset($balance) ? number_format((float)$balance, 2) : '0.00';
$cur = $currentPage ?? '';
?>
<!-- 1. Desktop Horizontal Navigation Bar (>= 1024px) -->
<nav class="la-desktop-nav" aria-label="เมนูหลักสำหรับคอมพิวเตอร์">
  <?php if ($isLoggedIn): ?>
  <a href="/neworder" class="la-dlink <?= ($cur==='neworder')?'active':'' ?>">
    <i class="ri-add-circle-fill" style="color:var(--la-accent, #10b981);"></i>
    <span>สั่งซื้อใหม่</span>
    <span class="la-dpill hot">ด่วน</span>
  </a>
  <a href="/orders" class="la-dlink <?= ($cur==='orders')?'active':'' ?>">
    <i class="ri-file-list-3-line"></i>
    <span>ประวัติคำสั่งซื้อ</span>
  </a>
  <a href="/services" class="la-dlink <?= ($cur==='services')?'active':'' ?>">
    <span>บริการและราคา</span>
  </a>
  <div class="la-ddrop">
    <button type="button" class="la-dlink la-ddrop-btn" aria-haspopup="true" aria-expanded="false">
      <span>แพลตฟอร์ม</span>
      <i class="ri-arrow-down-s-line"></i>
    </button>
    <div class="la-ddrop-menu">
      <a href="/tiktok" class="la-ddrop-item"><i class="ri-tiktok-fill" style="color:#25f4ee;"></i> <span>TikTok</span> <small>วิว / ฟอล / ไลค์</small></a>
      <a href="/instagram" class="la-ddrop-item"><i class="ri-instagram-fill" style="color:#e1306c;"></i> <span>Instagram</span> <small>ไลค์ / ผู้ติดตาม</small></a>
      <a href="/facebook" class="la-ddrop-item"><i class="ri-facebook-fill" style="color:#1877f2;"></i> <span>Facebook</span> <small>เพจ / ปั้มโพสต์</small></a>
      <a href="/youtube" class="la-ddrop-item"><i class="ri-youtube-fill" style="color:#ff0000;"></i> <span>YouTube</span> <small>วิว / ซับสไครบ์</small></a>
      <a href="/twitter" class="la-ddrop-item"><i class="ri-twitter-x-fill" style="color:#cbd5e1;"></i> <span>X (Twitter)</span> <small>รีทวีต / ฟอล</small></a>
      <a href="/shopee" class="la-ddrop-item"><i class="ri-shopping-bag-2-line" style="color:#ee4d2d;"></i> <span>Shopee</span> <small>ติดตามร้านค้า</small></a>
      <a href="/telegram" class="la-ddrop-item"><i class="ri-telegram-fill" style="color:#24a1de;"></i> <span>Telegram</span> <small>สมาชิกกลุ่ม</small></a>
    </div>
  </div>
  <a href="/addfunds" class="la-dlink <?= ($cur==='addfunds')?'active':'' ?>">
    <i class="ri-wallet-3-line"></i>
    <span>เติมเงิน</span>
  </a>
  <a href="/tickets" class="la-dlink <?= ($cur==='tickets')?'active':'' ?>">
    <span>ตั๋วช่วยเหลือ</span>
  </a>
  <a href="/blog" class="la-dlink <?= ($cur==='blog')?'active':'' ?>">
    <span>บทความ</span>
  </a>
  <?php else: ?>
  <a href="/" class="la-dlink <?= ($cur===''||$cur==='home')?'active':'' ?>">หน้าแรก</a>
  <a href="/services" class="la-dlink <?= ($cur==='services')?'active':'' ?>">
    <span>บริการและราคา</span>
    <span class="la-dpill hot">ยอดนิยม</span>
  </a>
  <div class="la-ddrop">
    <button type="button" class="la-dlink la-ddrop-btn" aria-haspopup="true" aria-expanded="false">
      <span>หมวดหมู่โซเชียล</span>
      <i class="ri-arrow-down-s-line"></i>
    </button>
    <div class="la-ddrop-menu">
      <a href="/tiktok" class="la-ddrop-item"><i class="ri-tiktok-fill" style="color:#25f4ee;"></i> <span>TikTok</span> <small>วิว / ฟอล / ไลค์</small></a>
      <a href="/instagram" class="la-ddrop-item"><i class="ri-instagram-fill" style="color:#e1306c;"></i> <span>Instagram</span> <small>ไลค์ / ผู้ติดตาม</small></a>
      <a href="/facebook" class="la-ddrop-item"><i class="ri-facebook-fill" style="color:#1877f2;"></i> <span>Facebook</span> <small>เพจ / ปั้มโพสต์</small></a>
      <a href="/youtube" class="la-ddrop-item"><i class="ri-youtube-fill" style="color:#ff0000;"></i> <span>YouTube</span> <small>วิว / ซับสไครบ์</small></a>
      <a href="/twitter" class="la-ddrop-item"><i class="ri-twitter-x-fill" style="color:#cbd5e1;"></i> <span>X (Twitter)</span> <small>รีทวีต / ฟอล</small></a>
      <a href="/shopee" class="la-ddrop-item"><i class="ri-shopping-bag-2-line" style="color:#ee4d2d;"></i> <span>Shopee</span> <small>ติดตามร้านค้า</small></a>
      <a href="/telegram" class="la-ddrop-item"><i class="ri-telegram-fill" style="color:#24a1de;"></i> <span>Telegram</span> <small>สมาชิกกลุ่ม</small></a>
    </div>
  </div>
  <a href="/blog" class="la-dlink <?= ($cur==='blog')?'active':'' ?>">
    <span>บทความ</span>
    <span class="la-dpill blog">68 บทความ</span>
  </a>
  <a href="/faq" class="la-dlink <?= ($cur==='faq')?'active':'' ?>">คำถามที่พบบ่อย</a>
  <a href="/#contact" class="la-dlink">ติดต่อเรา</a>
  <?php endif; ?>
</nav>

<!-- 2. Responsive Mobile Drawer Navigation -->
<nav class="la-nav la-drawer-revamp" id="laNav" aria-label="เมนูหลักบนมือถือ">
  <!-- Drawer Top Bar -->
  <div class="la-drawer-top">
    <div class="la-drawer-brand">
      <span class="la-brand-mark" aria-hidden="true"><i class="ri-flashlight-fill"></i></span>
      <span class="la-drawer-title">Likes<em>Auto</em></span>
    </div>
    <div class="la-drawer-top-actions">
      <span class="la-drawer-status-pill"><span class="la-live-pulse-dot"></span> ออนไลน์ 24 ชม.</span>
      <button type="button" class="la-drawer-close" onclick="laCloseNav()" aria-label="ปิดเมนู">
        <i class="ri-close-line"></i>
      </button>
    </div>
  </div>

  <div class="la-drawer-scroll">
    <!-- Profile or Welcome Card (Guaranteed never to shrink or clip) -->
    <?php if ($isLoggedIn): ?>
    <div class="la-drawer-user-card">
      <div class="la-drawer-user-row">
        <div class="la-drawer-avatar"><?= htmlspecialchars($userInitial) ?></div>
        <div class="la-drawer-uinfo">
          <div class="la-drawer-uname"><?= htmlspecialchars($username) ?></div>
          <div class="la-drawer-ubadge"><i class="ri-shield-check-fill"></i> สมาชิก Verified</div>
        </div>
      </div>
      <div class="la-drawer-bal-row">
        <div>
          <div class="la-drawer-bal-lbl">ยอดเงินคงเหลือ</div>
          <div class="la-drawer-bal-val">฿<?= $userBalFormatted ?></div>
        </div>
        <a href="/addfunds" class="la-btn la-btn-mini la-drawer-addfunds-btn"><i class="ri-wallet-3-line"></i> เติมเงิน</a>
      </div>
    </div>
    <?php else: ?>
    <div class="la-drawer-guest-card">
      <div class="la-drawer-guest-top">
        <div class="la-drawer-guest-badge">
          <span class="la-live-pulse-dot"></span> ระบบอัตโนมัติ 24 ชม.
        </div>
        <span class="la-drawer-guest-subtag"><i class="ri-shield-check-fill"></i> ปลอดภัย 100%</span>
      </div>
      <h3 class="la-drawer-guest-h">เพิ่มยอดไลค์ ฟอล วิว อันดับ 1</h3>
      <p class="la-drawer-guest-p">บริการปั้มไลค์โซเชียลทุกแพลตฟอร์ม เริ่มต้นเพียงหลักสตางค์ ไม่ขอรหัสผ่าน</p>
      <div class="la-drawer-cta-grid">
        <a href="/signup" class="la-btn la-drawer-btn-primary">
          <i class="ri-user-add-fill"></i> <span>สมัครสมาชิกฟรี</span>
        </a>
        <a href="/signin" onclick="laOpenLogin(event)" class="la-btn la-drawer-btn-secondary">
          <i class="ri-login-box-line"></i> <span>เข้าสู่ระบบ</span>
        </a>
      </div>
    </div>
    <?php endif; ?>

    <!-- Quick Social Platform Shortcuts -->
    <div class="la-drawer-section">
      <div class="la-drawer-sec-header">
        <span>แพลตฟอร์มยอดนิยม</span>
        <a href="/services" class="la-drawer-sec-link">ดูทั้งหมด <i class="ri-arrow-right-s-line"></i></a>
      </div>
      <div class="la-drawer-plat-grid">
        <a href="/tiktok" class="la-drawer-plat-item plat-tiktok">
          <div class="plat-ico"><i class="ri-tiktok-fill"></i></div>
          <div class="plat-meta">
            <span class="plat-name">TikTok</span>
            <span class="plat-sub">วิว / ฟอล / ไลค์</span>
          </div>
        </a>
        <a href="/instagram" class="la-drawer-plat-item plat-ig">
          <div class="plat-ico"><i class="ri-instagram-fill"></i></div>
          <div class="plat-meta">
            <span class="plat-name">Instagram</span>
            <span class="plat-sub">ไลค์ / ผู้ติดตาม</span>
          </div>
        </a>
        <a href="/facebook" class="la-drawer-plat-item plat-fb">
          <div class="plat-ico"><i class="ri-facebook-fill"></i></div>
          <div class="plat-meta">
            <span class="plat-name">Facebook</span>
            <span class="plat-sub">เพจ / ปั้มโพสต์</span>
          </div>
        </a>
        <a href="/youtube" class="la-drawer-plat-item plat-yt">
          <div class="plat-ico"><i class="ri-youtube-fill"></i></div>
          <div class="plat-meta">
            <span class="plat-name">YouTube</span>
            <span class="plat-sub">วิว / ซับสไครบ์</span>
          </div>
        </a>
      </div>
      <!-- Secondary Platform Badges -->
      <div class="la-drawer-plat-chips">
        <a href="/twitter" class="plat-chip"><i class="ri-twitter-x-fill"></i> X (Twitter)</a>
        <a href="/shopee" class="plat-chip"><i class="ri-shopping-bag-2-line"></i> Shopee</a>
        <a href="/telegram" class="plat-chip"><i class="ri-telegram-fill"></i> Telegram</a>
        <a href="/spotify" class="plat-chip"><i class="ri-spotify-fill"></i> Spotify</a>
      </div>
    </div>

    <!-- Navigation Menu List -->
    <div class="la-drawer-section">
      <div class="la-drawer-sec-header">
        <span>เมนูนำทาง</span>
      </div>
      <div class="la-drawer-nav-list">
        <?php if ($isLoggedIn): ?>
        <a href="/neworder" class="la-drawer-nav-item <?= ($cur==='neworder')?'active':'' ?>">
          <i class="ri-add-circle-line"></i>
          <span>สั่งซื้อใหม่</span>
          <span class="la-nav-pill-badge hot">ด่วน</span>
        </a>
        <a href="/orders" class="la-drawer-nav-item <?= ($cur==='orders')?'active':'' ?>">
          <i class="ri-file-list-3-line"></i>
          <span>ประวัติคำสั่งซื้อ</span>
        </a>
        <a href="/addfunds" class="la-drawer-nav-item <?= ($cur==='addfunds')?'active':'' ?>">
          <i class="ri-wallet-3-line"></i>
          <span>เติมเงินเข้าระบบ</span>
        </a>
        <a href="/services" class="la-drawer-nav-item <?= ($cur==='services')?'active':'' ?>">
          <i class="ri-store-2-line"></i>
          <span>บริการและราคา</span>
        </a>
        <a href="/tickets" class="la-drawer-nav-item <?= ($cur==='tickets')?'active':'' ?>">
          <i class="ri-customer-service-2-line"></i>
          <span>ตั๋วช่วยเหลือ</span>
        </a>
        <a href="/affiliates" class="la-drawer-nav-item <?= ($cur==='affiliates')?'active':'' ?>">
          <i class="ri-share-forward-line"></i>
          <span>แนะนำเพื่อน (Affiliate)</span>
        </a>
        <a href="/account" class="la-drawer-nav-item <?= ($cur==='account')?'active':'' ?>">
          <i class="ri-user-settings-line"></i>
          <span>ตั้งค่าบัญชี</span>
        </a>
        <a href="/logout" class="la-drawer-nav-item" style="color:#f87171 !important;">
          <i class="ri-logout-box-r-line" style="color:#f87171 !important;"></i>
          <span>ออกจากระบบ</span>
        </a>
        <?php else: ?>
        <a href="/" class="la-drawer-nav-item <?= ($cur==='home'||$cur==='')?'active':'' ?>">
          <i class="ri-home-5-line"></i>
          <span>หน้าแรก</span>
        </a>
        <a href="/services" class="la-drawer-nav-item <?= ($cur==='services')?'active':'' ?>">
          <i class="ri-store-2-line"></i>
          <span>บริการและราคา</span>
          <span class="la-nav-pill-badge hot">ยอดนิยม</span>
        </a>
        <a href="/blog" class="la-drawer-nav-item <?= ($cur==='blog')?'active':'' ?>">
          <i class="ri-article-line"></i>
          <span>บทความ &amp; สาระน่ารู้</span>
          <span class="la-nav-pill-badge new">68 บทความ</span>
        </a>
        <a href="/faq" class="la-drawer-nav-item <?= ($cur==='faq')?'active':'' ?>">
          <i class="ri-question-line"></i>
          <span>คำถามที่พบบ่อย (FAQ)</span>
        </a>
        <a href="/api" class="la-drawer-nav-item <?= ($cur==='api')?'active':'' ?>">
          <i class="ri-code-box-line"></i>
          <span>API สำหรับนักพัฒนา</span>
        </a>
        <a href="/#contact" class="la-drawer-nav-item">
          <i class="ri-customer-service-2-line"></i>
          <span>ติดต่อเรา</span>
        </a>
        <?php endif; ?>
      </div>
    </div>

    <!-- Trust & Guarantees -->
    <div class="la-drawer-trust-box">
      <div class="la-drawer-trust-item">
        <i class="ri-flashlight-line"></i>
        <div>
          <strong>ระบบอัตโนมัติ 100%</strong>
          <span>ส่งยอดไวใน 1-5 นาทีหลังสั่งซื้อ</span>
        </div>
      </div>
      <div class="la-drawer-trust-item">
        <i class="ri-shield-keyhole-line"></i>
        <div>
          <strong>ปลอดภัยสูงสุด</strong>
          <span>ใช้เพียงลิงก์ ไม่ขอรหัสผ่านเด็ดขาด</span>
        </div>
      </div>
      <div class="la-drawer-trust-item">
        <i class="ri-qr-code-line"></i>
        <div>
          <strong>สแกน QR พร้อมเพย์</strong>
          <span>เติมเงินได้ตลอด 24 ชั่วโมง</span>
        </div>
      </div>
    </div>

    <!-- Direct Support CTA -->
    <div class="la-drawer-support-card">
      <div class="support-icon"><i class="ri-customer-service-2-line"></i></div>
      <div class="support-text">
        <strong>ติดต่อฝ่ายบริการลูกค้า</strong>
        <span>มีข้อสงสัยหรือติดปัญหาการสั่งซื้อ แชทได้ 24 ชม.</span>
      </div>
      <a href="/tickets" class="la-btn la-btn-mini support-btn">
        <i class="ri-chat-3-line"></i> <span>เปิดตั๋วติดต่อแอดมิน</span>
      </a>
    </div>

    <!-- Theme Switcher -->
    <div class="la-drawer-theme-box">
      <span class="theme-lbl">ธีมการแสดงผล</span>
      <div class="la-pack-switch" role="group" aria-label="เปลี่ยนธีม">
        <button type="button" data-pack="peak" onclick="laSetPack('peak')" title="Peakerr Lime" aria-label="Peakerr Lime" style="--sw:#020804;--sw2:#8ee31f"></button>
        <button type="button" data-pack="violet" onclick="laSetPack('violet')" title="Night Violet" aria-label="Night Violet" style="--sw:#080614;--sw2:#a855f7"></button>
        <button type="button" data-pack="navy" onclick="laSetPack('navy')" title="Midnight Navy" aria-label="Midnight Navy" style="--sw:#0b1020;--sw2:#3b82f6"></button>
        <button type="button" data-pack="light" onclick="laSetPack('light')" title="Peakerr Soft" aria-label="Peakerr Soft" style="--sw:#f4f7f2;--sw2:#5eb516"></button>
      </div>
    </div>

    <!-- Footer Info -->
    <div class="la-drawer-foot">
      <span>Likes-Auto.com © 2026 · แผงปั้มไลค์อันดับ 1 ในไทย</span>
      <div class="la-drawer-legal-links">
        <a href="/terms">ข้อกำหนด</a> · <a href="/privacy">นโยบายความเป็นส่วนตัว</a> · <a href="/site-map">แผนผังเว็บ</a>
      </div>
    </div>
  </div>
</nav>
