<?php
// Bot-like Quick Order Hero & Platform Explorer Component
$botLikeHeroHtml = <<<'HTML'
<section class="la-hero la-hero-v2 la-hero-quick-order">
    <div class="la-hero-orbs" aria-hidden="true"><span class="a"></span><span class="b"></span><span class="c"></span></div>
    <div class="la-hero-spark" aria-hidden="true">
      <i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i>
    </div>
    <div class="la-hero-mesh" aria-hidden="true"></div>

    <div class="la-wrap la-hero-center-wrap">
      <!-- Bot-like Link & Platform Explorer Card -->
      <div class="la-link-launcher-card">
        <!-- Top Badge -->
        <div class="la-ll-badge">
          <span class="la-ll-badge-pulse"></span>
          <i class="ri-flashlight-fill"></i> เว็บปั๊มไลค์อัตโนมัติ 24 ชม.
        </div>
        
        <!-- Main Title & Subtitle -->
        <h1 class="la-ll-title">
          <span class="la-ll-title-main">ปั๊มไลค์ ปั๊มวิว ปั๊มผู้ติดตาม</span>
          <span class="la-ll-highlight">แค่วางลิงก์</span>
        </h1>
        <p class="la-ll-desc">
          <strong>likes-auto.com</strong> คือเว็บเพิ่มยอดโซเชียลที่สั่งเองได้ สำหรับร้านค้าออนไลน์ เพจ และครีเอเตอร์ วางลิงก์โพสต์หรือโปรไฟล์ เลือกจำนวน จ่ายผ่าน QR พร้อมเพย์ แล้วระบบส่งยอดให้อัตโนมัติ ไม่ต้องให้รหัสผ่าน
        </p>

        <!-- Search & Link Order Box -->
        <div class="la-ll-box">
          <form class="la-ll-form" id="laQuickOrderForm" onsubmit="laSubmitQuickOrder(event)">
            <div class="la-ll-input-wrap">
              <div class="la-ll-input-left">
                <i class="ri-link la-ll-link-icon"></i>
                <input 
                  type="url" 
                  id="laQuickLinkInput" 
                  class="la-ll-input" 
                  placeholder="วางลิงก์โพสต์ วิดีโอ หรือโปรไฟล์ที่ต้องการเพิ่มยอด" 
                  autocomplete="off" 
                  spellcheck="false"
                  oninput="laDetectPlatform(this.value)"
                >
              </div>
              <button type="submit" id="laQuickLinkBtn" class="la-ll-btn-submit">
                <span>ถัดไป</span> <i class="ri-arrow-right-line"></i>
              </button>
            </div>
            <!-- Auto Detection Alert -->
            <div class="la-ll-detection" id="laDetectionBanner" style="display:none;">
              <span class="la-ll-det-badge" id="laDetBadge"><i class="ri-checkbox-circle-fill"></i> <span id="laDetText">ตรวจพบคลิป TikTok</span></span>
              <span class="la-ll-det-hint">พร้อมส่งยอดอัตโนมัติ กด "ถัดไป" เพื่อเลือกบริการ</span>
            </div>
          </form>

          <!-- Platform Chips -->
          <div class="la-ll-chips-wrap">
            <div class="la-ll-chips-label">
              <i class="ri-compass-3-line"></i> ยังไม่มีลิงก์? เลือกแพลตฟอร์มเพื่อดูว่าเพิ่มอะไรได้บ้าง
            </div>
            <div class="la-ll-chips" role="group" aria-label="แพลตฟอร์มโซเชียล">
              <button type="button" class="la-chip active" data-plat="all" onclick="laSelectPlatform('all', this)"><i class="ri-apps-fill"></i> ทั้งหมด</button>
              <button type="button" class="la-chip" data-plat="facebook" onclick="laSelectPlatform('facebook', this)"><i class="ri-facebook-circle-fill" style="color:#1877f2;"></i> Facebook</button>
              <button type="button" class="la-chip" data-plat="tiktok" onclick="laSelectPlatform('tiktok', this)"><i class="ri-tiktok-fill"></i> TikTok</button>
              <button type="button" class="la-chip" data-plat="youtube" onclick="laSelectPlatform('youtube', this)"><i class="ri-youtube-fill" style="color:#ff0000;"></i> YouTube</button>
              <button type="button" class="la-chip" data-plat="instagram" onclick="laSelectPlatform('instagram', this)"><i class="ri-instagram-line" style="color:#e1306c;"></i> Instagram</button>
              <button type="button" class="la-chip" data-plat="threads" onclick="laSelectPlatform('threads', this)"><i class="ri-threads-fill"></i> Threads</button>
              <button type="button" class="la-chip" data-plat="twitter" onclick="laSelectPlatform('twitter', this)"><i class="ri-twitter-x-fill"></i> X (Twitter)</button>
              <button type="button" class="la-chip" data-plat="shopee" onclick="laSelectPlatform('shopee', this)"><i class="ri-shopping-bag-3-fill" style="color:#ee4d2d;"></i> Shopee</button>
              <button type="button" class="la-chip" data-plat="telegram" onclick="laSelectPlatform('telegram', this)"><i class="ri-telegram-fill" style="color:#229ed9;"></i> Telegram</button>
              <button type="button" class="la-chip" data-plat="line" onclick="laSelectPlatform('line', this)"><i class="ri-line-fill" style="color:#06c755;"></i> LINE OA</button>
              <button type="button" class="la-chip" data-plat="traffic" onclick="laSelectPlatform('traffic', this)"><i class="ri-global-line" style="color:#38bdf8;"></i> Website Traffic</button>
              <button type="button" class="la-chip" data-plat="other" onclick="laSelectPlatform('other', this)"><i class="ri-more-fill"></i> แพลตฟอร์มอื่นๆ</button>
            </div>
          </div>
        </div>

        <!-- Price Examples Cards ("ตัวอย่างราคา") -->
        <div class="la-ll-examples">
          <div class="la-ll-examples-head">
            <span class="la-ll-ex-title"><i class="ri-price-tag-3-fill"></i> ตัวอย่างราคาเริ่มต้น</span>
          </div>
          <div class="la-ll-cards-grid" id="laPriceCards">
            <!-- Facebook card -->
            <a href="/facebook" class="la-ll-price-card" data-card-plat="facebook">
              <span class="la-ll-picon" style="background:rgba(24,119,242,0.15); color:#1877f2;"><i class="ri-facebook-circle-fill"></i></span>
              <div class="la-ll-pinfo">
                <span class="la-ll-pname">ปั๊มไลค์ Facebook</span>
                <strong class="la-ll-prate">฿8.74 <small>/ 1,000 ไลค์</small></strong>
              </div>
              <i class="ri-arrow-right-s-line la-ll-parrow"></i>
            </a>
            <!-- TikTok card -->
            <a href="/tiktok" class="la-ll-price-card" data-card-plat="tiktok">
              <span class="la-ll-picon" style="background:rgba(255,255,255,0.1); color:#ffffff;"><i class="ri-tiktok-fill"></i></span>
              <div class="la-ll-pinfo">
                <span class="la-ll-pname">ปั๊มวิว TikTok</span>
                <strong class="la-ll-prate">฿0.38 <small>/ 1,000 วิว</small></strong>
              </div>
              <i class="ri-arrow-right-s-line la-ll-parrow"></i>
            </a>
            <!-- Instagram card -->
            <a href="/instagram" class="la-ll-price-card" data-card-plat="instagram">
              <span class="la-ll-picon" style="background:rgba(225,48,108,0.15); color:#e1306c;"><i class="ri-instagram-fill"></i></span>
              <div class="la-ll-pinfo">
                <span class="la-ll-pname">ปั๊มผู้ติดตาม IG</span>
                <strong class="la-ll-prate">฿14.03 <small>/ 1,000 คน</small></strong>
              </div>
              <i class="ri-arrow-right-s-line la-ll-parrow"></i>
            </a>
            <!-- YouTube card -->
            <a href="/youtube" class="la-ll-price-card" data-card-plat="youtube">
              <span class="la-ll-picon" style="background:rgba(255,0,0,0.15); color:#ff4444;"><i class="ri-youtube-fill"></i></span>
              <div class="la-ll-pinfo">
                <span class="la-ll-pname">ปั๊มวิว YouTube</span>
                <strong class="la-ll-prate">฿16.92 <small>/ 1,000 วิว</small></strong>
              </div>
              <i class="ri-arrow-right-s-line la-ll-parrow"></i>
            </a>
          </div>
        </div>

        <!-- Reseller Banner ("ตัวแทนจำหน่าย") -->
        <a href="/signup?ref=reseller" class="la-ll-reseller-banner">
          <span class="la-ll-reseller-badge"><i class="ri-vip-crown-fill"></i> ตัวแทนจำหน่าย</span>
          <span class="la-ll-reseller-text">เปิดบิลแรก ฿5,000 รับส่วนลดพิเศษ 20% ทุกบริการ พร้อมเชื่อม API ส่งยอดอัตโนมัติ</span>
          <i class="ri-arrow-right-line la-ll-reseller-arrow"></i>
        </a>

        <!-- Live Ticker Inside Centerpiece -->
        <div class="la-live-ticker la-ll-ticker" id="laLiveTicker" aria-live="polite" aria-label="ออเดอร์แบบเรียลไทม์">
          <div class="la-live-ticker-glow" aria-hidden="true"></div>
          <div class="la-live-ticker-scan" aria-hidden="true"></div>
          <div class="la-live-ticker-head">
            <span class="la-live-pulse"><i></i> LIVE</span>
            <b>ออเดอร์ล่าสุดตอนนี้</b>
            <em id="laTickerMeta">อัปเดตทุกไม่กี่วินาที</em>
          </div>
          <div class="la-live-ticker-stage">
            <div class="la-live-ticker-rail" id="laTickerRail"></div>
          </div>
        </div>

        <ul class="la-trust la-ll-trust">
          <li><i class="ri-lock-2-fill"></i> ปลอดภัยสูงสุด SSL</li>
          <li><i class="ri-shield-check-fill"></i> ไม่ขอรหัสผ่าน 100%</li>
          <li><i class="ri-time-fill"></i> ระบบอัตโนมัติ 24 ชม.</li>
        </ul>
      </div>
    </div>
  </section>
