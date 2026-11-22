<?php
declare(strict_types=1);

/**
 * Modern Admin Orders Master Desk for LIKES-AUTO.
 * Continuous Real-Time Provider Status Synchronization, 
 * Responsive Two-Tier Order Cards, Live Progress Tracking,
 * and 1-Click Fast Controls (Sync All, Resend, Refund, Status).
 */
function la_patch_admin_orders(string $html): string {
    $mStart = strpos($html, '<main class="dash-content">');
    if ($mStart === false) {
        return $html;
    }
    $mEnd = strpos($html, '</main>', $mStart);
    if ($mEnd === false) {
        return $html;
    }

    // Extract any existing alert from URL
    $okMsg = '';
    $errMsg = '';
    if (isset($_GET['ok']) && $_GET['ok'] !== '') {
        $okMsg = htmlspecialchars(urldecode((string)$_GET['ok']));
    }
    if (isset($_GET['err']) && $_GET['err'] !== '') {
        $errMsg = htmlspecialchars(urldecode((string)$_GET['err']));
    }

    // Active filters
    $statusFilter = isset($_GET['status']) ? trim((string)$_GET['status']) : '';
    $searchQuery = isset($_GET['q']) ? trim((string)$_GET['q']) : '';
    $page = isset($_GET['page']) ? max(1, (int)$_GET['page']) : 1;
    $perPage = 30;

    // Database lookup
    $possibleDbPaths = [
        __DIR__ . '/.la-db-restore-latest.db',
        __DIR__ . '/.la-db-restore-d1qyg5az73cs4unx8jl9trbw.db',
        __DIR__ . '/../.la-db-restore-latest.db',
    ];
    $activeDb = null;
    $db = null;
    foreach ($possibleDbPaths as $p) {
        if (file_exists($p) && class_exists('SQLite3')) {
            try {
                $db = new SQLite3($p, SQLITE3_OPEN_READWRITE);
                $db->busyTimeout(5000);
                $activeDb = $p;
                break;
            } catch (\Throwable $e) {}
        }
    }

    // If SQLite is not open, return original HTML
    if (!$db) {
        return $html;
    }

    // Real-time automatic background status sync if active orders exist
    if (function_exists('la_auto_sync_active_orders')) {
        @la_auto_sync_active_orders(false);
    }

    // Unsent count
    $unsentRes = $db->query("SELECT COUNT(*) as c FROM orders WHERE (api_orderid IS NULL OR api_orderid = '' OR api_orderid = '-') AND status NOT IN ('completed', 'canceled')");
    $unsentCount = $unsentRes ? (int)($unsentRes->fetchArray(SQLITE3_ASSOC)['c'] ?? 0) : 0;

    // 1. Calculate KPI Statistics
    $kpiCounts = [
        'all' => 0,
        'pending' => 0,
        'processing' => 0,
        'completed' => 0,
        'partial' => 0,
        'canceled' => 0,
    ];
    $kpiRes = $db->query("SELECT status, COUNT(*) as c FROM orders GROUP BY status");
    if ($kpiRes) {
        while ($kr = $kpiRes->fetchArray(SQLITE3_ASSOC)) {
            $st = strtolower(trim((string)$kr['status']));
            $cnt = (int)$kr['c'];
            $kpiCounts['all'] += $cnt;
            if ($st === 'inprogress') $st = 'processing';
            if (isset($kpiCounts[$st])) {
                $kpiCounts[$st] += $cnt;
            }
        }
    }

    // 2. Build Where Clause
    $whereParts = [];
    $binds = [];
    if ($statusFilter !== '') {
        if ($statusFilter === 'processing') {
            $whereParts[] = "o.status IN ('processing', 'inprogress')";
        } else {
            $whereParts[] = "o.status = :filter_status";
            $binds[':filter_status'] = $statusFilter;
        }
    }
    if ($searchQuery !== '') {
        $whereParts[] = "(o.id = :qid OR o.client LIKE :qlike OR o.service LIKE :qlike OR o.link LIKE :qlike OR o.api_orderid LIKE :qlike)";
        $binds[':qid'] = is_numeric($searchQuery) ? (int)$searchQuery : 0;
        $binds[':qlike'] = '%' . $searchQuery . '%';
    }
    $whereSql = !empty($whereParts) ? ('WHERE ' . implode(' AND ', $whereParts)) : '';

    // Total Count
    $cntStmt = $db->prepare("SELECT COUNT(*) as c FROM orders o {$whereSql}");
    foreach ($binds as $param => $val) {
        $cntStmt->bindValue($param, $val, is_int($val) ? SQLITE3_INTEGER : SQLITE3_TEXT);
    }
    $cntRes = $cntStmt->execute();
    $totalOrders = $cntRes ? (int)($cntRes->fetchArray(SQLITE3_ASSOC)['c'] ?? 0) : 0;
    $totalPages = max(1, (int)ceil($totalOrders / $perPage));
    if ($page > $totalPages) $page = $totalPages;
    $offset = ($page - 1) * $perPage;

    // 3. Fetch Order Items
    $orderSql = "
        SELECT o.*, 
               s.name as svc_name, s.platform as svc_platform, s.category as svc_cat, s.api_service,
               p.name as provider_name, p.api_url
        FROM orders o
        LEFT JOIN services s ON o.service_id = s.id
        LEFT JOIN providers p ON p.id = COALESCE(s.provider_id, o.provider_id, 1)
        {$whereSql}
        ORDER BY CASE o.status
            WHEN 'pending' THEN 0
            WHEN 'processing' THEN 1
            WHEN 'inprogress' THEN 1
            WHEN 'partial' THEN 2
            ELSE 3 END, o.id DESC
        LIMIT :limit OFFSET :offset
    ";
    $stmt = $db->prepare($orderSql);
    foreach ($binds as $param => $val) {
        $stmt->bindValue($param, $val, is_int($val) ? SQLITE3_INTEGER : SQLITE3_TEXT);
    }
    $stmt->bindValue(':limit', $perPage, SQLITE3_INTEGER);
    $stmt->bindValue(':offset', $offset, SQLITE3_INTEGER);
    $res = $stmt->execute();

    $orders = [];
    if ($res) {
        while ($row = $res->fetchArray(SQLITE3_ASSOC)) {
            $orders[] = $row;
        }
    }
    $db->close();

    // 4. Render Orders Master HTML
    ob_start();
    ?>
    <main class="dash-content">
      <div class="om-desk-wrap">
        
        <!-- Flash Alerts -->
        <?php if (!empty($okMsg)): ?>
          <div class="om-alert om-alert-ok">
            <i class="ri-checkbox-circle-fill"></i>
            <span><?= $okMsg ?></span>
          </div>
        <?php endif; ?>
        <?php if (!empty($errMsg)): ?>
          <div class="om-alert om-alert-err">
            <i class="ri-error-warning-fill"></i>
            <span><?= $errMsg ?></span>
          </div>
        <?php endif; ?>

        <!-- ── 1. Top KPI Summary Grid ── -->
        <div class="om-kpi-grid">
          <a href="/admin/orders" class="om-kpi-card <?= $statusFilter === '' ? 'is-active' : '' ?>">
            <div class="om-kpi-info">
              <span class="om-kpi-lbl">ออเดอร์ทั้งหมด</span>
              <span class="om-kpi-val"><?= number_format($kpiCounts['all']) ?></span>
              <span class="om-kpi-sub">รายการในระบบ</span>
            </div>
            <div class="om-kpi-icon om-ico-all"><i class="ri-shopping-bag-3-fill"></i></div>
          </a>

          <a href="/admin/orders?status=pending" class="om-kpi-card <?= $statusFilter === 'pending' ? 'is-active' : '' ?>">
            <div class="om-kpi-info">
              <span class="om-kpi-lbl">ในคิวระบบ (API)</span>
              <span class="om-kpi-val text-warn"><?= number_format($kpiCounts['pending']) ?></span>
              <span class="om-kpi-sub"><?= $unsentCount > 0 ? ('รอส่ง ' . $unsentCount . ' รายการ') : 'รอเริ่มงานบน API' ?></span>
            </div>
            <div class="om-kpi-icon om-ico-pending"><i class="ri-time-fill"></i></div>
          </a>

          <a href="/admin/orders?status=processing" class="om-kpi-card <?= $statusFilter === 'processing' ? 'is-active' : '' ?>">
            <div class="om-kpi-info">
              <span class="om-kpi-lbl">กำลังดำเนินการ</span>
              <span class="om-kpi-val text-blue"><?= number_format($kpiCounts['processing']) ?></span>
              <span class="om-kpi-sub">ส่ง API แล้ว (รันงาน)</span>
            </div>
            <div class="om-kpi-icon om-ico-processing"><i class="ri-loader-4-fill om-spin"></i></div>
          </a>

          <a href="/admin/orders?status=completed" class="om-kpi-card <?= $statusFilter === 'completed' ? 'is-active' : '' ?>">
            <div class="om-kpi-info">
              <span class="om-kpi-lbl">สำเร็จแล้ว</span>
              <span class="om-kpi-val text-ok"><?= number_format($kpiCounts['completed']) ?></span>
              <span class="om-kpi-sub">เสร็จสมบูรณ์</span>
            </div>
            <div class="om-kpi-icon om-ico-completed"><i class="ri-checkbox-circle-fill"></i></div>
          </a>

          <a href="/admin/orders?status=partial" class="om-kpi-card <?= $statusFilter === 'partial' ? 'is-active' : '' ?>">
            <div class="om-kpi-info">
              <span class="om-kpi-lbl">สำเร็จบางส่วน</span>
              <span class="om-kpi-val text-purple"><?= number_format($kpiCounts['partial']) ?></span>
              <span class="om-kpi-sub">คืนเงินส่วนที่เหลือ</span>
            </div>
            <div class="om-kpi-icon om-ico-partial"><i class="ri-pie-chart-2-fill"></i></div>
          </a>

          <a href="/admin/orders?status=canceled" class="om-kpi-card <?= $statusFilter === 'canceled' ? 'is-active' : '' ?>">
            <div class="om-kpi-info">
              <span class="om-kpi-lbl">ยกเลิก / คืนเงิน</span>
              <span class="om-kpi-val text-red"><?= number_format($kpiCounts['canceled']) ?></span>
              <span class="om-kpi-sub">คืนเงินลูกค้าแล้ว</span>
            </div>
            <div class="om-kpi-icon om-ico-canceled"><i class="ri-close-circle-fill"></i></div>
          </a>
        </div>

        <!-- ── 2. Command Toolbar (Filter Tabs + Search + Sync All) ── -->
        <div class="om-toolbar">
          <div class="om-filter-tabs">
            <a href="/admin/orders<?= !empty($searchQuery) ? ('?q=' . urlencode($searchQuery)) : '' ?>" class="om-tab <?= $statusFilter === '' ? 'is-active' : '' ?>">
              ทั้งหมด <span class="om-tab-badge"><?= $kpiCounts['all'] ?></span>
            </a>
            <a href="/admin/orders?status=pending<?= !empty($searchQuery) ? ('&q=' . urlencode($searchQuery)) : '' ?>" class="om-tab <?= $statusFilter === 'pending' ? 'is-active' : '' ?>">
              <i class="ri-time-line"></i> ในคิวระบบ <span class="om-tab-badge"><?= $kpiCounts['pending'] ?></span>
            </a>
            <a href="/admin/orders?status=processing<?= !empty($searchQuery) ? ('&q=' . urlencode($searchQuery)) : '' ?>" class="om-tab <?= $statusFilter === 'processing' ? 'is-active' : '' ?>">
              <i class="ri-loader-4-line"></i> กำลังทำ <span class="om-tab-badge"><?= $kpiCounts['processing'] ?></span>
            </a>
            <a href="/admin/orders?status=completed<?= !empty($searchQuery) ? ('&q=' . urlencode($searchQuery)) : '' ?>" class="om-tab <?= $statusFilter === 'completed' ? 'is-active' : '' ?>">
              <i class="ri-checkbox-circle-line"></i> สำเร็จ <span class="om-tab-badge"><?= $kpiCounts['completed'] ?></span>
            </a>
            <a href="/admin/orders?status=partial<?= !empty($searchQuery) ? ('&q=' . urlencode($searchQuery)) : '' ?>" class="om-tab <?= $statusFilter === 'partial' ? 'is-active' : '' ?>">
              <i class="ri-pie-chart-line"></i> บางส่วน <span class="om-tab-badge"><?= $kpiCounts['partial'] ?></span>
            </a>
            <a href="/admin/orders?status=canceled<?= !empty($searchQuery) ? ('&q=' . urlencode($searchQuery)) : '' ?>" class="om-tab <?= $statusFilter === 'canceled' ? 'is-active' : '' ?>">
              <i class="ri-close-circle-line"></i> ยกเลิก <span class="om-tab-badge"><?= $kpiCounts['canceled'] ?></span>
            </a>
          </div>

          <div class="om-search-bar">
            <form method="get" action="/admin/orders" class="om-search-form">
              <?php if (!empty($statusFilter)): ?>
                <input type="hidden" name="status" value="<?= htmlspecialchars($statusFilter) ?>">
              <?php endif; ?>
              <div class="om-search-input-wrap">
                <i class="ri-search-line om-search-icon"></i>
                <input type="text" name="q" value="<?= htmlspecialchars($searchQuery) ?>" placeholder="ค้นหาด้วย #ID, ชื่อลูกค้า, ลิงก์, ชื่อบริการ หรือรหัส API..." class="om-search-input">
                <?php if (!empty($searchQuery)): ?>
                  <a href="/admin/orders<?= !empty($statusFilter) ? ('?status=' . urlencode($statusFilter)) : '' ?>" class="om-search-clear" title="ล้างการค้นหา"><i class="ri-close-line"></i></a>
                <?php endif; ?>
              </div>
              <button type="submit" class="om-btn om-btn-search"><i class="ri-search-2-line"></i> ค้นหา</button>
            </form>

            <div class="om-actions-right">
              <!-- Sync All Button -->
              <form method="post" action="/admin/orders/sync-all" class="om-inline-form" onsubmit="var b=this.querySelector('button'); if(b){ b.disabled=true; b.innerHTML='<i class=\'ri-loader-4-line om-spin\'></i> กำลังซิงค์...'; }">
                <input type="hidden" name="q" value="<?= htmlspecialchars($searchQuery) ?>">
                <input type="hidden" name="filter_status" value="<?= htmlspecialchars($statusFilter) ?>">
                <input type="hidden" name="page" value="<?= $page ?>">
                <button type="submit" class="om-btn om-btn-sync-all" title="ดึงและซิงค์สถานะออเดอร์ทั้งหมดกับ API ผู้ให้บริการแบบเรียลไทม์ทันที">
                  <i class="ri-refresh-line"></i> ซิงค์สถานะทั้งหมด
                </button>
              </form>

              <!-- Send Pending Button -->
              <form method="post" action="/admin/crons/orders" class="om-inline-form" onsubmit="if(!confirm('ส่งออเดอร์ที่ค้างส่งไปยังผู้ให้บริการทันที?')) return false; var b=this.querySelector('button'); if(b){ b.disabled=true; b.innerHTML='<i class=\'ri-loader-4-line om-spin\'></i> กำลังส่ง...'; } return true;">
                <button type="submit" class="om-btn om-btn-send-all" title="ส่งออเดอร์ค้างส่งทั้งหมดไปยัง API ทันที">
                  <i class="ri-send-plane-2-fill"></i> ส่งออเดอร์ค้างทันที
                </button>
              </form>

              <!-- Live Heartbeat Indicator -->
              <div class="om-live-badge" title="ระบบซิงค์อัตโนมัติทำงานร่วมกับ JustAnotherPanel API และ DirectAdmin Linux Crontab ตลอด 24 ชม.">
                <span class="om-pulse-dot"></span>
                <span>ซิงค์สด 24 ชม.</span>
              </div>
            </div>
          </div>
        </div>

        <!-- ── 3. Orders Cards List ── -->
        <div class="om-cards-list" id="omCardsContainer">
          <?php if (empty($orders)): ?>
            <div class="om-empty-card">
              <div class="om-empty-icon"><i class="ri-inbox-line"></i></div>
              <h3>ไม่พบรายการออเดอร์</h3>
              <p>ไม่มีรายการที่ตรงกับเงื่อนไขการค้นหาหรือตัวกรองที่เลือก</p>
              <?php if (!empty($searchQuery) || !empty($statusFilter)): ?>
                <a href="/admin/orders" class="om-btn om-btn-search" style="margin-top:12px;">ดูออเดอร์ทั้งหมด</a>
              <?php endif; ?>
            </div>
          <?php else: ?>
            <?php foreach ($orders as $ord): 
              $oid = (int)$ord['id'];
              $st = strtolower(trim((string)$ord['status']));
              if ($st === 'inprogress') $st = 'processing';
              $charge = (float)($ord['charge'] ?? 0);
              $qty = (int)($ord['quantity'] ?? 0);
              $apiOid = trim((string)($ord['api_orderid'] ?? ''));
              $hasApi = ($apiOid !== '' && $apiOid !== '-');
              $startCnt = (string)($ord['start_count'] ?? '-');
              $remains = (string)($ord['remains'] ?? '-');
              $hasErr = !empty($ord['api_error']) && $ord['api_error'] !== '-';
              
              // Progress calculation
              $progPct = 0;
              if ($st === 'completed') {
                $progPct = 100;
              } elseif ($st === 'processing') {
                if ($qty > 0 && is_numeric($remains)) {
                  $remVal = (float)$remains;
                  $doneVal = max(0, $qty - $remVal);
                  $progPct = (int)round(($doneVal / $qty) * 100);
                  $progPct = max(5, min(95, $progPct));
                } else {
                  $progPct = 35;
                }
              } elseif ($st === 'partial') {
                $progPct = 50;
              }

              // Provider Live Status string
              $apiSt = trim((string)($ord['api_status'] ?? ''));
              if ($apiSt === '') {
                if ($st === 'completed') $apiSt = 'Completed';
                elseif ($st === 'processing') $apiSt = 'In progress';
                elseif ($st === 'pending') $apiSt = $hasApi ? 'Pending' : '';
                elseif ($st === 'partial') $apiSt = 'Partial';
                elseif ($st === 'canceled') $apiSt = 'Canceled';
              }

              // Status meta
              if ($hasApi) {
                if ($st === 'completed') {
                  $stInfo = ['สำเร็จ (API: Completed)', 'om-st-completed', 'ri-checkbox-circle-fill'];
                } elseif ($st === 'processing') {
                  $stInfo = ['กำลังทำ (API: ' . ($apiSt ?: 'In progress') . ')', 'om-st-processing', 'ri-loader-4-line om-spin'];
                } elseif ($st === 'pending') {
                  $stInfo = ['ในคิว (API: ' . ($apiSt ?: 'Pending') . ')', 'om-st-pending', 'ri-time-line'];
                } elseif ($st === 'partial') {
                  $stInfo = ['บางส่วน (API: ' . ($apiSt ?: 'Partial') . ')', 'om-st-partial', 'ri-pie-chart-line'];
                } elseif ($st === 'canceled') {
                  $stInfo = ['ยกเลิก (API: ' . ($apiSt ?: 'Canceled') . ')', 'om-st-canceled', 'ri-close-circle-line'];
                } else {
                  $stInfo = [$st . ($apiSt ? ' (API: ' . $apiSt . ')' : ''), 'om-st-pending', 'ri-information-line'];
                }
              } else {
                $stInfo = ['รอส่งไป API (คอนจ็อปส่งออโต้)', 'om-st-pending om-pill-unsent', 'ri-send-plane-fill om-pulse'];
              }
            ?>
              <article class="om-card status-<?= $st ?> <?= $hasErr ? 'is-err' : '' ?>" id="omCard-<?= $oid ?>">
                
                <!-- Card Header: 2-Tier Structure (Always Clean on PC & Mobile) -->
                <div class="om-card-header" onclick="toggleOmDrawer(<?= $oid ?>)">
                  
                  <!-- Tier 1: ID, Status, Amount, and Toggle Arrow -->
                  <div class="om-hdr-top">
                    <div class="om-hdr-badges">
                      <span class="om-id-badge">#<?= $oid ?></span>
                      <span class="om-status-pill <?= $stInfo[1] ?>">
                        <i class="<?= $stInfo[2] ?>"></i> <?= $stInfo[0] ?>
                      </span>
                      <div class="om-amt-box">
                        <span class="om-amt-num">฿<?= number_format($charge, 2) ?></span>
                        <span class="om-amt-unit">บาท</span>
                      </div>
                    </div>
                    <div class="om-toggle-btn" aria-label="ดูรายละเอียด">
                      <i class="ri-arrow-down-s-line"></i>
                    </div>
                  </div>

                  <!-- Tier 2: Metadata (Client, Service, Quantity, API ID, Date) -->
                  <div class="om-hdr-sub">
                    <span class="om-meta-item om-meta-user" title="ชื่อลูกค้าผู้สั่งซื้อ">
                      <i class="ri-user-3-line"></i> <strong><?= htmlspecialchars((string)$ord['client']) ?></strong>
                    </span>
                    <span class="om-meta-item om-meta-svc" title="<?= htmlspecialchars((string)($ord['svc_name'] ?? $ord['service'])) ?>">
                      <i class="ri-shopping-cart-2-line"></i> <?= htmlspecialchars((string)($ord['svc_name'] ?? $ord['service'])) ?>
                    </span>
                    <span class="om-meta-item om-meta-qty" title="จำนวนที่สั่ง">
                      <i class="ri-stack-line"></i> <?= number_format($qty) ?> ชิ้น
                    </span>
                    <?php if ($hasApi): ?>
                      <span class="om-meta-item om-meta-api" title="รหัสอ้างอิงบน Provider API">
                        <i class="ri-cloud-line"></i> API: <strong>#<?= htmlspecialchars($apiOid) ?></strong>
                      </span>
                      <?php if (!empty($apiSt)): ?>
                        <span class="om-meta-item om-meta-apistatus" title="สถานะสดจากเว็บผู้ให้บริการ">
                          <i class="ri-pulse-line"></i> สถานะเว็บ: <strong class="om-apist-txt-<?= strtolower($apiSt) ?>"><?= htmlspecialchars($apiSt) ?></strong>
                        </span>
                      <?php endif; ?>
                    <?php else: ?>
                      <span class="om-meta-item om-meta-noapi text-warn">
                        <i class="ri-time-line om-pulse"></i> คอนจ็อปกำลังส่งออเดอร์ไป API อัตโนมัติ
                      </span>
                    <?php endif; ?>
                    <span class="om-meta-item om-meta-time" title="วันเวลาที่สั่งซื้อ">
                      <i class="ri-calendar-line"></i> <?= htmlspecialchars(substr((string)($ord['created_at'] ?? ''), 0, 16)) ?>
                    </span>
                    <?php if ($hasErr): ?>
                      <span class="om-meta-item om-meta-err" title="พบข้อผิดพลาด">
                        <i class="ri-alert-fill"></i> มีข้อความแจ้งเตือน
                      </span>
                    <?php endif; ?>
                  </div>

                  <!-- Live Progress Strip (for processing/completed) -->
                  <?php if ($st === 'processing' || $st === 'completed'): ?>
                    <div class="om-hdr-prog">
                      <div class="om-hdr-prog-bar <?= $st === 'completed' ? 'is-done' : '' ?>" style="width: <?= $progPct ?>%;"></div>
                    </div>
                  <?php endif; ?>
                </div>

                <!-- ── Accordion Drawer: 3 Inspection Boxes ── -->
                <div class="om-drawer" id="omDrawer-<?= $oid ?>">
                  <div class="om-drawer-grid">
                    
                    <!-- Box 1: Order Details -->
                    <div class="om-drawer-box om-box-details">
                      <div class="om-box-head">
                        <i class="ri-file-list-3-line"></i>
                        <h4>ข้อมูลคำสั่งซื้อ (#<?= $oid ?>)</h4>
                      </div>
                      <div class="om-kv-list">
                        <div class="om-kv-row">
                          <span class="om-kv-k">รหัสรายการ:</span>
                          <span class="om-kv-v"><strong>#<?= $oid ?></strong></span>
                        </div>
                        <div class="om-kv-row">
                          <span class="om-kv-k">ลูกค้า:</span>
                          <span class="om-kv-v text-blue">@<?= htmlspecialchars((string)$ord['client']) ?></span>
                        </div>
                        <div class="om-kv-row">
                          <span class="om-kv-k">บริการ:</span>
                          <span class="om-kv-v om-wrap-text"><?= htmlspecialchars((string)($ord['svc_name'] ?? $ord['service'])) ?></span>
                        </div>
                        <div class="om-kv-row">
                          <span class="om-kv-k">ลิงก์เป้าหมาย:</span>
                          <span class="om-kv-v om-wrap-text">
                            <?php if (!empty($ord['link'])): ?>
                              <a href="<?= htmlspecialchars((string)$ord['link']) ?>" target="_blank" rel="noopener noreferrer" class="om-link-out">
                                <i class="ri-external-link-line"></i> <?= htmlspecialchars((string)$ord['link']) ?>
                              </a>
                            <?php else: ?>
                              <span class="text-muted">-</span>
                            <?php endif; ?>
                          </span>
                        </div>
                        <div class="om-kv-row">
                          <span class="om-kv-k">จำนวน:</span>
                          <span class="om-kv-v"><strong><?= number_format($qty) ?></strong> หน่วย</span>
                        </div>
                        <div class="om-kv-row">
                          <span class="om-kv-k">ยอดเงินตัดกระเป๋า:</span>
                          <span class="om-kv-v text-ok"><strong>฿<?= number_format($charge, 2) ?></strong></span>
                        </div>
                        <div class="om-kv-row">
                          <span class="om-kv-k">วันเวลาสั่งซื้อ:</span>
                          <span class="om-kv-v text-muted"><?= htmlspecialchars((string)($ord['created_at'] ?? '-')) ?></span>
                        </div>
                        <?php if (!empty($ord['comments'])): ?>
                          <div class="om-kv-row">
                            <span class="om-kv-k">คอมเมนต์:</span>
                            <span class="om-kv-v om-wrap-text text-muted"><?= nl2br(htmlspecialchars((string)$ord['comments'])) ?></span>
                          </div>
                        <?php endif; ?>
                      </div>
                    </div>

                    <!-- Box 2: Provider API & Live Progress -->
                    <div class="om-drawer-box om-box-provider">
                      <div class="om-box-head">
                        <i class="ri-cloud-line"></i>
                        <h4>สถานะผู้ให้บริการ (API Provider)</h4>
                      </div>
                      <div class="om-prov-body">
                        <div class="om-prov-status-row">
                          <span class="om-prov-tag"><i class="ri-server-line"></i> JustAnotherPanel</span>
                          <?php if ($hasApi): ?>
                            <span class="om-prov-id">Order ID: <strong>#<?= htmlspecialchars($apiOid) ?></strong></span>
                          <?php else: ?>
                            <span class="om-prov-id text-warn"><i class="ri-time-line om-pulse"></i> รอดำเนินการส่ง API อัตโนมัติ</span>
                          <?php endif; ?>
                        </div>

                        <?php if ($hasApi): ?>
                          <div class="om-api-live-row">
                            <span class="om-api-live-lbl"><i class="ri-global-line"></i> สถานะสดจากเว็บ API:</span>
                            <span class="om-api-live-pill is-<?= strtolower($apiSt ?: $st) ?>">
                              <span class="om-pulse-dot-sm"></span> <strong><?= htmlspecialchars($apiSt ?: ucfirst($st)) ?></strong>
                            </span>
                          </div>
                        <?php endif; ?>

                        <!-- Progress Section -->
                        <div class="om-prog-container">
                          <div class="om-prog-labels">
                            <span>ความคืบหน้าของงาน</span>
                            <strong><?= $progPct ?>%</strong>
                          </div>
                          <div class="om-prog-track">
                            <div class="om-prog-fill <?= $st === 'completed' ? 'is-done' : '' ?>" style="width: <?= $progPct ?>%;"></div>
                          </div>
                          <div class="om-prog-counts">
                            <span>เริ่มนับ (Start): <strong><?= htmlspecialchars($startCnt) ?></strong></span>
                            <span>คงเหลือ (Remains): <strong class="<?= $remains === '0' ? 'text-ok' : 'text-warn' ?>"><?= htmlspecialchars($remains) ?></strong></span>
                          </div>
                        </div>

                        <?php if ($hasErr): ?>
                          <div class="om-err-notice">
                            <i class="ri-error-warning-fill"></i>
                            <div>
                              <strong>ข้อความแจ้งจาก API:</strong>
                              <p><?= htmlspecialchars((string)$ord['api_error']) ?></p>
                            </div>
                          </div>
                        <?php endif; ?>

                        <!-- Quick Single Sync Button inside Provider box -->
                        <?php if ($hasApi): ?>
                          <form method="post" action="/admin/orders/<?= $oid ?>/sync" class="om-box-sync-form" onsubmit="var b=this.querySelector('button'); if(b){ b.disabled=true; b.innerHTML='<i class=\'ri-loader-4-line om-spin\'></i> กำลังดึงสถานะ...'; }">
                            <button type="submit" class="om-btn om-btn-ghost om-btn-block">
                              <i class="ri-refresh-line"></i> ดึงสถานะออเดอร์นี้จาก Provider แบบเดี่ยว
                            </button>
                          </form>
                        <?php endif; ?>
                      </div>
                    </div>

                    <!-- Box 3: Admin Action Tools -->
                    <div class="om-drawer-box om-box-actions">
                      <div class="om-box-head">
                        <i class="ri-tools-line"></i>
                        <h4>เครื่องมือจัดการ &amp; แอ็กชั่น</h4>
                      </div>
                      <div class="om-act-body">
                        
                        <!-- 1. Change Status Form -->
                        <form method="post" action="/admin/orders/<?= $oid ?>/status" class="om-st-change-form" onsubmit="var b=this.querySelector('button'); if(b){ b.disabled=true; b.innerHTML='<i class=\'ri-loader-4-line om-spin\'></i> บันทึก...'; }">
                          <label class="om-field-lbl"><i class="ri-edit-line"></i> ปรับเปลี่ยนสถานะคำสั่งซื้อ</label>
                          <div class="om-field-row">
                            <select name="status" class="om-select">
                              <option value="pending" <?= $st === 'pending' ? 'selected' : '' ?>>รอส่ง (Pending)</option>
                              <option value="processing" <?= $st === 'processing' ? 'selected' : '' ?>>กำลังทำ (Processing)</option>
                              <option value="completed" <?= $st === 'completed' ? 'selected' : '' ?>>สำเร็จ (Completed)</option>
                              <option value="partial" <?= $st === 'partial' ? 'selected' : '' ?>>บางส่วน (Partial)</option>
                              <option value="canceled" <?= $st === 'canceled' ? 'selected' : '' ?>>ยกเลิก (Canceled)</option>
                            </select>
                            <button type="submit" class="om-btn om-btn-save">
                              <i class="ri-check-line"></i> บันทึก
                            </button>
                          </div>
                        </form>

                        <!-- 2. Fast Action Buttons -->
                        <div class="om-fast-btns">
                          <!-- Resend API -->
                          <form method="post" action="/admin/orders/<?= $oid ?>/resend" onsubmit="if(!confirm('ส่งออเดอร์ #<?= $oid ?> ไปยัง API ผู้ให้บริการ (พร้อมระบบ Auto-Fallback)?')) return false; var b=this.querySelector('button'); if(b){ b.disabled=true; b.innerHTML='<i class=\'ri-loader-4-line om-spin\'></i> กำลังส่ง...'; } return true;">
                            <button type="submit" class="om-btn om-btn-resend om-btn-block" title="ส่งออเดอร์ไปยัง API ผู้ให้บริการ">
                              <i class="ri-send-plane-fill"></i> ส่งคำสั่งซื้อไป API
                            </button>
                          </form>

                          <!-- Refund -->
                          <?php if ($st !== 'canceled'): ?>
                            <form method="post" action="/admin/orders/<?= $oid ?>/refund" onsubmit="if(!confirm('ยืนยันยกเลิกออเดอร์ #<?= $oid ?> และคืนเงิน ฿<?= number_format($charge, 2) ?> เข้ากระเป๋า @<?= htmlspecialchars((string)$ord['client']) ?>?')) return false; var b=this.querySelector('button'); if(b){ b.disabled=true; b.innerHTML='<i class=\'ri-loader-4-line om-spin\'></i> กำลังคืนเงิน...'; } return true;">
                              <button type="submit" class="om-btn om-btn-refund om-btn-block" title="ยกเลิกออเดอร์และคืนเงินเข้ากระเป๋าลูกค้า">
                                <i class="ri-refund-2-line"></i> ยกเลิก &amp; คืนเงินเต็มจำนวน
                              </button>
                            </form>
                          <?php else: ?>
                            <div class="om-refunded-badge">
                              <i class="ri-checkbox-circle-fill"></i> ออเดอร์นี้ถูกยกเลิก/คืนเงินเรียบร้อยแล้ว
                            </div>
                          <?php endif; ?>
                        </div>

                      </div>
                    </div>

                  </div>
                </div>

              </article>
            <?php endforeach; ?>
          <?php endif; ?>
        </div>

        <!-- ── 4. Pagination ── -->
        <?php if ($totalPages > 1): ?>
          <nav class="om-pagination">
            <span class="om-pag-info">หน้า <?= $page ?> จากทั้งหมด <?= $totalPages ?> หน้า (รวม <?= number_format($totalOrders) ?> รายการ)</span>
            <div class="om-pag-btns">
              <?php if ($page > 1): ?>
                <a href="/admin/orders?page=<?= $page - 1 ?><?= !empty($statusFilter) ? ('&status=' . urlencode($statusFilter)) : '' ?><?= !empty($searchQuery) ? ('&q=' . urlencode($searchQuery)) : '' ?>" class="om-pag-btn"><i class="ri-arrow-left-s-line"></i> ก่อนหน้า</a>
              <?php endif; ?>
              <?php for ($p = max(1, $page - 2); $p <= min($totalPages, $page + 2); $p++): ?>
                <a href="/admin/orders?page=<?= $p ?><?= !empty($statusFilter) ? ('&status=' . urlencode($statusFilter)) : '' ?><?= !empty($searchQuery) ? ('&q=' . urlencode($searchQuery)) : '' ?>" class="om-pag-btn <?= $p === $page ? 'is-active' : '' ?>"><?= $p ?></a>
              <?php endfor; ?>
              <?php if ($page < $totalPages): ?>
                <a href="/admin/orders?page=<?= $page + 1 ?><?= !empty($statusFilter) ? ('&status=' . urlencode($statusFilter)) : '' ?><?= !empty($searchQuery) ? ('&q=' . urlencode($searchQuery)) : '' ?>" class="om-pag-btn">ถัดไป <i class="ri-arrow-right-s-line"></i></a>
              <?php endif; ?>
            </div>
          </nav>
        <?php endif; ?>

      </div>

      <!-- Scoped Orders Master Stylesheet -->
      <style>
        .om-desk-wrap {
          width: 100% !important;
          max-width: 100% !important;
          box-sizing: border-box !important;
          padding: 8px 0 24px 0 !important;
          display: flex !important;
          flex-direction: column !important;
          gap: 16px !important;
          color: #e5e7eb !important;
          font-family: inherit !important;
        }

        /* Flash Alerts */
        .om-alert {
          display: flex !important;
          align-items: center !important;
          gap: 10px !important;
          padding: 12px 16px !important;
          border-radius: 10px !important;
          font-size: 14px !important;
          font-weight: 500 !important;
        }
        .om-alert-ok {
          background: rgba(16, 185, 129, 0.12) !important;
          border: 1px solid rgba(16, 185, 129, 0.3) !important;
          color: #10b981 !important;
        }
        .om-alert-err {
          background: rgba(239, 68, 68, 0.12) !important;
          border: 1px solid rgba(239, 68, 68, 0.3) !important;
          color: #ef4444 !important;
        }

        /* KPI Grid: 6 on Desktop, 2x3 on Mobile */
        .om-kpi-grid {
          display: grid !important;
          grid-template-columns: repeat(6, 1fr) !important;
          gap: 12px !important;
          width: 100% !important;
          box-sizing: border-box !important;
        }
        @media (max-width: 1100px) {
          .om-kpi-grid { grid-template-columns: repeat(3, 1fr) !important; }
        }
        @media (max-width: 640px) {
          .om-kpi-grid { grid-template-columns: repeat(2, 1fr) !important; gap: 8px !important; }
        }
        .om-kpi-card {
          background: #111827 !important;
          border: 1px solid #1f2937 !important;
          border-radius: 12px !important;
          padding: 14px 16px !important;
          display: flex !important;
          align-items: center !important;
          justify-content: space-between !important;
          text-decoration: none !important;
          color: inherit !important;
          transition: all 0.2s ease !important;
        }
        .om-kpi-card:hover, .om-kpi-card.is-active {
          border-color: #3b82f6 !important;
          background: #172033 !important;
          transform: translateY(-1px) !important;
        }
        .om-kpi-info {
          display: flex !important;
          flex-direction: column !important;
          gap: 2px !important;
          min-width: 0 !important;
        }
        .om-kpi-lbl {
          font-size: 12px !important;
          color: #9ca3af !important;
          white-space: nowrap !important;
          overflow: hidden !important;
          text-overflow: ellipsis !important;
        }
        .om-kpi-val {
          font-size: 22px !important;
          font-weight: 700 !important;
          line-height: 1.2 !important;
          color: #f9fafb !important;
        }
        .om-kpi-sub {
          font-size: 11px !important;
          color: #6b7280 !important;
          white-space: nowrap !important;
          overflow: hidden !important;
          text-overflow: ellipsis !important;
        }
        .om-kpi-icon {
          width: 38px !important;
          height: 38px !important;
          border-radius: 10px !important;
          display: flex !important;
          align-items: center !important;
          justify-content: center !important;
          font-size: 18px !important;
          flex-shrink: 0 !important;
        }
        .om-ico-all { background: rgba(59, 130, 246, 0.12) !important; color: #3b82f6 !important; }
        .om-ico-pending { background: rgba(245, 158, 11, 0.12) !important; color: #f59e0b !important; }
        .om-ico-processing { background: rgba(14, 165, 233, 0.12) !important; color: #0ea5e9 !important; }
        .om-ico-completed { background: rgba(16, 185, 129, 0.12) !important; color: #10b981 !important; }
        .om-ico-partial { background: rgba(168, 85, 247, 0.12) !important; color: #a855f7 !important; }
        .om-ico-canceled { background: rgba(239, 68, 68, 0.12) !important; color: #ef4444 !important; }

        /* Toolbar */
        .om-toolbar {
          background: #111827 !important;
          border: 1px solid #1f2937 !important;
          border-radius: 12px !important;
          padding: 12px 16px !important;
          display: flex !important;
          flex-direction: column !important;
          gap: 12px !important;
        }
        .om-filter-tabs {
          display: flex !important;
          flex-wrap: wrap !important;
          gap: 8px !important;
        }
        .om-tab {
          display: inline-flex !important;
          align-items: center !important;
          gap: 6px !important;
          padding: 6px 12px !important;
          border-radius: 8px !important;
          background: #1f2937 !important;
          color: #d1d5db !important;
          text-decoration: none !important;
          font-size: 13px !important;
          font-weight: 500 !important;
          transition: all 0.15s ease !important;
        }
        .om-tab:hover { background: #374151 !important; color: #fff !important; }
        .om-tab.is-active { background: #3b82f6 !important; color: #fff !important; }
        .om-tab-badge {
          background: rgba(0,0,0,0.25) !important;
          padding: 1px 6px !important;
          border-radius: 6px !important;
          font-size: 11px !important;
          font-weight: 600 !important;
        }

        .om-search-bar {
          display: flex !important;
          flex-wrap: wrap !important;
          align-items: center !important;
          justify-content: space-between !important;
          gap: 12px !important;
        }
        .om-search-form {
          display: flex !important;
          align-items: center !important;
          gap: 8px !important;
          flex: 1 !important;
          min-width: 260px !important;
        }
        .om-search-input-wrap {
          position: relative !important;
          flex: 1 !important;
        }
        .om-search-icon {
          position: absolute !important;
          left: 12px !important;
          top: 50% !important;
          transform: translateY(-50%) !important;
          color: #9ca3af !important;
          font-size: 16px !important;
        }
        .om-search-input {
          width: 100% !important;
          background: #1f2937 !important;
          border: 1px solid #374151 !important;
          border-radius: 8px !important;
          padding: 8px 36px 8px 36px !important;
          color: #f9fafb !important;
          font-size: 13px !important;
          box-sizing: border-box !important;
        }
        .om-search-input:focus {
          outline: none !important;
          border-color: #3b82f6 !important;
          background: #111827 !important;
        }
        .om-search-clear {
          position: absolute !important;
          right: 10px !important;
          top: 50% !important;
          transform: translateY(-50%) !important;
          color: #9ca3af !important;
          text-decoration: none !important;
        }
        .om-actions-right {
          display: flex !important;
          flex-wrap: wrap !important;
          align-items: center !important;
          gap: 8px !important;
        }
        .om-inline-form { margin: 0 !important; display: inline-block !important; }

        /* Buttons */
        .om-btn {
          display: inline-flex !important;
          align-items: center !important;
          justify-content: center !important;
          gap: 6px !important;
          padding: 8px 14px !important;
          border-radius: 8px !important;
          border: none !important;
          font-size: 13px !important;
          font-weight: 500 !important;
          cursor: pointer !important;
          text-decoration: none !important;
          transition: all 0.15s ease !important;
          white-space: nowrap !important;
        }
        .om-btn-search { background: #374151 !important; color: #fff !important; }
        .om-btn-search:hover { background: #4b5563 !important; }
        .om-btn-sync-all {
          background: #10b981 !important;
          color: #fff !important;
          box-shadow: 0 1px 2px rgba(0,0,0,0.2) !important;
        }
        .om-btn-sync-all:hover { background: #059669 !important; }
        .om-btn-send-all { background: #3b82f6 !important; color: #fff !important; }
        .om-btn-send-all:hover { background: #2563eb !important; }
        .om-btn-save { background: #10b981 !important; color: #fff !important; padding: 7px 14px !important; }
        .om-btn-resend { background: #0284c7 !important; color: #fff !important; }
        .om-btn-resend:hover { background: #0369a1 !important; }
        .om-btn-refund { background: #dc2626 !important; color: #fff !important; }
        .om-btn-refund:hover { background: #b91c1c !important; }
        .om-btn-ghost { background: #1f2937 !important; border: 1px solid #374151 !important; color: #d1d5db !important; }
        .om-btn-ghost:hover { background: #374151 !important; color: #fff !important; }
        .om-btn-block { width: 100% !important; }

        .om-live-badge {
          display: inline-flex !important;
          align-items: center !important;
          gap: 6px !important;
          background: rgba(16, 185, 129, 0.12) !important;
          border: 1px solid rgba(16, 185, 129, 0.25) !important;
          color: #10b981 !important;
          padding: 6px 10px !important;
          border-radius: 8px !important;
          font-size: 12px !important;
          font-weight: 500 !important;
        }
        .om-pulse-dot {
          width: 8px !important;
          height: 8px !important;
          border-radius: 50% !important;
          background: #10b981 !important;
          box-shadow: 0 0 6px #10b981 !important;
          animation: omPulse 2s infinite !important;
        }
        @keyframes omPulse {
          0% { opacity: 1; transform: scale(1); }
          50% { opacity: 0.4; transform: scale(0.85); }
          100% { opacity: 1; transform: scale(1); }
        }

        /* Order Cards List */
        .om-cards-list {
          display: flex !important;
          flex-direction: column !important;
          gap: 10px !important;
          width: 100% !important;
          box-sizing: border-box !important;
        }
        .om-card {
          background: #111827 !important;
          border: 1px solid #1f2937 !important;
          border-left: 4px solid #374151 !important;
          border-radius: 12px !important;
          overflow: hidden !important;
          transition: border-color 0.2s ease, box-shadow 0.2s ease !important;
        }
        .om-card.status-pending { border-left-color: #f59e0b !important; }
        .om-card.status-processing { border-left-color: #0ea5e9 !important; }
        .om-card.status-completed { border-left-color: #10b981 !important; }
        .om-card.status-partial { border-left-color: #a855f7 !important; }
        .om-card.status-canceled { border-left-color: #ef4444 !important; }
        .om-card.is-err { border-color: rgba(239, 68, 68, 0.4) !important; }

        /* Card Header */
        .om-card-header {
          padding: 12px 16px !important;
          cursor: pointer !important;
          user-select: none !important;
          display: flex !important;
          flex-direction: column !important;
          gap: 8px !important;
          position: relative !important;
        }
        .om-card-header:hover { background: #161f30 !important; }

        .om-hdr-top {
          display: flex !important;
          align-items: center !important;
          justify-content: space-between !important;
          width: 100% !important;
        }
        .om-hdr-badges {
          display: flex !important;
          align-items: center !important;
          gap: 10px !important;
          flex-wrap: wrap !important;
        }
        .om-id-badge {
          font-size: 14px !important;
          font-weight: 700 !important;
          color: #f9fafb !important;
          background: #1f2937 !important;
          padding: 3px 8px !important;
          border-radius: 6px !important;
        }
        .om-status-pill {
          display: inline-flex !important;
          align-items: center !important;
          gap: 5px !important;
          padding: 3px 10px !important;
          border-radius: 20px !important;
          font-size: 12px !important;
          font-weight: 600 !important;
        }
        .om-st-pending { background: rgba(245, 158, 11, 0.15) !important; color: #fbbf24 !important; }
        .om-st-processing { background: rgba(14, 165, 233, 0.15) !important; color: #38bdf8 !important; }
        .om-st-completed { background: rgba(16, 185, 129, 0.15) !important; color: #34d399 !important; }
        .om-st-partial { background: rgba(168, 85, 247, 0.15) !important; color: #c084fc !important; }
        .om-st-canceled { background: rgba(239, 68, 68, 0.15) !important; color: #f87171 !important; }
        .om-pill-unsent {
          background: rgba(245, 158, 11, 0.25) !important;
          color: #fbbf24 !important;
          border: 1px dashed rgba(245, 158, 11, 0.6) !important;
        }
        .om-meta-apistatus {
          display: inline-flex !important;
          align-items: center !important;
          gap: 4px !important;
        }
        .om-apist-txt-completed { color: #34d399 !important; font-weight: 700 !important; }
        .om-apist-txt-processing, .om-apist-txt-inprogress { color: #38bdf8 !important; font-weight: 700 !important; }
        .om-apist-txt-pending { color: #fbbf24 !important; font-weight: 700 !important; }
        .om-apist-txt-partial { color: #c084fc !important; font-weight: 700 !important; }
        .om-apist-txt-canceled { color: #f87171 !important; font-weight: 700 !important; }

        .om-api-live-row {
          display: flex !important;
          align-items: center !important;
          justify-content: space-between !important;
          background: #0f172a !important;
          padding: 8px 12px !important;
          border-radius: 8px !important;
          border: 1px solid #1e293b !important;
          margin-bottom: 12px !important;
          font-size: 13px !important;
        }
        .om-api-live-lbl {
          color: #94a3b8 !important;
          display: flex !important;
          align-items: center !important;
          gap: 6px !important;
        }
        .om-api-live-pill {
          display: inline-flex !important;
          align-items: center !important;
          gap: 6px !important;
          padding: 3px 10px !important;
          border-radius: 20px !important;
          font-size: 12px !important;
          font-weight: 600 !important;
        }
        .om-api-live-pill.is-completed {
          background: rgba(16, 185, 129, 0.15) !important;
          color: #34d399 !important;
          border: 1px solid rgba(16, 185, 129, 0.3) !important;
        }
        .om-api-live-pill.is-processing, .om-api-live-pill.is-inprogress {
          background: rgba(14, 165, 233, 0.15) !important;
          color: #38bdf8 !important;
          border: 1px solid rgba(14, 165, 233, 0.3) !important;
        }
        .om-api-live-pill.is-pending {
          background: rgba(245, 158, 11, 0.15) !important;
          color: #fbbf24 !important;
          border: 1px solid rgba(245, 158, 11, 0.3) !important;
        }
        .om-api-live-pill.is-partial {
          background: rgba(168, 85, 247, 0.15) !important;
          color: #c084fc !important;
          border: 1px solid rgba(168, 85, 247, 0.3) !important;
        }
        .om-api-live-pill.is-canceled {
          background: rgba(239, 68, 68, 0.15) !important;
          color: #f87171 !important;
          border: 1px solid rgba(239, 68, 68, 0.3) !important;
        }
        .om-pulse-dot-sm {
          width: 6px !important;
          height: 6px !important;
          border-radius: 50% !important;
          background: currentColor !important;
          animation: om-pulse 1.8s infinite !important;
        }

        .om-amt-box {
          display: inline-flex !important;
          align-items: baseline !important;
          gap: 3px !important;
        }
        .om-amt-num {
          font-size: 15px !important;
          font-weight: 700 !important;
          color: #10b981 !important;
        }
        .om-amt-unit { font-size: 11px !important; color: #9ca3af !important; }

        .om-toggle-btn {
          width: 28px !important;
          height: 28px !important;
          border-radius: 6px !important;
          background: #1f2937 !important;
          color: #9ca3af !important;
          display: flex !important;
          align-items: center !important;
          justify-content: center !important;
          font-size: 16px !important;
          transition: all 0.2s ease !important;
          flex-shrink: 0 !important;
        }
        .om-card.is-open .om-toggle-btn {
          transform: rotate(180deg) !important;
          background: #3b82f6 !important;
          color: #fff !important;
        }

        .om-hdr-sub {
          display: flex !important;
          flex-wrap: wrap !important;
          align-items: center !important;
          gap: 6px 14px !important;
          font-size: 12px !important;
          color: #9ca3af !important;
        }
        .om-meta-item {
          display: inline-flex !important;
          align-items: center !important;
          gap: 4px !important;
        }
        .om-meta-user strong { color: #60a5fa !important; }
        .om-meta-svc {
          color: #e5e7eb !important;
          max-width: 320px !important;
          white-space: nowrap !important;
          overflow: hidden !important;
          text-overflow: ellipsis !important;
        }
        .om-meta-api strong { color: #f59e0b !important; }
        .om-meta-noapi { color: #9ca3af !important; font-style: italic !important; }
        .om-meta-err { color: #f87171 !important; font-weight: 600 !important; }

        .om-hdr-prog {
          width: 100% !important;
          height: 3px !important;
          background: #1f2937 !important;
          border-radius: 2px !important;
          overflow: hidden !important;
          margin-top: 4px !important;
        }
        .om-hdr-prog-bar {
          height: 100% !important;
          background: #0ea5e9 !important;
          transition: width 0.3s ease !important;
        }
        .om-hdr-prog-bar.is-done { background: #10b981 !important; }

        /* Accordion Drawer */
        .om-drawer {
          display: none !important;
          border-top: 1px solid #1f2937 !important;
          background: #0b0f19 !important;
          padding: 16px !important;
        }
        .om-card.is-open .om-drawer { display: block !important; }

        .om-drawer-grid {
          display: grid !important;
          grid-template-columns: 1fr 1fr 1fr !important;
          gap: 14px !important;
        }
        @media (max-width: 960px) {
          .om-drawer-grid { grid-template-columns: 1fr !important; }
        }

        .om-drawer-box {
          background: #111827 !important;
          border: 1px solid #1f2937 !important;
          border-radius: 10px !important;
          padding: 14px !important;
          display: flex !important;
          flex-direction: column !important;
          gap: 12px !important;
        }
        .om-box-head {
          display: flex !important;
          align-items: center !important;
          gap: 8px !important;
          font-size: 13px !important;
          font-weight: 600 !important;
          color: #f3f4f6 !important;
          border-bottom: 1px solid #1f2937 !important;
          padding-bottom: 8px !important;
        }
        .om-box-head i { font-size: 16px !important; color: #3b82f6 !important; }

        .om-kv-list {
          display: flex !important;
          flex-direction: column !important;
          gap: 8px !important;
          font-size: 12px !important;
        }
        .om-kv-row {
          display: flex !important;
          justify-content: space-between !important;
          align-items: flex-start !important;
          gap: 8px !important;
        }
        .om-kv-k { color: #9ca3af !important; flex-shrink: 0 !important; }
        .om-kv-v { color: #f9fafb !important; text-align: right !important; word-break: break-word !important; }
        .om-wrap-text { max-width: 240px !important; text-align: right !important; }
        .om-link-out { color: #38bdf8 !important; text-decoration: none !important; word-break: break-all !important; }
        .om-link-out:hover { text-decoration: underline !important; }

        .om-prov-body {
          display: flex !important;
          flex-direction: column !important;
          gap: 12px !important;
        }
        .om-prov-status-row {
          display: flex !important;
          justify-content: space-between !important;
          align-items: center !important;
          font-size: 12px !important;
        }
        .om-prov-tag {
          background: #1f2937 !important;
          padding: 3px 8px !important;
          border-radius: 6px !important;
          color: #d1d5db !important;
        }
        .om-prov-id strong { color: #f59e0b !important; }

        .om-prog-container {
          background: #172033 !important;
          border: 1px solid rgba(59, 130, 246, 0.2) !important;
          border-radius: 8px !important;
          padding: 10px !important;
          display: flex !important;
          flex-direction: column !important;
          gap: 6px !important;
        }
        .om-prog-labels {
          display: flex !important;
          justify-content: space-between !important;
          font-size: 12px !important;
          color: #93c5fd !important;
        }
        .om-prog-track {
          height: 6px !important;
          background: #1f2937 !important;
          border-radius: 3px !important;
          overflow: hidden !important;
        }
        .om-prog-fill {
          height: 100% !important;
          background: #0ea5e9 !important;
          transition: width 0.3s ease !important;
        }
        .om-prog-fill.is-done { background: #10b981 !important; }
        .om-prog-counts {
          display: flex !important;
          justify-content: space-between !important;
          font-size: 11px !important;
          color: #9ca3af !important;
        }

        .om-err-notice {
          background: rgba(239, 68, 68, 0.12) !important;
          border: 1px solid rgba(239, 68, 68, 0.25) !important;
          border-radius: 8px !important;
          padding: 8px 10px !important;
          display: flex !important;
          gap: 8px !important;
          font-size: 11px !important;
          color: #f87171 !important;
        }
        .om-err-notice p { margin: 2px 0 0 0 !important; color: #fca5a5 !important; }

        .om-act-body {
          display: flex !important;
          flex-direction: column !important;
          gap: 12px !important;
        }
        .om-st-change-form {
          display: flex !important;
          flex-direction: column !important;
          gap: 6px !important;
        }
        .om-field-lbl {
          font-size: 11px !important;
          color: #9ca3af !important;
          font-weight: 500 !important;
        }
        .om-field-row {
          display: flex !important;
          gap: 6px !important;
        }
        .om-select {
          flex: 1 !important;
          background: #1f2937 !important;
          border: 1px solid #374151 !important;
          border-radius: 6px !important;
          padding: 6px 10px !important;
          color: #f9fafb !important;
          font-size: 12px !important;
        }
        .om-fast-btns {
          display: flex !important;
          flex-direction: column !important;
          gap: 8px !important;
        }
        .om-refunded-badge {
          background: rgba(239, 68, 68, 0.12) !important;
          border: 1px solid rgba(239, 68, 68, 0.25) !important;
          color: #f87171 !important;
          padding: 8px !important;
          border-radius: 6px !important;
          font-size: 12px !important;
          text-align: center !important;
        }

        /* Pagination */
        .om-pagination {
          display: flex !important;
          flex-wrap: wrap !important;
          justify-content: space-between !important;
          align-items: center !important;
          gap: 12px !important;
          padding: 12px 16px !important;
          background: #111827 !important;
          border: 1px solid #1f2937 !important;
          border-radius: 12px !important;
          font-size: 12px !important;
        }
        .om-pag-info { color: #9ca3af !important; }
        .om-pag-btns { display: flex !important; gap: 4px !important; }
        .om-pag-btn {
          padding: 4px 10px !important;
          border-radius: 6px !important;
          background: #1f2937 !important;
          color: #d1d5db !important;
          text-decoration: none !important;
          font-size: 12px !important;
        }
        .om-pag-btn:hover, .om-pag-btn.is-active {
          background: #3b82f6 !important;
          color: #fff !important;
        }

        /* Empty State */
        .om-empty-card {
          background: #111827 !important;
          border: 1px dashed #374151 !important;
          border-radius: 12px !important;
          padding: 40px 20px !important;
          text-align: center !important;
        }
        .om-empty-icon { font-size: 36px !important; color: #6b7280 !important; margin-bottom: 8px !important; }
        .om-empty-card h3 { font-size: 16px !important; color: #f9fafb !important; margin: 0 0 6px 0 !important; }
        .om-empty-card p { font-size: 13px !important; color: #9ca3af !important; margin: 0 !important; }

        .om-spin { animation: omSpinAnim 1s linear infinite !important; }
        @keyframes omSpinAnim { 100% { transform: rotate(360deg); } }
        .text-ok { color: #10b981 !important; }
        .text-warn { color: #f59e0b !important; }
        .text-blue { color: #38bdf8 !important; }
        .text-purple { color: #c084fc !important; }
        .text-red { color: #ef4444 !important; }
        .text-muted { color: #6b7280 !important; }
      </style>

      <script>
        function toggleOmDrawer(oid) {
          var card = document.getElementById('omCard-' + oid);
          if (card) {
            card.classList.toggle('is-open');
          }
        }
      </script>
    </main>
    <?php
    $newMain = ob_get_clean();

    return substr($html, 0, $mStart) . $newMain . substr($html, $mEnd + strlen('</main>'));
}
