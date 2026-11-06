<?php
declare(strict_types=1);

/**
 * Modern In-Flow Expandable Accordion Order Cards for Admin Orders.
 * Eliminates popup clipping at container borders and multiple popup overlap.
 * Provides a compact collapsed overview and convenient 3-box detail drawer.
 */
function la_patch_admin_orders(string $html): string {
    $wrapStart = strpos($html, '<div class="ord-wrap">');
    if ($wrapStart === false) {
        return $html;
    }

    $mainEnd = strpos($html, '</main>', $wrapStart);
    if ($mainEnd === false) {
        return $html;
    }

    $pagPos = strpos($html, '<nav class="la-pagination"', $wrapStart);
    $cutEnd = ($pagPos !== false) ? $pagPos : $mainEnd;

    $wrapChunk = substr($html, $wrapStart, $cutEnd - $wrapStart);
    $parts = explode('<div class="ord-row ', $wrapChunk);
    if (count($parts) <= 1) {
        return $html;
    }

    $orders = [];
    for ($i = 1; $i < count($parts); $i++) {
        $raw = '<div class="ord-row ' . $parts[$i];

        $oid = '';
        if (preg_match('~class="ord-id">#?(\d+)<~', $raw, $m)) {
            $oid = $m[1];
        }

        $statusCls = 'pending';
        $statusLbl = 'รอส่ง';
        if (preg_match('~class="adm-badge\s+([^"]+)">([^<]+)<~', $raw, $m)) {
            $statusCls = trim($m[1]);
            $statusLbl = trim($m[2]);
        }

        $amt = '0.00';
        if (preg_match('~class="ord-amt">([^<]+)<~', $raw, $m)) {
            $amt = trim($m[1]);
        }

        $user = '';
        if (preg_match('~class="ord-user"[^>]*>([^<]+)<~', $raw, $m)) {
            $user = trim($m[1]);
        }

        $svc = '';
        if (preg_match('~class="ord-svc"[^>]*title="([^"]+)"~', $raw, $m)) {
            $svc = trim($m[1]);
        } elseif (preg_match('~class="ord-svc"[^>]*>([^<]+)<~', $raw, $m)) {
            $svc = trim($m[1]);
        }

        $qty = '0';
        if (preg_match('~class="ord-qty">([^<]+)<~', $raw, $m)) {
            $qty = trim($m[1]);
        }

        $link = '';
        if (preg_match('~class="ord-link"\s+href="([^"]+)"~', $raw, $m)) {
            $link = trim($m[1]);
        }

        $dateStr = '';
        if (preg_match('~<p>(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2})\s*·\s*([^<]+)</p>~', $raw, $m)) {
            $dateStr = $m[1];
        }

        $startVal = '-';
        $remainsVal = '-';
        $doneVal = '-';
        if (preg_match('~<p>เริ่ม\s*([^\s·<]+)\s*·\s*คง\s*([^\s·<]+)\s*·\s*ทำ\s*([^<]+)</p>~', $raw, $m)) {
            $startVal = trim($m[1]);
            $remainsVal = trim($m[2]);
            $doneVal = trim($m[3]);
        }

        $apiId = '-';
        $provHost = 'justanotherpanel.com';
        $provSvcId = '-';
        if (preg_match('~<p>API\s*([^\s·<]+)\s*·\s*([^·<]+)\s*·\s*บริการ\s*#?([^<]+)</p>~', $raw, $m)) {
            $apiId = trim($m[1]);
            $provHost = trim($m[2]);
            $provSvcId = trim($m[3]);
        }

        $err = '';
        if (preg_match('~class="ord-err">([^<]+)<~', $raw, $m)) {
            $err = trim($m[1]);
        }
        $hasErr = ($err !== '') || (strpos(substr($raw, 0, 50), 'is-err') !== false);

        $toolsHtml = '';
        if (preg_match('~<div class="ord-tools">(.*?)</div>\s*</div>\s*</details>~s', $raw, $m)) {
            $toolsHtml = trim($m[1]);
        }

        $progPct = null;
        if (strpos($doneVal, '%') !== false && preg_match('~(\d+)%~', $doneVal, $mPct)) {
            $progPct = (int)$mPct[1];
        } elseif ($statusCls === 'completed') {
            $progPct = 100;
        } elseif ($statusCls === 'processing' && $remainsVal !== '-' && $qty !== '0') {
            $rem = (float)str_replace(',', '', $remainsVal);
            $q = (float)str_replace(',', '', $qty);
            if ($q > 0 && $rem >= 0 && $rem <= $q) {
                $progPct = (int)round((($q - $rem) / $q) * 100);
            }
        }

        $orders[] = [
            'id' => $oid,
            'status_cls' => $statusCls,
            'status_lbl' => $statusLbl,
            'amt' => $amt,
            'user' => $user,
            'svc' => $svc,
            'qty' => $qty,
            'link' => $link,
            'date' => $dateStr,
            'start' => $startVal,
            'remains' => $remainsVal,
            'done' => $doneVal,
            'prog_pct' => $progPct,
            'api_id' => $apiId,
            'provider' => $provHost,
            'provider_svc' => $provSvcId,
            'err' => $err,
            'has_err' => $hasErr,
            'tools_html' => $toolsHtml,
        ];
    }

    ob_start();
    ?>
    <div class="ord-list">
      <?php foreach ($orders as $o): ?>
      <details class="ord-card is-<?= htmlspecialchars($o['status_cls']) ?><?php if ($o['has_err']): ?> is-err<?php endif; ?>" id="order-<?= htmlspecialchars($o['id']) ?>">
        <summary class="ord-head">
          <div class="ord-head-main">
            <span class="ord-id">#<?= htmlspecialchars($o['id']) ?></span>

            <span class="adm-badge <?= htmlspecialchars($o['status_cls']) ?>">
              <?php if ($o['status_cls'] === 'completed'): ?>
                <i class="ri-check-line"></i>
              <?php elseif ($o['status_cls'] === 'processing'): ?>
                <i class="ri-loader-4-line"></i>
              <?php elseif ($o['status_cls'] === 'pending'): ?>
                <i class="ri-time-line"></i>
              <?php elseif ($o['status_cls'] === 'partial'): ?>
                <i class="ri-pie-chart-line"></i>
              <?php else: ?>
                <i class="ri-close-circle-line"></i>
              <?php endif; ?>
              <?= htmlspecialchars($o['status_lbl']) ?>
            </span>

            <span class="ord-amt">฿<?= htmlspecialchars($o['amt']) ?></span>

            <span class="ord-user" title="ผู้สั่งซื้อ: <?= htmlspecialchars($o['user']) ?>">
              <i class="ri-user-3-line"></i> <?= htmlspecialchars($o['user']) ?>
            </span>

            <span class="ord-svc" title="<?= htmlspecialchars($o['svc']) ?>">
              <?= htmlspecialchars($o['svc']) ?>
            </span>
          </div>

          <div class="ord-head-meta">
            <span class="ord-qty" title="จำนวน">
              <i class="ri-stack-line"></i> <?= htmlspecialchars($o['qty']) ?>
            </span>

            <?php if (!empty($o['link'])): ?>
            <a class="ord-quick-link" href="<?= htmlspecialchars($o['link']) ?>" target="_blank" rel="noopener" title="เปิดลิงก์ปลายทางในแท็บใหม่" onclick="event.stopPropagation()">
              <i class="ri-external-link-line"></i> ลิงก์
            </a>
            <?php else: ?>
            <span class="ord-quick-link is-empty">-</span>
            <?php endif; ?>

            <?php if ($o['prog_pct'] !== null && $o['prog_pct'] > 0): ?>
            <span class="ord-kpi-pill kpi-prog" title="ความคืบหน้า <?= $o['prog_pct'] ?>%">
              <?= $o['prog_pct'] ?>%
            </span>
            <?php elseif (!empty($o['api_id']) && $o['api_id'] !== '-'): ?>
            <span class="ord-kpi-pill kpi-api" title="ส่ง API แล้ว (รหัส #<?= htmlspecialchars($o['api_id']) ?>)">
              API #<?= htmlspecialchars($o['api_id']) ?>
            </span>
            <?php endif; ?>

            <?php if ($o['has_err']): ?>
            <span class="ord-kpi-pill kpi-err" title="<?= htmlspecialchars($o['err'] ?: 'มีข้อผิดพลาด') ?>">
              <i class="ri-error-warning-fill"></i> มีข้อผิดพลาด
            </span>
            <?php endif; ?>

            <span class="ord-btn-manage">
              จัดการ <i class="ri-arrow-down-s-line ord-chevron"></i>
            </span>
          </div>
        </summary>

        <div class="ord-body">
          <div class="ord-grid">
            <!-- 1. ข้อมูลคำสั่งซื้อ -->
            <div class="ord-box ord-box-info">
              <div class="ord-box-header">
                <i class="ri-shopping-cart-2-line"></i> ข้อมูลคำสั่งซื้อ
              </div>
              <div class="ord-info-list">
                <div class="ord-info-row">
                  <span class="ord-label">วันที่/เวลาสั่ง:</span>
                  <span class="ord-val"><?= htmlspecialchars($o['date'] ?: '-') ?></span>
                </div>
                <div class="ord-info-row">
                  <span class="ord-label">ผู้สั่งซื้อ:</span>
                  <span class="ord-val ord-val-user">
                    <i class="ri-user-line"></i> <strong><?= htmlspecialchars($o['user']) ?></strong>
                  </span>
                </div>
                <div class="ord-info-row ord-info-stacked">
                  <span class="ord-label">บริการ:</span>
                  <div class="ord-val-svc"><?= htmlspecialchars($o['svc']) ?></div>
                </div>
                <div class="ord-info-row">
                  <span class="ord-label">จำนวน:</span>
                  <span class="ord-val ord-val-qty"><strong><?= htmlspecialchars($o['qty']) ?></strong> ชิ้น</span>
                </div>
                <div class="ord-info-row">
                  <span class="ord-label">ยอดเงินตัดชำระ:</span>
                  <span class="ord-val ord-val-charge">฿<?= htmlspecialchars($o['amt']) ?></span>
                </div>
                <div class="ord-info-row ord-info-stacked">
                  <span class="ord-label">ลิงก์ปลายทาง:</span>
                  <div class="ord-link-action">
                    <input class="la-input ord-link-input" type="text" value="<?= htmlspecialchars($o['link']) ?>" readonly id="link-field-<?= htmlspecialchars($o['id']) ?>">
                    <?php if (!empty($o['link'])): ?>
                    <button type="button" class="la-btn la-btn-mini la-btn-ghost" style="white-space:nowrap;flex-shrink:0;" onclick="navigator.clipboard.writeText('<?= addslashes($o['link']) ?>'); this.innerHTML='<i class=\'ri-check-line\'></i> คัดลอกแล้ว'; var b=this; setTimeout(function(){ b.innerHTML='<i class=\'ri-file-copy-line\'></i> คัดลอก'; }, 1500);" title="คัดลอกลิงก์">
                      <i class="ri-file-copy-line"></i> คัดลอก
                    </button>
                    <a href="<?= htmlspecialchars($o['link']) ?>" target="_blank" rel="noopener" class="la-btn la-btn-mini la-btn-ghost" style="white-space:nowrap;flex-shrink:0;" title="เปิดในแท็บใหม่">
                      <i class="ri-external-link-line"></i> เปิด
                    </a>
                    <?php endif; ?>
                  </div>
                </div>
              </div>
            </div>

            <!-- 2. การเชื่อมต่อ API & ความคืบหน้า -->
            <div class="ord-box ord-box-api">
              <div class="ord-box-header">
                <i class="ri-router-line"></i> การเชื่อมต่อ API &amp; ความคืบหน้า
              </div>
              <div class="ord-info-list">
                <div class="ord-info-row">
                  <span class="ord-label">ผู้ให้บริการ:</span>
                  <span class="ord-val ord-val-prov">
                    <i class="ri-server-line"></i> <?= htmlspecialchars($o['provider'] ?: 'รอส่ง API') ?>
                  </span>
                </div>
                <div class="ord-info-row">
                  <span class="ord-label">รหัสออเดอร์ API:</span>
                  <span class="ord-val">
                    <?php if (!empty($o['api_id']) && $o['api_id'] !== '-'): ?>
                    <code class="ord-code">#<?= htmlspecialchars($o['api_id']) ?></code>
                    <button type="button" class="la-btn la-btn-mini la-btn-ghost ord-copy-btn" onclick="navigator.clipboard.writeText('<?= htmlspecialchars($o['api_id']) ?>'); this.innerHTML='<i class=\'ri-check-line\'></i>'; var b=this; setTimeout(function(){ b.innerHTML='<i class=\'ri-file-copy-line\'></i>'; }, 1500);" title="คัดลอกรหัสออเดอร์ API">
                      <i class="ri-file-copy-line"></i>
                    </button>
                    <?php else: ?>
                    <span class="la-muted">- ยังไม่ได้ส่ง API -</span>
                    <?php endif; ?>
                  </span>
                </div>
                <div class="ord-info-row">
                  <span class="ord-label">สถานะจาก Provider:</span>
                  <span class="ord-val">
                    <span class="adm-badge <?= htmlspecialchars($o['status_cls']) ?>">
                      <?= htmlspecialchars($o['status_lbl']) ?>
                    </span>
                  </span>
                </div>

                <div class="ord-kpi-row">
                  <div class="ord-kpi-box">
                    <span class="kpi-tag">เริ่มนับ (Start)</span>
                    <span class="kpi-val"><?= htmlspecialchars($o['start']) ?></span>
                  </div>
                  <div class="ord-kpi-box">
                    <span class="kpi-tag">คงเหลือ (Remains)</span>
                    <span class="kpi-val"><?= htmlspecialchars($o['remains']) ?></span>
                  </div>
                  <div class="ord-kpi-box">
                    <span class="kpi-tag">ทำแล้ว (Done)</span>
                    <span class="kpi-val"><?= htmlspecialchars($o['done']) ?></span>
                  </div>
                  <div class="ord-kpi-box">
                    <span class="kpi-tag">คืบหน้า</span>
                    <span class="kpi-val"><?= $o['prog_pct'] !== null ? $o['prog_pct'] . '%' : '-' ?></span>
                  </div>
                </div>

                <?php if ($o['prog_pct'] !== null): ?>
                <div class="ord-meter" title="ความคืบหน้า <?= $o['prog_pct'] ?>%">
                  <div class="ord-meter-fill is-<?= htmlspecialchars($o['status_cls']) ?>" style="width: <?= min(100, max(0, $o['prog_pct'])) ?>%;"></div>
                </div>
                <?php endif; ?>

                <?php if (!empty($o['err'])): ?>
                <div class="ord-alert-box ord-err-box">
                  <i class="ri-error-warning-fill"></i>
                  <div>
                    <strong>ข้อผิดพลาดจาก API:</strong>
                    <div><?= htmlspecialchars(htmlspecialchars_decode((string)$o['err'], ENT_QUOTES)) ?></div>
                  </div>
                </div>
                <?php endif; ?>
              </div>
            </div>

            <!-- 3. เครื่องมือจัดการคำสั่งซื้อ -->
            <div class="ord-box ord-box-act">
              <div class="ord-box-header">
                <i class="ri-tools-line"></i> เครื่องมือจัดการคำสั่งซื้อ
              </div>
              <div class="ord-actions-wrap">
                <?= $o['tools_html'] ?>
              </div>
            </div>
          </div>
        </div>
      </details>
      <?php endforeach; ?>
    </div>
    <?php
    $newList = ob_get_clean();

    $html = substr($html, 0, $wrapStart) . $newList . "\n" . substr($html, $cutEnd);
    return $html;
}
