<?php
declare(strict_types=1);

/**
 * Modern In-Flow Expandable Client Cards for Admin Clients.
 * Replaces legacy broken table with responsive KPI cards, instant search,
 * and ergonomic client management tools (Balance adjust, Status toggle, Password reset, API key).
 */
function la_patch_admin_clients(string $html): string {
    $tableWrapPos = strpos($html, '<div class="adm-table-wrap">');
    if ($tableWrapPos === false) {
        return $html;
    }

    $mainEnd = strpos($html, '</main>', $tableWrapPos);
    if ($mainEnd === false) {
        return $html;
    }

    $pagPos = strpos($html, '<nav class="la-pagination"', $tableWrapPos);
    $cutEnd = ($pagPos !== false) ? $pagPos : $mainEnd;

    $filterPos = strpos($html, '<form method="get" class="adm-filter">');
    $cutStart = ($filterPos !== false && $filterPos < $tableWrapPos) ? $filterPos : $tableWrapPos;

    $tableChunk = substr($html, $tableWrapPos, $cutEnd - $tableWrapPos);
    
    // Extract client rows
    $pattern = '~<tr>\s*<td>(\d+)</td>\s*<td>([^<]+)</td>\s*<td>([^<]+)</td>\s*<td>([^<]+)</td>\s*<td><span class="adm-badge\s+([^"]+)">([^<]+)</span></td>\s*<td>([^<]*)</td>\s*<td>(.*?)</td>\s*</tr>~s';
    if (!preg_match_all($pattern, $tableChunk, $matches, PREG_SET_ORDER)) {
        return $html;
    }

    $clients = [];
    $totalBal = 0.0;
    $activeCount = 0;
    $pausedCount = 0;
    $withBalCount = 0;

    foreach ($matches as $m) {
        $cid = (int)$m[1];
        $username = trim($m[2]);
        $email = trim($m[3]);
        $rawBal = (float)str_replace(',', '', trim($m[4]));
        $statusCls = trim($m[5]);
        $statusLbl = trim($m[6]);
        $refCode = trim($m[7]);
        $actionsHtml = trim($m[8]);

        $totalBal += $rawBal;
        if ($statusCls === 'active') {
            $activeCount++;
        } else {
            $pausedCount++;
        }
        if ($rawBal > 0) {
            $withBalCount++;
        }

        // Determine if Google user from email or pattern
        $isGoogle = (stripos($email, '@gmail.com') !== false);

        $clients[] = [
            'id' => $cid,
            'username' => $username,
            'email' => $email,
            'balance' => $rawBal,
            'bal_fmt' => number_format($rawBal, 2),
            'status_cls' => $statusCls,
            'status_lbl' => $statusLbl,
            'ref_code' => $refCode,
            'is_google' => $isGoogle,
            'actions_html' => $actionsHtml,
        ];
    }

    $totalClients = count($clients);

    ob_start();
    ?>
    <!-- ── Modern Admin Clients Component ── -->
    <div class="la-clients-container">
      
      <!-- Top KPI Summary Cards Grid -->
      <div class="client-kpi-grid">
        <div class="client-kpi-card is-primary">
          <div class="client-kpi-icon"><i class="ri-user-shared-line"></i></div>
          <div class="client-kpi-body">
            <span class="client-kpi-title">ลูกค้าทั้งหมด</span>
            <div class="client-kpi-num"><?= number_format($totalClients) ?> <span class="client-kpi-unit">คน</span></div>
          </div>
        </div>

        <div class="client-kpi-card is-success">
          <div class="client-kpi-icon"><i class="ri-checkbox-circle-line"></i></div>
          <div class="client-kpi-body">
            <span class="client-kpi-title">ใช้งานปกติ</span>
            <div class="client-kpi-num"><?= number_format($activeCount) ?> <span class="client-kpi-unit">คน</span></div>
          </div>
        </div>

        <div class="client-kpi-card is-warning">
          <div class="client-kpi-icon"><i class="ri-pause-circle-line"></i></div>
          <div class="client-kpi-body">
            <span class="client-kpi-title">พักการใช้งาน</span>
            <div class="client-kpi-num"><?= number_format($pausedCount) ?> <span class="client-kpi-unit">คน</span></div>
          </div>
        </div>

        <div class="client-kpi-card is-info">
          <div class="client-kpi-icon"><i class="ri-wallet-3-line"></i></div>
          <div class="client-kpi-body">
            <span class="client-kpi-title">ยอดเงินคงเหลือรวม</span>
            <div class="client-kpi-num">฿<?= number_format($totalBal, 2) ?></div>
          </div>
        </div>

        <div class="client-kpi-card is-purple">
          <div class="client-kpi-icon"><i class="ri-funds-line"></i></div>
          <div class="client-kpi-body">
            <span class="client-kpi-title">มียอดเงินพร้อมสั่ง</span>
            <div class="client-kpi-num"><?= number_format($withBalCount) ?> <span class="client-kpi-unit">คน</span></div>
          </div>
        </div>
      </div>

      <!-- Quick Filter Pills & Live Search -->
      <div class="client-toolbar">
        <div class="client-tabs">
          <button type="button" class="client-tab is-active" data-client-filter="all">
            ทั้งหมด <span class="client-tab-cnt"><?= $totalClients ?></span>
          </button>
          <button type="button" class="client-tab" data-client-filter="active">
            ใช้งาน <span class="client-tab-cnt"><?= $activeCount ?></span>
          </button>
          <?php if ($pausedCount > 0): ?>
          <button type="button" class="client-tab" data-client-filter="paused">
            พักใช้งาน <span class="client-tab-cnt"><?= $pausedCount ?></span>
          </button>
          <?php endif; ?>
          <button type="button" class="client-tab" data-client-filter="has-bal">
            มียอดเงิน <span class="client-tab-cnt"><?= $withBalCount ?></span>
          </button>
        </div>

        <div class="client-search-wrap">
          <i class="ri-search-line client-search-icon"></i>
          <?php $initialQ = htmlspecialchars($_GET['q'] ?? ''); ?>
          <input type="text" id="clientSearchInput" class="la-input client-search-input" value="<?= $initialQ ?>" placeholder="ค้นหาชื่อผู้ใช้, อีเมล หรือรหัส..." autocomplete="off">
          <button type="button" id="clientSearchClear" class="client-search-clear" style="<?= !empty($initialQ) ? 'display:inline-block;' : 'display:none;' ?>" title="ล้างการค้นหา">&times;</button>
        </div>
      </div>

      <!-- Expandable Client Cards List -->
      <div class="client-list" id="clientList">
        <?php foreach ($clients as $c): ?>
        <details class="client-card" id="client-<?= $c['id'] ?>" data-status="<?= $c['status_cls'] ?>" data-has-bal="<?= $c['balance'] > 0 ? '1' : '0' ?>" data-search="<?= htmlspecialchars(strtolower($c['username'] . ' ' . $c['email'] . ' ' . $c['id'] . ' ' . $c['ref_code'])) ?>">
          <summary class="client-head">
            <div class="client-head-main">
              <span class="client-id">#<?= $c['id'] ?></span>
              
              <div class="client-avatar" title="<?= htmlspecialchars($c['username']) ?>">
                <?= strtoupper(substr($c['username'], 0, 1)) ?>
              </div>

              <div class="client-title-group">
                <span class="client-uname">
                  <?= htmlspecialchars($c['username']) ?>
                  <?php if ($c['is_google']): ?>
                  <span class="client-google-badge" title="ผู้ใช้เข้าสู่ระบบด้วย Google"><i class="ri-google-fill"></i> Google</span>
                  <?php endif; ?>
                </span>
                <span class="client-email" title="<?= htmlspecialchars($c['email']) ?>">
                  <?= htmlspecialchars($c['email']) ?>
                </span>
              </div>
            </div>

            <div class="client-head-meta">
              <span class="client-bal-tag <?= $c['balance'] > 0 ? 'is-positive' : 'is-zero' ?>" title="ยอดเงินคงเหลือในกระเป๋า">
                <i class="ri-wallet-3-line"></i> ฿<?= $c['bal_fmt'] ?>
              </span>

              <span class="adm-badge <?= htmlspecialchars($c['status_cls']) ?>">
                <?php if ($c['status_cls'] === 'active'): ?>
                  <i class="ri-check-line"></i>
                <?php else: ?>
                  <i class="ri-pause-line"></i>
                <?php endif; ?>
                <?= htmlspecialchars($c['status_lbl']) ?>
              </span>

              <a class="client-orders-link" href="/admin/orders?q=<?= urlencode($c['username']) ?>" title="ดูคำสั่งซื้อทั้งหมดของลูกค้ารายนี้" onclick="event.stopPropagation()">
                <i class="ri-shopping-bag-3-line"></i> ออเดอร์
              </a>

              <span class="client-btn-manage">
                จัดการ <i class="ri-arrow-down-s-line"></i>
              </span>
            </div>
          </summary>

          <!-- Detail Drawer (3 Cards Grid) -->
          <div class="client-drawer">
            <div class="client-grid">
              
              <!-- 1. ข้อมูลลูกค้าและสถิติ -->
              <div class="client-box client-box-profile">
                <div class="client-box-header">
                  <i class="ri-user-3-line"></i> ข้อมูลลูกค้า
                </div>
                <div class="client-info-list">
                  <div class="client-info-row">
                    <span class="client-label">รหัสสมาชิก:</span>
                    <span class="client-val"><code>#<?= $c['id'] ?></code></span>
                  </div>
                  <div class="client-info-row">
                    <span class="client-label">ชื่อผู้ใช้:</span>
                    <span class="client-val"><strong><?= htmlspecialchars($c['username']) ?></strong></span>
                  </div>
                  <div class="client-info-row">
                    <span class="client-label">อีเมล:</span>
                    <div class="client-val client-val-copy">
                      <span><?= htmlspecialchars($c['email']) ?></span>
                      <button type="button" class="la-btn la-btn-mini la-btn-ghost client-copy-btn" onclick="navigator.clipboard.writeText('<?= htmlspecialchars($c['email']) ?>'); this.innerHTML='<i class=\'ri-check-line\'></i>'; var b=this; setTimeout(function(){ b.innerHTML='<i class=\'ri-file-copy-line\'></i>'; }, 1500);" title="คัดลอกอีเมล">
                        <i class="ri-file-copy-line"></i>
                      </button>
                    </div>
                  </div>
                  <div class="client-info-row">
                    <span class="client-label">โค้ดแนะนำ (Ref):</span>
                    <div class="client-val client-val-copy">
                      <code><?= htmlspecialchars($c['ref_code'] ?: '-') ?></code>
                      <?php if ($c['ref_code']): ?>
                      <button type="button" class="la-btn la-btn-mini la-btn-ghost client-copy-btn" onclick="navigator.clipboard.writeText('<?= htmlspecialchars($c['ref_code']) ?>'); this.innerHTML='<i class=\'ri-check-line\'></i>'; var b=this; setTimeout(function(){ b.innerHTML='<i class=\'ri-file-copy-line\'></i>'; }, 1500);" title="คัดลอกโค้ด">
                        <i class="ri-file-copy-line"></i>
                      </button>
                      <?php endif; ?>
                    </div>
                  </div>
                  <div class="client-info-row">
                    <span class="client-label">ยอดเงินในกระเป๋า:</span>
                    <span class="client-val client-val-bal">฿<?= $c['bal_fmt'] ?></span>
                  </div>
                  <div class="client-quick-nav">
                    <a href="/admin/orders?q=<?= urlencode($c['username']) ?>" class="la-btn la-btn-ghost la-btn-sm client-nav-btn">
                      <i class="ri-shopping-bag-3-line"></i> ดูประวัติคำสั่งซื้อ
                    </a>
                  </div>
                </div>
              </div>

              <!-- 2. ปรับยอดเงินในกระเป๋า -->
              <div class="client-box client-box-balance">
                <div class="client-box-header">
                  <i class="ri-wallet-3-line"></i> ปรับยอดเงินในกระเป๋า
                </div>
                <div class="client-box-body">
                  <div class="client-cur-bal">
                    <span class="client-cur-lbl">ยอดเงินปัจจุบัน:</span>
                    <span class="client-cur-amt">฿<?= $c['bal_fmt'] ?></span>
                  </div>

                  <!-- Quick Add Buttons -->
                  <div class="client-quick-chips">
                    <button type="button" class="client-chip" onclick="document.getElementById('bal_input_<?= $c['id'] ?>').value='50';">+฿50</button>
                    <button type="button" class="client-chip" onclick="document.getElementById('bal_input_<?= $c['id'] ?>').value='100';">+฿100</button>
                    <button type="button" class="client-chip" onclick="document.getElementById('bal_input_<?= $c['id'] ?>').value='500';">+฿500</button>
                    <button type="button" class="client-chip" onclick="document.getElementById('bal_input_<?= $c['id'] ?>').value='1000';">+฿1,000</button>
                    <button type="button" class="client-chip is-minus" onclick="document.getElementById('bal_input_<?= $c['id'] ?>').value='-50';">-฿50</button>
                  </div>

                  <form method="post" action="/admin/clients/<?= $c['id'] ?>/balance" class="client-bal-form" onsubmit="var b=this.querySelector('button[type=submit]'); if(b){ b.disabled=true; b.innerHTML='<i class=\'ri-loader-4-line la-spin\'></i> กำลังปรับยอด...'; }">
                    <div class="client-form-field">
                      <label class="client-field-label">จำนวนเงินที่ต้องการปรับ (+ หรือ -):</label>
                      <input id="bal_input_<?= $c['id'] ?>" class="la-input client-bal-input" type="number" step="0.01" name="amount" placeholder="+/- ตัวอย่าง: 100 หรือ -50" required>
                    </div>
                    <div class="client-form-field">
                      <label class="client-field-label">หมายเหตุ / เหตุผล:</label>
                      <input class="la-input" type="text" name="note" placeholder="เช่น เติมโบนัส, แก้ไขยอดโอน">
                    </div>
                    <button class="la-btn la-btn-primary client-btn-submit" type="submit">
                      <i class="ri-check-line"></i> บันทึกการปรับยอดเงิน
                    </button>
                  </form>
                </div>
              </div>

              <!-- 3. ความปลอดภัยและสิทธิ์ใช้งาน -->
              <div class="client-box client-box-security">
                <div class="client-box-header">
                  <i class="ri-shield-keyhole-line"></i> จัดการสิทธิ์ &amp; ความปลอดภัย
                </div>
                <div class="client-box-body">
                  
                  <!-- สลับสถานะบัญชี -->
                  <div class="client-sec-item">
                    <span class="client-sec-lbl">สถานะการเข้าใช้งาน:</span>
                    <form method="post" action="/admin/clients/<?= $c['id'] ?>/status" onsubmit="return confirm('ยืนยัน<?= $c['status_cls'] === 'active' ? 'พักการใช้งาน' : 'เปิดใช้งาน' ?> บัญชี <?= htmlspecialchars($c['username']) ?>?')">
                      <input type="hidden" name="status" value="<?= $c['status_cls'] === 'active' ? 'paused' : 'active' ?>">
                      <?php if ($c['status_cls'] === 'active'): ?>
                      <button class="la-btn la-btn-warning la-btn-sm client-btn-full" type="submit">
                        <i class="ri-pause-circle-line"></i> พักการใช้งานบัญชีนี้
                      </button>
                      <?php else: ?>
                      <button class="la-btn la-btn-success la-btn-sm client-btn-full" type="submit">
                        <i class="ri-play-circle-line"></i> ปลดล็อกเปิดใช้งานบัญชี
                      </button>
                      <?php endif; ?>
                    </form>
                  </div>

                  <!-- รีเซ็ตรหัสผ่าน -->
                  <div class="client-sec-item">
                    <span class="client-sec-lbl">ตั้งรหัสผ่านใหม่:</span>
                    <form method="post" action="/admin/clients/<?= $c['id'] ?>/password" class="client-pwd-form" onsubmit="var b=this.querySelector('button[type=submit]'); if(b){ b.disabled=true; b.innerHTML='<i class=\'ri-loader-4-line la-spin\'></i> กำลังตั้งรหัส...'; }">
                      <div class="client-field-row">
                        <input class="la-input" type="text" name="password" placeholder="รหัสผ่านใหม่อย่างน้อย 6 ตัว" required minlength="6">
                        <button class="la-btn la-btn-outline la-btn-sm" type="submit">
                          <i class="ri-key-2-line"></i> ตั้งรหัส
                        </button>
                      </div>
                    </form>
                  </div>

                  <!-- สร้าง API Key ใหม่ -->
                  <div class="client-sec-item">
                    <span class="client-sec-lbl">การเข้าถึงผ่าน API:</span>
                    <form method="post" action="/admin/clients/<?= $c['id'] ?>/apikey" onsubmit="return confirm('ยืนยันออก API Key ใหม่ให้ลูกค้า <?= htmlspecialchars($c['username']) ?>? (คีย์เดิมจะถูกยกเลิกทันที)')">
                      <button class="la-btn la-btn-ghost la-btn-sm client-btn-full" type="submit">
                        <i class="ri-key-fill"></i> ออก API Key ใหม่
                      </button>
                    </form>
                  </div>

                </div>
              </div>

            </div>
          </div>
        </details>
        <?php endforeach; ?>
      </div>

    </div>

    <!-- Live Client Filter & Search Script -->
    <script>
    (function(){
      var input = document.getElementById('clientSearchInput');
      var clearBtn = document.getElementById('clientSearchClear');
      var tabs = document.querySelectorAll('[data-client-filter]');
      var cards = document.querySelectorAll('.client-card');

      var currentFilter = 'all';

      function applyFilter() {
        var query = (input ? input.value : '').trim().toLowerCase();
        if (clearBtn) {
          clearBtn.style.display = query.length > 0 ? 'inline-block' : 'none';
        }

        cards.forEach(function(card){
          var st = card.getAttribute('data-status') || '';
          var hasBal = card.getAttribute('data-has-bal') === '1';
          var searchTxt = card.getAttribute('data-search') || '';

          var matchTab = true;
          if (currentFilter === 'active') {
            matchTab = (st === 'active');
          } else if (currentFilter === 'paused') {
            matchTab = (st === 'paused');
          } else if (currentFilter === 'has-bal') {
            matchTab = hasBal;
          }

          var matchSearch = true;
          if (query.length > 0) {
            matchSearch = (searchTxt.indexOf(query) !== -1);
          }

          if (matchTab && matchSearch) {
            card.style.display = '';
          } else {
            card.style.display = 'none';
          }
        });
      }

      if (input) {
        input.addEventListener('input', applyFilter);
      }
      if (clearBtn) {
        clearBtn.addEventListener('click', function(){
          input.value = '';
          applyFilter();
          input.focus();
        });
      }

      tabs.forEach(function(tab){
        tab.addEventListener('click', function(){
          tabs.forEach(function(t){ t.classList.remove('is-active'); });
          tab.classList.add('is-active');
          currentFilter = tab.getAttribute('data-client-filter') || 'all';
          applyFilter();
        });
      });

      if (input && input.value.trim().length > 0) {
        applyFilter();
      }
    })();
    </script>
    <?php
    $newList = ob_get_clean();

    $html = substr($html, 0, $cutStart) . $newList . "\n" . substr($html, $cutEnd);
    return $html;
}