HTML;

$botLikeHeroJs = <<<'HTML'
<script>
(function(){
  var platServices = {
    all: [
      { plat: 'facebook', icon: 'ri-facebook-circle-fill', color: '#1877f2', bg: 'rgba(24,119,242,0.15)', name: 'ปั๊มไลค์ Facebook', rate: '฿8.74', unit: '/ 1,000 ไลค์', href: '/facebook' },
      { plat: 'tiktok', icon: 'ri-tiktok-fill', color: '#ffffff', bg: 'rgba(255,255,255,0.1)', name: 'ปั๊มวิว TikTok', rate: '฿0.38', unit: '/ 1,000 วิว', href: '/tiktok' },
      { plat: 'instagram', icon: 'ri-instagram-fill', color: '#e1306c', bg: 'rgba(225,48,108,0.15)', name: 'ปั๊มผู้ติดตาม IG', rate: '฿14.03', unit: '/ 1,000 คน', href: '/instagram' },
      { plat: 'youtube', icon: 'ri-youtube-fill', color: '#ff4444', bg: 'rgba(255,0,0,0.15)', name: 'ปั๊มวิว YouTube', rate: '฿16.92', unit: '/ 1,000 วิว', href: '/youtube' }
    ],
    facebook: [
      { plat: 'facebook', icon: 'ri-thumb-up-fill', color: '#1877f2', bg: 'rgba(24,119,242,0.15)', name: 'ปั๊มไลค์โพสต์ Facebook', rate: '฿8.74', unit: '/ 1,000 ไลค์', href: '/facebook' },
      { plat: 'facebook', icon: 'ri-user-follow-fill', color: '#1877f2', bg: 'rgba(24,119,242,0.15)', name: 'ปั๊มผู้ติดตามเพจ Facebook', rate: '฿32.50', unit: '/ 1,000 คน', href: '/facebook' },
      { plat: 'facebook', icon: 'ri-video-fill', color: '#1877f2', bg: 'rgba(24,119,242,0.15)', name: 'ปั๊มวิวคลิป Reels Facebook', rate: '฿2.10', unit: '/ 1,000 วิว', href: '/facebook' },
      { plat: 'facebook', icon: 'ri-chat-1-fill', color: '#1877f2', bg: 'rgba(24,119,242,0.15)', name: 'ปั๊มคอมเมนต์ Facebook คนไทย', rate: '฿45.00', unit: '/ 100 เมนต์', href: '/facebook' }
    ],
    tiktok: [
      { plat: 'tiktok', icon: 'ri-eye-fill', color: '#00f2fe', bg: 'rgba(0,242,254,0.15)', name: 'ปั๊มวิว TikTok เร็วสุด', rate: '฿0.38', unit: '/ 1,000 วิว', href: '/tiktok' },
      { plat: 'tiktok', icon: 'ri-heart-fill', color: '#fe2c55', bg: 'rgba(254,44,85,0.15)', name: 'ปั๊มหัวใจ TikTok (ไลค์)', rate: '฿12.60', unit: '/ 1,000 ไลค์', href: '/tiktok' },
      { plat: 'tiktok', icon: 'ri-user-add-fill', color: '#ffffff', bg: 'rgba(255,255,255,0.15)', name: 'ปั๊มผู้ติดตาม TikTok', rate: '฿58.00', unit: '/ 1,000 ฟอล', href: '/tiktok' },
      { plat: 'tiktok', icon: 'ri-share-forward-fill', color: '#00f2fe', bg: 'rgba(0,242,254,0.15)', name: 'ปั๊มแชร์ TikTok / บันทึก', rate: '฿3.50', unit: '/ 1,000 ครั้ง', href: '/tiktok' }
    ],
    youtube: [
      { plat: 'youtube', icon: 'ri-youtube-fill', color: '#ff0000', bg: 'rgba(255,0,0,0.15)', name: 'ปั๊มวิว YouTube เสถียร', rate: '฿16.92', unit: '/ 1,000 วิว', href: '/youtube' },
      { plat: 'youtube', icon: 'ri-user-star-fill', color: '#ff4444', bg: 'rgba(255,0,0,0.15)', name: 'ปั๊มผู้ติดตาม YouTube (Sub)', rate: '฿85.00', unit: '/ 1,000 ซับ', href: '/youtube' },
      { plat: 'youtube', icon: 'ri-thumb-up-fill', color: '#ff4444', bg: 'rgba(255,0,0,0.15)', name: 'ปั๊มไลค์วิดีโอ YouTube', rate: '฿19.20', unit: '/ 1,000 ไลค์', href: '/youtube' },
      { plat: 'youtube', icon: 'ri-play-circle-fill', color: '#ff4444', bg: 'rgba(255,0,0,0.15)', name: 'ปั๊มชั่วโมงดู YouTube 4,000 ชม.', rate: '฿280.00', unit: '/ 1,000 ชม.', href: '/youtube' }
    ],
    instagram: [
      { plat: 'instagram', icon: 'ri-user-follow-fill', color: '#e1306c', bg: 'rgba(225,48,108,0.15)', name: 'ปั๊มผู้ติดตาม IG (คนจริง)', rate: '฿14.03', unit: '/ 1,000 คน', href: '/instagram' },
      { plat: 'instagram', icon: 'ri-heart-3-fill', color: '#e1306c', bg: 'rgba(225,48,108,0.15)', name: 'ปั๊มไลค์โพสต์ Instagram', rate: '฿6.80', unit: '/ 1,000 ไลค์', href: '/instagram' },
      { plat: 'instagram', icon: 'ri-video-line', color: '#e1306c', bg: 'rgba(225,48,108,0.15)', name: 'ปั๊มวิวคลิป Reels IG', rate: '฿1.50', unit: '/ 1,000 วิว', href: '/instagram' },
      { plat: 'instagram', icon: 'ri-eye-line', color: '#e1306c', bg: 'rgba(225,48,108,0.15)', name: 'ปั๊มวิว Story Instagram', rate: '฿2.20', unit: '/ 1,000 วิว', href: '/instagram' }
    ],
    threads: [
      { plat: 'threads', icon: 'ri-threads-fill', color: '#ffffff', bg: 'rgba(255,255,255,0.12)', name: 'ปั๊มผู้ติดตาม Threads', rate: '฿25.00', unit: '/ 1,000 ฟอล', href: '/services?cat=threads' },
      { plat: 'threads', icon: 'ri-heart-line', color: '#ffffff', bg: 'rgba(255,255,255,0.12)', name: 'ปั๊มไลค์โพสต์ Threads', rate: '฿12.00', unit: '/ 1,000 ไลค์', href: '/services?cat=threads' },
      { plat: 'threads', icon: 'ri-repeat-line', color: '#ffffff', bg: 'rgba(255,255,255,0.12)', name: 'ปั๊มรีโพสต์ Threads', rate: '฿18.00', unit: '/ 1,000 รี', href: '/services?cat=threads' }
    ],
    twitter: [
      { plat: 'twitter', icon: 'ri-twitter-x-fill', color: '#ffffff', bg: 'rgba(255,255,255,0.12)', name: 'ปั๊มผู้ติดตาม X (Twitter)', rate: '฿38.00', unit: '/ 1,000 ฟอล', href: '/services?cat=twitter' },
      { plat: 'twitter', icon: 'ri-heart-fill', color: '#f43f5e', bg: 'rgba(244,63,94,0.15)', name: 'ปั๊มไลค์ทวีต X', rate: '฿11.50', unit: '/ 1,000 ไลค์', href: '/services?cat=twitter' },
      { plat: 'twitter', icon: 'ri-repeat-2-line', color: '#22c55e', bg: 'rgba(34,197,94,0.15)', name: 'ปั๊มรีทวีต X (Retweet)', rate: '฿15.00', unit: '/ 1,000 รี', href: '/services?cat=twitter' },
      { plat: 'twitter', icon: 'ri-eye-line', color: '#38bdf8', bg: 'rgba(56,189,248,0.15)', name: 'ปั๊มวิว Impression ทวีต', rate: '฿1.80', unit: '/ 1,000 วิว', href: '/services?cat=twitter' }
    ],
    shopee: [
      { plat: 'shopee', icon: 'ri-shopping-bag-3-fill', color: '#ee4d2d', bg: 'rgba(238,77,45,0.15)', name: 'ปั๊มผู้ติดตามร้านค้า Shopee', rate: '฿42.00', unit: '/ 1,000 ฟอล', href: '/services?cat=shopee' },
      { plat: 'shopee', icon: 'ri-heart-fill', color: '#ee4d2d', bg: 'rgba(238,77,45,0.15)', name: 'ปั๊มถูกใจสินค้า Shopee', rate: '฿18.50', unit: '/ 1,000 ไลค์', href: '/services?cat=shopee' },
      { plat: 'shopee', icon: 'ri-eye-fill', color: '#ee4d2d', bg: 'rgba(238,77,45,0.15)', name: 'ปั๊มคนดู Shopee Live', rate: '฿28.00', unit: '/ 1,000 วิว', href: '/services?cat=shopee' }
    ],
    telegram: [
      { plat: 'telegram', icon: 'ri-telegram-fill', color: '#229ed9', bg: 'rgba(34,158,217,0.15)', name: 'ปั๊มสมาชิก Telegram Channel', rate: '฿19.50', unit: '/ 1,000 สมาชิก', href: '/services?cat=telegram' },
      { plat: 'telegram', icon: 'ri-eye-line', color: '#229ed9', bg: 'rgba(34,158,217,0.15)', name: 'ปั๊มวิวโพสต์ Telegram', rate: '฿0.95', unit: '/ 1,000 วิว', href: '/services?cat=telegram' },
      { plat: 'telegram', icon: 'ri-emotion-line', color: '#229ed9', bg: 'rgba(34,158,217,0.15)', name: 'ปั๊ม Reaction โพสต์ Telegram', rate: '฿2.50', unit: '/ 1,000 รีแอค', href: '/services?cat=telegram' }
    ],
    line: [
      { plat: 'line', icon: 'ri-line-fill', color: '#06c755', bg: 'rgba(6,199,85,0.15)', name: 'ปั๊มเพื่อน LINE Official Account', rate: '฿85.00', unit: '/ 1,000 คน', href: '/services?cat=line' },
      { plat: 'line', icon: 'ri-heart-fill', color: '#06c755', bg: 'rgba(6,199,85,0.15)', name: 'ปั๊มไลค์โพสต์ LINE VOOM', rate: '฿22.00', unit: '/ 1,000 ไลค์', href: '/services?cat=line' }
    ],
    traffic: [
      { plat: 'traffic', icon: 'ri-global-line', color: '#38bdf8', bg: 'rgba(56,189,248,0.15)', name: 'คนเข้าเว็บไซต์จากทั่วโลก', rate: '฿8.00', unit: '/ 1,000 วิสิท', href: '/services?cat=traffic' },
      { plat: 'traffic', icon: 'ri-google-fill', color: '#ea4335', bg: 'rgba(234,67,53,0.15)', name: 'Traffic เข้าจาก Google Search', rate: '฿16.50', unit: '/ 1,000 คลิก', href: '/services?cat=traffic' }
    ],
    other: [
      { plat: 'other', icon: 'ri-apps-2-line', color: '#8ee31f', bg: 'rgba(142,227,31,0.15)', name: 'บริการทั้งหมดกว่า 100+ รายการ', rate: 'เริ่มต้น ฿0.38', unit: '', href: '/services' }
    ]
  };

  window.laSelectPlatform = function(plat, btn){
    document.querySelectorAll('.la-chip').forEach(function(c){ c.classList.remove('active'); });
    if (btn) btn.classList.add('active');
    
    var list = platServices[plat] || platServices.all;
    var container = document.getElementById('laPriceCards');
    if (!container) return;
    
    container.style.opacity = '0';
    container.style.transform = 'translateY(4px)';
    
    setTimeout(function(){
      var html = '';
      list.forEach(function(item){
        html += '<a href="' + item.href + '" class="la-ll-price-card" data-card-plat="' + item.plat + '">' +
          '<span class="la-ll-picon" style="background:' + item.bg + '; color:' + item.color + ';"><i class="' + item.icon + '"></i></span>' +
          '<div class="la-ll-pinfo">' +
            '<span class="la-ll-pname">' + item.name + '</span>' +
            '<strong class="la-ll-prate">' + item.rate + (item.unit ? ' <small>' + item.unit + '</small>' : '') + '</strong>' +
          '</div>' +
          '<i class="ri-arrow-right-s-line la-ll-parrow"></i>' +
        '</a>';
      });
      container.innerHTML = html;
      container.style.opacity = '1';
      container.style.transform = 'translateY(0)';
    }, 100);
  };

  window.laDetectPlatform = function(url){
    url = (url || '').trim().toLowerCase();
    var banner = document.getElementById('laDetectionBanner');
    var badge = document.getElementById('laDetBadge');
    var text = document.getElementById('laDetText');
    if (!banner || !badge || !text) return;

    if (!url) {
      banner.style.display = 'none';
      return;
    }

    var platName = '';
    var platKey = '';
    if (url.indexOf('tiktok.com') !== -1) {
      platName = 'TikTok'; platKey = 'tiktok';
    } else if (url.indexOf('facebook.com') !== -1 || url.indexOf('fb.watch') !== -1 || url.indexOf('fb.me') !== -1) {
      platName = 'Facebook'; platKey = 'facebook';
    } else if (url.indexOf('instagram.com') !== -1 || url.indexOf('instagr.am') !== -1) {
      platName = 'Instagram'; platKey = 'instagram';
    } else if (url.indexOf('youtube.com') !== -1 || url.indexOf('youtu.be') !== -1) {
      platName = 'YouTube'; platKey = 'youtube';
    } else if (url.indexOf('x.com') !== -1 || url.indexOf('twitter.com') !== -1) {
      platName = 'X (Twitter)'; platKey = 'twitter';
    } else if (url.indexOf('threads.net') !== -1) {
      platName = 'Threads'; platKey = 'threads';
    } else if (url.indexOf('shopee.co.th') !== -1) {
      platName = 'Shopee'; platKey = 'shopee';
    } else if (url.indexOf('t.me') !== -1 || url.indexOf('telegram') !== -1) {
      platName = 'Telegram'; platKey = 'telegram';
    } else if (url.indexOf('line.me') !== -1) {
      platName = 'LINE OA'; platKey = 'line';
    }

    if (platName) {
      text.textContent = 'ตรวจพบลิงก์ ' + platName + ' สำเร็จ!';
      banner.style.display = 'flex';
      var matchingChip = document.querySelector('.la-chip[data-plat="' + platKey + '"]');
      if (matchingChip && !matchingChip.classList.contains('active')) {
        laSelectPlatform(platKey, matchingChip);
      }
    } else {
      banner.style.display = 'none';
    }
  };

  window.laSubmitQuickOrder = function(e){
    if (e) e.preventDefault();
    var inp = document.getElementById('laQuickLinkInput');
    var val = inp ? inp.value.trim() : '';
    if (!val) {
      if (inp) {
        inp.focus();
        inp.classList.add('la-shake');
        setTimeout(function(){ inp.classList.remove('la-shake'); }, 500);
      }
      return;
    }
    // Route to services with prefilled link
    window.location.href = '/services?link=' + encodeURIComponent(val);
  };
})();
</script>
HTML;
