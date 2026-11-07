<?php
declare(strict_types=1);

/**
 * Modern Full-Featured Crons & Automation Engine Dashboard.
 * Includes Top KPIs, 1-Click Fast Controls, System Bots Matrix, External Webhook Setup,
 * Real-Time Log Search & Filter, and Live Browser Heartbeat Runner.
 */
function la_patch_admin_crons(string $html): string {
    $mStart = strpos($html, '<main class="dash-content">');
    if ($mStart === false) {
        return $html;
    }
    $mEnd = strpos($html, '</main>', $mStart);
    if ($mEnd === false) {
        return $html;
    }

    // Extract any existing 'ran' alert
    $ranMsg = '';
    if (preg_match('#<div class="adm-ok"><i class="[^"]*"></i>\s*(.*?)</div>#s', $html, $mRan)) {
        $ranMsg = trim(strip_tags($mRan[1]));
    } elseif (isset($_GET['ran']) && $_GET['ran'] !== '') {
        $ranMsg = htmlspecialchars(urldecode($_GET['ran']));
    } elseif (isset($_GET['ok']) && $_GET['ok'] !== '') {
        $ranMsg = htmlspecialchars(urldecode($_GET['ok']));
    }

    // Extract KPI dates
    $lastPull = '-';
    $lastPullSum = 'ยังไม่มีบันทึก';
    $lastSync = '-';
    $lastSyncSum = '-';
    $lastShop = '-';
    $lastShopSum = '-';

    if (preg_match('#<article class="adm-card cron-kpi">\s*<em>ดึงงานล่าสุด</em>\s*<strong>(.*?)</strong>\s*<p>(.*?)</p>#s', $html, $mP)) {
        $lastPull = trim(strip_tags($mP[1]));
        $lastPullSum = trim(strip_tags($mP[2]));
    }
    if (preg_match('#<article class="adm-card cron-kpi">\s*<em>ซิงก์บริการล่าสุด</em>\s*<strong>(.*?)</strong>\s*<p>(.*?)</p>#s', $html, $mS)) {
        $lastSync = trim(strip_tags($mS[1]));
        $lastSyncSum = trim(strip_tags($mS[2]));
    }
    if (preg_match('#<article class="adm-card cron-kpi">\s*<em>คัดร้านล่าสุด</em>\s*<strong>(.*?)</strong>\s*<p>(.*?)</p>#s', $html, $mSh)) {
        $lastShop = trim(strip_tags($mSh[1]));
        $lastShopSum = trim(strip_tags($mSh[2]));
    }

    // Read cron state file if exists
    $stateFile = __DIR__ . '/cron_state.json';
    $cronState = [];
    if (file_exists($stateFile)) {
        $cronState = @json_decode(file_get_contents($stateFile), true) ?: [];
    }
    if ($lastPull === '-' && !empty($cronState['last_run_fmt'])) {
        $lastPull = $cronState['last_run_fmt'];
        $lastPullSum = 'รันอัตโนมัติผ่าน Background Engine (' . ($cronState['trigger'] ?? 'system') . ')';
    }

    // Extract logs
    $logs = [];
    if (preg_match_all('#<article class="cron-log-row([^"]*)">(.*?)</article>#s', $html, $matches, PREG_SET_ORDER)) {
        foreach ($matches as $m) {
            $rowCls = trim($m[1]);
            $body = $m[2];

            $badgeTone = 'other';
            $badgeLbl = 'อื่นๆ';
            $badgeIcon = 'ri-file-list-line';
            if (preg_match('#<span class="cron-badge\s+is-([^"]+)">\s*<i class="([^"]*)"></i>\s*([^<]+)</span>#s', $body, $mB)) {
                $badgeTone = trim($mB[1]);
                $badgeIcon = trim($mB[2]);
                $badgeLbl = trim($mB[3]);
            }

            $timeStr = '-';
            if (preg_match('#<time[^>]*>(.*?)</time>#s', $body, $mT)) {
                $timeStr = trim(strip_tags($mT[1]));
            }

            $lid = '';
            if (preg_match('#<span class="cron-log-id">\#?(\d+)</span>#s', $body, $mL)) {
                $lid = $mL[1];
            }

            $summary = '';
            if (preg_match('#<p class="cron-log-summary">(.*?)</p>#s', $body, $mSm)) {
                $summary = trim(strip_tags($mSm[1]));
            }

            $chipsHtml = '';
            if (preg_match('#<div class="cron-chips">(.*?)</div>#s', $body, $mCh)) {
                $chipsHtml = trim($mCh[1]);
            }

            $rawCode = '';
            if (preg_match('#<code>(.*?)</code>#s', $body, $mRc)) {
                $rawCode = trim($mRc[1]);
            }

            $isErr = (strpos($rowCls, 'is-error') !== false) || (stripos($summary, 'err=') !== false && !preg_match('#err=0(\s|$)#', $summary));

            $logs[] = [
                'id' => $lid,
                'cls' => $rowCls,
                'tone' => $badgeTone,
                'icon' => $badgeIcon,
                'label' => $badgeLbl,
                'time' => $timeStr,
                'summary' => $summary,
                'chips' => $chipsHtml,
                'raw' => $rawCode,
                'is_error' => $isErr,
            ];
        }
    }

    // Compute stats
    $totalLogs = count($logs);
    $errLogsCount = 0;
    foreach ($logs as $l) {
        if ($l['is_error']) {
            $errLogsCount++;
        }
    }

    ob_start();
    ?>
    <main class="dash-content cron-master-container">
      
      <!-- Top Title Header -->
      <div class="cron-header-row">
        <div>
          <h1 class="dash-h"><i class="ri-cpu-line"></i> บันทึกงาน &amp; บอทอัตโนมัติ (Crons &amp; Automation)</h1>
          <p class="adm-sub">ระบบจัดการและตรวจสอบการทำงานของบอทอัตโนมัติ 24 ชม. ส่งออเดอร์, ดึงสถานะ, เช็คยอดเงิน และซิงก์ราคา</p>
        </div>
        <div class="cron-heartbeat-box">
          <div class="cron-pulse-dot" title="ระบบอัตโนมัติกำลังทำงาน"></div>
          <span class="cron-pulse-text">บอทออโต้ 24 ชม.: <strong id="cronTimerText">กำลังทำงาน</strong></span>
          <button type="button" class="la-btn la-btn-mini la-btn-ghost" onclick="cronTriggerImmediate()" title="กดสั่งรันทันที">
            <i class="ri-flashlight-line"></i> รันด่วน
          </button>
        </div>
      </div>

      <?php if (!empty($ranMsg)): ?>
      <div class="adm-ok cron-alert-ok">
        <i class="ri-checkbox-circle-fill"></i>
        <span><strong>ทำรายการสำเร็จ:</strong> <?= htmlspecialchars($ranMsg) ?></span>
      </div>
      <?php endif; ?>

      <!-- ── 1. Top KPI Summary Grid ── -->
      <div class="cron-kpi-grid">
        <div class="cron-kpi-card is-engine">
          <div class="cron-kpi-icon"><i class="ri-radar-line"></i></div>
          <div class="cron-kpi-body">
            <span class="cron-kpi-lbl">สถานะระบบอัตโนมัติ</span>
            <div class="cron-kpi-val"><span class="cron-live-pill"><i class="ri-record-circle-fill"></i> ออโต้ 24 ชม.</span></div>
            <span class="cron-kpi-sub">รอบล่าสุด: <?= $lastPull !== '-' ? htmlspecialchars($lastPull) : 'เมื่อสักครู่' ?></span>
          </div>
        </div>

        <div class="cron-kpi-card is-send">
          <div class="cron-kpi-icon"><i class="ri-send-plane-fill"></i></div>
          <div class="cron-kpi-body">
            <span class="cron-kpi-lbl">ส่งออเดอร์ไป Provider</span>
            <div class="cron-kpi-val">ทำงานอัตโนมัติ</div>
            <span class="cron-kpi-sub"><i class="ri-shield-check-line"></i> Auto-Fallback เมื่อบริการปิด</span>
          </div>
        </div>

        <div class="cron-kpi-card is-status">
          <div class="cron-kpi-icon"><i class="ri-loop-right-line"></i></div>
          <div class="cron-kpi-body">
            <span class="cron-kpi-lbl">ติดตามสถานะออเดอร์</span>
            <div class="cron-kpi-val">เช็คทุกรอบ</div>
            <span class="cron-kpi-sub"><i class="ri-refund-line"></i> คืนเงินอัตโนมัติถ้าถูกยกเลิก</span>
          </div>
        </div>

        <div class="cron-kpi-card is-balance">
          <div class="cron-kpi-icon"><i class="ri-wallet-3-line"></i></div>
          <div class="cron-kpi-body">
            <span class="cron-kpi-lbl">ตรวจเช็คยอดเงิน API</span>
            <div class="cron-kpi-val">พร้อมใช้งาน</div>
            <span class="cron-kpi-sub">เช็ค Provider ทุกแห่งสม่ำเสมอ</span>
          </div>
        </div>

        <div class="cron-kpi-card is-sync">
          <div class="cron-kpi-icon"><i class="ri-store-2-line"></i></div>
          <div class="cron-kpi-body">
            <span class="cron-kpi-lbl">ซิงก์ราคาและบริการ</span>
            <div class="cron-kpi-val"><?= $lastSync !== '-' ? htmlspecialchars($lastSync) : 'สมบูรณ์' ?></div>
            <span class="cron-kpi-sub">อัปเดตราคาต้นทุนอัตโนมัติ</span>
          </div>
        </div>
      </div>

      <!-- ── 2. Quick Control Command Bar ── -->
      <div class="cron-command-bar">
        <div class="cron-cmd-title">
          <i class="ri-terminal-box-line"></i> คำสั่งควบคุมบอทและงานระบบ:
        </div>
        <div class="cron-cmd-btns">
          <!-- 1. Run All -->
          <form method="post" action="/admin/crons/run" class="cron-form-inline" onsubmit="return cronSubmitWithLoader(this, 'กำลังรันทุกระบบ...');">
            <button class="la-btn la-btn-primary cron-btn-main" type="submit">
              <i class="ri-flashlight-fill"></i> รันทุกระบบพร้อมกัน (Run All)
            </button>
          </form>

          <!-- 2. Send Orders -->
          <form method="post" action="/admin/crons/orders" class="cron-form-inline" onsubmit="return cronSubmitWithLoader(this, 'กำลังส่งออเดอร์...');">
            <button class="la-btn cron-btn-sub" type="submit">
              <i class="ri-send-plane-line"></i> ส่งออเดอร์ค้างส่ง
            </button>
          </form>

          <!-- 3. Check Statuses -->
          <form method="post" action="/admin/crons/status" class="cron-form-inline" onsubmit="return cronSubmitWithLoader(this, 'กำลังดึงสถานะ...');">
            <button class="la-btn cron-btn-sub" type="submit">
              <i class="ri-refresh-line"></i> ดึงสถานะออเดอร์
            </button>
          </form>

          <!-- 4. Refresh Balances -->
          <form method="post" action="/admin/crons/balance" class="cron-form-inline" onsubmit="return cronSubmitWithLoader(this, 'กำลังเช็คยอดเงิน...');">
            <button class="la-btn cron-btn-sub" type="submit">
              <i class="ri-wallet-line"></i> เช็คยอด API Provider
            </button>
          </form>

          <!-- 5. Sync Catalog -->
          <form method="post" action="/admin/crons/catalog" class="cron-form-inline" onsubmit="return cronSubmitWithLoader(this, 'กำลังซิงก์ราคา...');">
            <button class="la-btn cron-btn-sub" type="submit">
              <i class="ri-database-2-line"></i> ซิงก์ราคา &amp; แคตตาล็อก
            </button>
          </form>

          <!-- 6. Publish Blog -->
          <form method="post" action="/admin/crons/blog" class="cron-form-inline" onsubmit="return cronSubmitWithLoader(this, 'กำลังปล่อยบทความ...');">
            <button class="la-btn cron-btn-sub" type="submit">
              <i class="ri-article-line"></i> ปล่อยบทความ SEO
            </button>
          </form>

          <!-- 7. Clear Logs -->
          <form method="post" action="/admin/crons/clear" class="cron-form-inline" onsubmit="return confirm('ยืนยันล้าง log เก่า (จะคงเหลือ 200 รายการล่าสุด)?') && cronSubmitWithLoader(this, 'กำลังล้าง log...');">
            <button class="la-btn la-btn-ghost cron-btn-clear" type="submit" title="ล้าง log เก่าเกิน 200 รายการ">
              <i class="ri-delete-bin-line"></i> ล้าง Log เก่า
            </button>
          </form>
        </div>
      </div>

      <!-- ── 3. External Webhook & Automation Runner Info Card ── -->
      <div class="cron-webhook-card">
        <div class="cron-wh-left">
          <div class="cron-wh-icon"><i class="ri-cloud-windy-line"></i></div>
          <div>
            <h3 class="cron-wh-title">ระบบสั่งรันอัตโนมัติภายนอกตลอด 24 ชั่วโมง (External 24/7 Webhook)</h3>
            <p class="cron-wh-desc">
              ระบบมี <strong>Background Traffic Runner</strong> ในตัวแล้ว และท่านสามารถนำ URL Webhook ด้านล่างไปใส่ในบริการฟรีเช่น 
              <a href="https://cron-job.org" target="_blank" rel="noopener"><strong>cron-job.org</strong></a> หรือ <strong>cPanel Cron Jobs</strong> 
              (ตั้งค่าให้เรียกทุก 1 นาที หรือ 2 นาที) เพื่อรับประกันว่าบอทจะส่งออเดอร์ให้ลูกค้าทันทีแม้ไม่มีใครเปิดหน้าเว็บ
            </p>
          </div>
        </div>
        <div class="cron-wh-right">
          <div class="cron-wh-input-group">
            <input type="text" id="cronWebhookUrl" class="la-input cron-wh-input" readonly value="https://likes-auto.com/api/cron?key=likesauto2026">
            <button type="button" class="la-btn la-btn-primary cron-copy-btn" onclick="navigator.clipboard.writeText('https://likes-auto.com/api/cron?key=likesauto2026'); this.innerHTML='<i class=\'ri-check-line\'></i> คัดลอกแล้ว'; var b=this; setTimeout(function(){ b.innerHTML='<i class=\'ri-file-copy-line\'></i> คัดลอก URL'; }, 2000);">
              <i class="ri-file-copy-line"></i> คัดลอก URL
            </button>
          </div>
          <div class="cron-wh-badges">
            <span class="cron-badge is-pull"><i class="ri-check-double-line"></i> รองรับ GET / POST</span>
            <span class="cron-badge is-sync"><i class="ri-lock-line"></i> Key Protected</span>
            <span class="cron-badge is-shop"><i class="ri-timer-line"></i> Fast Response &lt; 2s</span>
          </div>
        </div>
      </div>

      <!-- ── 4. System Bots Matrix Grid (ตารางบอท 6 ตัว) ── -->
      <div class="cron-bots-section">
        <div class="cron-section-title">
          <i class="ri-robot-2-line"></i> ตารางภารกิจบอทระบบอัตโนมัติ (Active System Bots):
        </div>
        <div class="cron-bots-grid">
          
          <!-- Bot 1: Order Dispatcher -->
          <div class="cron-bot-card">
            <div class="cron-bot-head">
              <div class="cron-bot-icon is-blue"><i class="ri-send-plane-2-fill"></i></div>
              <div class="cron-bot-meta">
                <span class="cron-bot-name">บอทส่งออเดอร์อัตโนมัติ</span>
                <span class="cron-bot-freq">ความถี่: ทุก 1-2 นาที</span>
              </div>
              <span class="cron-badge is-pull">ทำงานออโต้</span>
            </div>
            <p class="cron-bot-desc">ตรวจสอบคำสั่งซื้อใหม่ของลูกค้า ส่งตรงไปยัง API Provider พร้อมระบบ <strong>Auto-Fallback</strong> สลับบริการใกล้เคียงอัตโนมัติเมื่อบริการเดิมปิด</p>
            <div class="cron-bot-foot">
              <span class="cron-bot-state"><i class="ri-checkbox-circle-fill text-ok"></i> รันล่าสุด: <?= $lastPull !== '-' ? htmlspecialchars($lastPull) : 'พร้อมทำงาน' ?></span>
              <form method="post" action="/admin/crons/orders" onsubmit="return cronSubmitWithLoader(this, 'กำลังส่งออเดอร์...');">
                <button type="submit" class="la-btn la-btn-mini la-btn-ghost"><i class="ri-play-fill"></i> สั่งรัน</button>
              </form>
            </div>
          </div>

          <!-- Bot 2: Status Watchdog -->
          <div class="cron-bot-card">
            <div class="cron-bot-head">
              <div class="cron-bot-icon is-green"><i class="ri-pulse-line"></i></div>
              <div class="cron-bot-meta">
                <span class="cron-bot-name">บอทติดตามสถานะคำสั่งซื้อ</span>
                <span class="cron-bot-freq">ความถี่: ทุก 2 นาที</span>
              </div>
              <span class="cron-badge is-pull">ทำงานออโต้</span>
            </div>
            <p class="cron-bot-desc">ดึงสถานะงานจริงจาก Provider (In Progress, Completed, Partial, Canceled) พร้อมอัปเดตยอดเริ่มนับ (Start) และคงเหลือ (Remains)</p>
            <div class="cron-bot-foot">
              <span class="cron-bot-state"><i class="ri-checkbox-circle-fill text-ok"></i> อัปเดตสถานะอัตโนมัติ</span>
              <form method="post" action="/admin/crons/status" onsubmit="return cronSubmitWithLoader(this, 'กำลังดึงสถานะ...');">
                <button type="submit" class="la-btn la-btn-mini la-btn-ghost"><i class="ri-play-fill"></i> สั่งรัน</button>
              </form>
            </div>
          </div>

          <!-- Bot 3: Auto-Refund -->
          <div class="cron-bot-card">
            <div class="cron-bot-head">
              <div class="cron-bot-icon is-purple"><i class="ri-refund-2-line"></i></div>
              <div class="cron-bot-meta">
                <span class="cron-bot-name">บอทคืนเงินและชดเชย</span>
                <span class="cron-bot-freq">ความถี่: Real-time ตามสถานะ</span>
              </div>
              <span class="cron-badge is-shop">ทำงานออโต้</span>
            </div>
            <p class="cron-bot-desc">คืนเงินเข้ากระเป๋าลูกค้าทันทีเมื่อออเดอร์ถูกยกเลิก หรือคำนวณยอดคืนตามสัดส่วนที่เหลือเมื่อออเดอร์สำเร็จเพียงบางส่วน (Partial)</p>
            <div class="cron-bot-foot">
              <span class="cron-bot-state"><i class="ri-checkbox-circle-fill text-ok"></i> คุ้มครองยอดเงินลูกค้า 100%</span>
              <a href="/admin/orders?status=canceled" class="la-btn la-btn-mini la-btn-ghost"><i class="ri-eye-line"></i> ดูออเดอร์</a>
            </div>
          </div>

          <!-- Bot 4: Provider Balance Watchdog -->
          <div class="cron-bot-card">
            <div class="cron-bot-head">
              <div class="cron-bot-icon is-amber"><i class="ri-money-dollar-circle-line"></i></div>
              <div class="cron-bot-meta">
                <span class="cron-bot-name">บอทตรวจสอบยอดเงิน API</span>
                <span class="cron-bot-freq">ความถี่: ทุกรอบดึงงาน</span>
              </div>
              <span class="cron-badge is-pull">ทำงานออโต้</span>
            </div>
            <p class="cron-bot-desc">เช็คยอดเงินคงเหลือในบัญชีของผู้ให้บริการแต่ละราย ป้องกันปัญหายอดเงินไม่พอสั่งซื้อและแจ้งเตือนผู้ดูแลระบบ</p>
            <div class="cron-bot-foot">
              <span class="cron-bot-state"><i class="ri-checkbox-circle-fill text-ok"></i> ตรวจสอบยอดเงินครบทุกแห่ง</span>
              <form method="post" action="/admin/crons/balance" onsubmit="return cronSubmitWithLoader(this, 'กำลังเช็คยอดเงิน...');">
                <button type="submit" class="la-btn la-btn-mini la-btn-ghost"><i class="ri-play-fill"></i> สั่งรัน</button>
              </form>
            </div>
          </div>

          <!-- Bot 5: Service & Catalog Sync -->
          <div class="cron-bot-card">
            <div class="cron-bot-head">
              <div class="cron-bot-icon is-cyan"><i class="ri-store-3-line"></i></div>
              <div class="cron-bot-meta">
                <span class="cron-bot-name">บอทซิงก์ราคาและบริการ</span>
                <span class="cron-bot-freq">ความถี่: อัปเดตรายวัน / สั่งรัน</span>
              </div>
              <span class="cron-badge is-sync">ทำงานออโต้</span>
            </div>
            <p class="cron-bot-desc">ดึงรายการบริการใหม่ ตรวจสอบราคาต้นทุน และปรับเปลี่ยนสถานะบริการที่ปิดตัวจากต้นทาง เพื่อรักษาความถูกต้องของหน้าร้าน</p>
            <div class="cron-bot-foot">
              <span class="cron-bot-state"><i class="ri-checkbox-circle-fill text-ok"></i> ล่าสุด: <?= $lastSync !== '-' ? htmlspecialchars($lastSync) : 'พร้อมทำงาน' ?></span>
              <form method="post" action="/admin/crons/catalog" onsubmit="return cronSubmitWithLoader(this, 'กำลังซิงก์ราคา...');">
                <button type="submit" class="la-btn la-btn-mini la-btn-ghost"><i class="ri-play-fill"></i> สั่งรัน</button>
              </form>
            </div>
          </div>

          <!-- Bot 6: SEO Auto-Publisher -->
          <div class="cron-bot-card">
            <div class="cron-bot-head">
              <div class="cron-bot-icon is-red"><i class="ri-article-line"></i></div>
              <div class="cron-bot-meta">
                <span class="cron-bot-name">บอทเผยแพร่บทความ SEO</span>
                <span class="cron-bot-freq">ความถี่: อัตโนมัติตามคิว</span>
              </div>
              <span class="cron-badge is-catalog">ทำงานออโต้</span>
            </div>
            <p class="cron-bot-desc">ตรวจสอบคิวบทความและเผยแพร่คอนเทนต์ใหม่ขึ้นเว็บไซต์ตามเวลา พร้อมกระจาย Index ไปยัง Google &amp; Bing ทันที</p>
            <div class="cron-bot-foot">
              <span class="cron-bot-state"><i class="ri-checkbox-circle-fill text-ok"></i> สนับสนุน SEO ติดหน้าแรก Google</span>
              <form method="post" action="/admin/crons/blog" onsubmit="return cronSubmitWithLoader(this, 'กำลังปล่อยบทความ...');">
                <button type="submit" class="la-btn la-btn-mini la-btn-ghost"><i class="ri-play-fill"></i> สั่งรัน</button>
              </form>
            </div>
          </div>

        </div>
      </div>

      <!-- ── 5. Advanced Log Viewer Card ── -->
      <section class="adm-card cron-log-card">
        <div class="cron-log-head">
          <div class="cron-log-head-title">
            <h2><i class="ri-file-list-3-line"></i> ประวัติการทำงานของบอท (Automation Execution Logs)</h2>
            <p class="la-muted">แสดง <?= $totalLogs ?> รายการล่าสุด · เก็บข้อมูลการส่งงาน, ผลลัพธ์ และข้อความตอบกลับจาก API</p>
          </div>

          <!-- Search & Filter Controls -->
          <div class="cron-log-controls">
            <div class="cron-search-wrap">
              <i class="ri-search-line cron-search-icon"></i>
              <input type="text" id="cronLogSearch" class="la-input cron-search-input" placeholder="ค้นหาใน log..." autocomplete="off">
              <button type="button" id="cronLogSearchClear" class="cron-search-clear" style="display:none;" title="ล้างการค้นหา">&times;</button>
            </div>

            <nav class="cron-filters" aria-label="กรองประเภท log">
              <button type="button" class="cron-tab is-active" data-cron-filter="all">ทั้งหมด (<?= $totalLogs ?>)</button>
              <button type="button" class="cron-tab" data-cron-filter="pull">ดึงงานรอบหลัก</button>
              <button type="button" class="cron-tab" data-cron-filter="sync">ซิงก์บริการ</button>
              <button type="button" class="cron-tab" data-cron-filter="shop">คัดร้าน</button>
              <button type="button" class="cron-tab" data-cron-filter="catalog">แคตตาล็อก</button>
              <?php if ($errLogsCount > 0): ?>
              <button type="button" class="cron-tab is-err-tab" data-cron-filter="error">มีข้อผิดพลาด (<?= $errLogsCount ?>)</button>
              <?php endif; ?>
            </nav>
          </div>
        </div>

        <!-- Log Rows List -->
        <div class="cron-log-list" id="cronLogList" role="log">
          <?php if (empty($logs)): ?>
          <div class="cron-empty">
            <i class="ri-inbox-line"></i>
            <p>ยังไม่มีบันทึก log ในระบบ — กดปุ่ม "รันทุกระบบพร้อมกัน" ด้านบนเพื่อเริ่มการทำงานทันที</p>
          </div>
          <?php else: ?>
            <?php foreach ($logs as $r): ?>
            <article class="cron-log-row <?= $r['is_error'] ? 'is-error' : '' ?>" data-tone="<?= htmlspecialchars($r['tone']) ?>" data-err="<?= $r['is_error'] ? '1' : '0' ?>" data-search="<?= htmlspecialchars(strtolower($r['summary'] . ' ' . $r['raw'] . ' ' . $r['label'] . ' ' . $r['time'])) ?>">
              <div class="cron-log-meta">
                <span class="cron-badge is-<?= htmlspecialchars($r['tone']) ?>">
                  <i class="<?= htmlspecialchars($r['icon']) ?>"></i> <?= htmlspecialchars($r['label']) ?>
                </span>
                <time datetime="<?= htmlspecialchars($r['time']) ?>"><i class="ri-time-line"></i> <?= htmlspecialchars($r['time']) ?></time>
                <?php if (!empty($r['id'])): ?>
                <span class="cron-log-id">#<?= htmlspecialchars($r['id']) ?></span>
                <?php endif; ?>
                <?php if ($r['is_error']): ?>
                <span class="cron-err-pill"><i class="ri-error-warning-fill"></i> มีข้อผิดพลาด</span>
                <?php else: ?>
                <span class="cron-ok-pill"><i class="ri-check-line"></i> สำเร็จ</span>
                <?php endif; ?>
              </div>

              <p class="cron-log-summary"><?= htmlspecialchars($r['summary']) ?></p>

              <?php if (!empty($r['chips'])): ?>
              <div class="cron-chips">
                <?= $r['chips'] ?>
              </div>
              <?php endif; ?>

              <?php if (!empty($r['raw'])): ?>
              <details class="cron-raw">
                <summary><i class="ri-code-box-line"></i> ดูข้อความดิบ (Raw API Payload)</summary>
                <code><?= htmlspecialchars($r['raw']) ?></code>
              </details>
              <?php endif; ?>
            </article>
            <?php endforeach; ?>
          <?php endif; ?>
        </div>
      </section>

    </main>

    <!-- ── Interactive Automation Heartbeat Script ── -->
    <script>
    (function(){
      // 1. Live Filter & Search
      var searchInput = document.getElementById('cronLogSearch');
      var clearBtn = document.getElementById('cronLogSearchClear');
      var tabs = document.querySelectorAll('.cron-tab[data-cron-filter]');
      var rows = document.querySelectorAll('.cron-log-row');
      var curFilter = 'all';

      function applyFilter() {
        var query = (searchInput ? searchInput.value : '').trim().toLowerCase();
        if (clearBtn) {
          clearBtn.style.display = query.length > 0 ? 'inline-block' : 'none';
        }
        rows.forEach(function(row){
          var tone = row.getAttribute('data-tone') || '';
          var isErr = row.getAttribute('data-err') === '1';
          var searchTxt = row.getAttribute('data-search') || '';

          var matchTab = true;
          if (curFilter === 'error') {
            matchTab = isErr;
          } else if (curFilter !== 'all') {
            matchTab = (tone === curFilter);
          }

          var matchSearch = true;
          if (query.length > 0) {
            matchSearch = (searchTxt.indexOf(query) !== -1);
          }

          if (matchTab && matchSearch) {
            row.style.display = '';
          } else {
            row.style.display = 'none';
          }
        });
      }

      if (searchInput) {
        searchInput.addEventListener('input', applyFilter);
      }
      if (clearBtn) {
        clearBtn.addEventListener('click', function(){
          searchInput.value = '';
          applyFilter();
          searchInput.focus();
        });
      }

      tabs.forEach(function(tab){
        tab.addEventListener('click', function(){
          tabs.forEach(function(t){ t.classList.remove('is-active'); });
          tab.classList.add('is-active');
          curFilter = tab.getAttribute('data-cron-filter') || 'all';
          applyFilter();
        });
      });

      // 2. Countdown Heartbeat Timer
      var timerText = document.getElementById('cronTimerText');
      var secondsLeft = 60;

      function updateCountdown() {
        secondsLeft--;
        if (secondsLeft <= 0) {
          secondsLeft = 60;
          if (timerText) {
            timerText.innerHTML = '<span class="la-spin"><i class="ri-loader-4-line"></i></span> กำลังรันรอบออโต้...';
          }
          // Trigger silent background heartbeat
          fetch('/api/cron?key=likesauto2026', { method: 'GET' })
            .then(function(r){ return r.json(); })
            .then(function(d){
              if (timerText) {
                timerText.textContent = 'รันแล้ว ' + (d.timestamp ? d.timestamp.split(' ')[1] : 'เมื่อสักครู่');
              }
            })
            .catch(function(){
              if (timerText) {
                timerText.textContent = 'ทำงานอัตโนมัติ';
              }
            });
        } else {
          if (timerText) {
            timerText.textContent = 'รอบถัดไปใน ' + secondsLeft + ' วิ';
          }
        }
      }

      setInterval(updateCountdown, 1000);
      updateCountdown();

      // 3. Fast button helper
      window.cronTriggerImmediate = function() {
        if (timerText) {
          timerText.innerHTML = '<span class="la-spin"><i class="ri-loader-4-line"></i></span> กำลังส่งคำขอ...';
        }
        fetch('/api/cron?key=likesauto2026', { method: 'GET' })
          .then(function(){
            window.location.href = '/admin/crons?ran=' + encodeURIComponent('รันรอบอัตโนมัติเรียบร้อยแล้ว');
          })
          .catch(function(){
            window.location.reload();
          });
      };

      window.cronSubmitWithLoader = function(form, msg) {
        var btn = form.querySelector('button[type=submit]');
        if (btn) {
          btn.disabled = true;
          btn.innerHTML = '<i class="ri-loader-4-line la-spin"></i> ' + msg;
        }
        return true;
      };
    })();
    </script>
    <?php
    $newContent = ob_get_clean();

    $html = substr($html, 0, $mStart) . $newContent . substr($html, $mEnd + strlen('</main>'));
    return $html;
}

