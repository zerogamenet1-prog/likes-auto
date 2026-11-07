<?php
declare(strict_types=1);

/**
 * Modern In-Flow Expandable Ticket Cards for Admin Support Desk.
 * Replaces legacy minimal cards with responsive KPI cards, smart order previews,
 * customer balances, modern chat thread bubbles, canned quick responses, and full lifecycle controls.
 */
function la_patch_admin_tickets(string $html): string {
    $mStart = strpos($html, '<main class="dash-content">');
    if ($mStart === false) {
        return $html;
    }
    $mEnd = strpos($html, '</main>', $mStart);
    if ($mEnd === false) {
        return $html;
    }

    // Extract any existing 'ok' or 'err' alert
    $okMsg = '';
    $errMsg = '';
    if (preg_match('#<div class="adm-ok"><i class="[^"]*"></i>\s*(.*?)</div>#s', $html, $mOk)) {
        $okMsg = trim(strip_tags($mOk[1]));
    } elseif (isset($_GET['ok']) && $_GET['ok'] !== '') {
        $okMsg = htmlspecialchars(urldecode($_GET['ok']));
    }
    if (preg_match('#<div class="adm-error"><i class="[^"]*"></i>\s*(.*?)</div>#s', $html, $mErr)) {
        $errMsg = trim(strip_tags($mErr[1]));
    } elseif (isset($_GET['err']) && $_GET['err'] !== '') {
        $errMsg = htmlspecialchars(urldecode($_GET['err']));
    }

    // Active status filter from query
    $statusFilter = isset($_GET['status']) ? trim((string)$_GET['status']) : '';
    $searchQuery = isset($_GET['q']) ? trim((string)$_GET['q']) : '';

    // Database lookup for richest possible context
    $possibleDbPaths = [
        __DIR__ . '/.la-db-restore-latest.db',
        __DIR__ . '/.la-db-restore-d1qyg5az73cs4unx8jl9trbw.db',
        __DIR__ . '/../.la-db-restore-latest.db',
        __DIR__ . '/../.la-db-restore-d1qyg5az73cs4unx8jl9trbw.db',
        dirname(__DIR__, 2) . '/live_app.db',
    ];
    $dbPath = '';
    foreach ($possibleDbPaths as $p) {
        if (file_exists($p)) {
            $dbPath = $p;
            break;
        }
    }

    $tickets = [];
    $replies = [];
    $clientsMap = [];
    $clientsList = [];
    $ordersMap = [];

    $counts = [
        'all' => 0,
        'open' => 0,
        'answered' => 0,
        'closed' => 0,
    ];

    $hasDb = false;
    if (file_exists($dbPath) && class_exists('SQLite3')) {
        try {
            $db = new SQLite3($dbPath, SQLITE3_OPEN_READONLY);
            $hasDb = true;

            // Clients
            $res = @$db->query('SELECT id, username, email, balance FROM clients');
            if ($res) {
                while ($row = $res->fetchArray(SQLITE3_ASSOC)) {
                    $clientsMap[$row['username']] = $row;
                    $clientsList[] = $row;
                }
            }

            // Orders
            $res = @$db->query('SELECT id, client, service, service_id, quantity, charge, status, link FROM orders');
            if ($res) {
                while ($row = $res->fetchArray(SQLITE3_ASSOC)) {
                    $ordersMap[(int)$row['id']] = $row;
                }
            }

            // Replies
            $res = @$db->query('SELECT id, ticket_id, author, message, created_at FROM ticket_replies ORDER BY id ASC');
            if ($res) {
                while ($row = $res->fetchArray(SQLITE3_ASSOC)) {
                    $tid = (int)$row['ticket_id'];
                    if (!isset($replies[$tid])) {
                        $replies[$tid] = [];
                    }
                    $replies[$tid][] = $row;
                }
            }

            // Tickets
            $res = @$db->query('SELECT id, client, subject, status, created_at, message, reply FROM tickets ORDER BY id DESC');
            if ($res) {
                while ($row = $res->fetchArray(SQLITE3_ASSOC)) {
                    $st = $row['status'] ?: 'open';
                    $counts['all']++;
                    if ($st === 'open' || $st === 'pending') {
                        $counts['open']++;
                    } elseif ($st === 'answered') {
                        $counts['answered']++;
                    } elseif ($st === 'closed') {
                        $counts['closed']++;
                    }

                    // Filter
                    if ($statusFilter !== '') {
                        if ($statusFilter === 'open' && $st !== 'open' && $st !== 'pending') {
                            continue;
                        }
                        if ($statusFilter !== 'open' && $st !== $statusFilter) {
                            continue;
                        }
                    }

                    if ($searchQuery !== '') {
                        $ql = mb_strtolower($searchQuery);
                        $txt = mb_strtolower((string)$row['id'] . ' ' . $row['client'] . ' ' . $row['subject'] . ' ' . $row['message'] . ' ' . ($row['reply'] ?? ''));
                        if (mb_strpos($txt, $ql) === false) {
                            continue;
                        }
                    }

                    $tickets[] = $row;
                }
            }
            $db->close();
        } catch (\Throwable $e) {
            $hasDb = false;
        }
    }

    // Merge tickets_override.json for 100% immediate consistency
    $ovFile = __DIR__ . '/tickets_override.json';
    if (is_file($ovFile)) {
        $tOverrides = json_decode((string)file_get_contents($ovFile), true) ?: [];
        foreach ($tickets as &$tRow) {
            $tId = (int)$tRow['id'];
            if (isset($tOverrides[$tId])) {
                if (isset($tOverrides[$tId]['status'])) {
                    $tRow['status'] = $tOverrides[$tId]['status'];
                }
                if (!empty($tOverrides[$tId]['replies'])) {
                    if (!isset($replies[$tId])) {
                        $replies[$tId] = [];
                    }
                    foreach ($tOverrides[$tId]['replies'] as $oRep) {
                        $dup = false;
                        foreach ($replies[$tId] as $exRep) {
                            if (($exRep['message'] ?? '') === $oRep['message'] && ($exRep['created_at'] ?? '') === $oRep['created_at']) {
                                $dup = true;
                                break;
                            }
                        }
                        if (!$dup) {
                            $replies[$tId][] = $oRep;
                            $tRow['reply'] = $oRep['message'];
                        }
                    }
                }
            }
        }
        unset($tRow);
        
        // Recount based on merged statuses
        $counts = ['all' => count($tickets), 'open' => 0, 'answered' => 0, 'closed' => 0];
        foreach ($tickets as $tRow) {
            $st = $tRow['status'] ?: 'open';
            if ($st === 'open' || $st === 'pending') $counts['open']++;
            elseif ($st === 'answered') $counts['answered']++;
            elseif ($st === 'closed') $counts['closed']++;
        }
    }

    // Fallback: parse tickets from HTML if DB is not available
    if (!$hasDb || empty($tickets)) {
        $ticketCardsChunk = substr($html, $mStart, $mEnd - $mStart);
        $pattern = '#<article class="adm-card adm-ticket">(.*?)</article>#s';
        if (preg_match_all($pattern, $ticketCardsChunk, $mCards)) {
            foreach ($mCards[1] as $cHtml) {
                $tid = 0;
                $subject = 'สอบถาม';
                $status = 'open';
                $client = 'ลูกค้า';
                $createdAt = '';
                $message = '';
                $cardReplies = [];

                if (preg_match('#<b>\#(\d+)\s*(.*?)</b>#', $cHtml, $mSub)) {
                    $tid = (int)$mSub[1];
                    $subject = trim($mSub[2]);
                }
                if (preg_match('#<span class="adm-badge\s+([^"]+)">([^<]+)</span>#', $cHtml, $mBadge)) {
                    $badgeCls = trim($mBadge[1]);
                    $badgeText = trim($mBadge[2]);
                    if (strpos($badgeCls, 'closed') !== false || $badgeText === 'ปิด') {
                        $status = 'closed';
                    } elseif (strpos($badgeCls, 'answered') !== false || $badgeText === 'ตอบแล้ว') {
                        $status = 'answered';
                    } else {
                        $status = 'open';
                    }
                }
                if (preg_match('#<p class="la-muted">([^·<]+)\s*·\s*([^<]+)</p>#', $cHtml, $mMeta)) {
                    $client = trim($mMeta[1]);
                    $createdAt = trim($mMeta[2]);
                }
                if (preg_match_all('#<div class="adm-thread"><b>([^:<]+):</b>\s*(.*?)(?:<span class="la-muted">([^<]*)</span>)?</div>#s', $cHtml, $mThreads, PREG_SET_ORDER)) {
                    foreach ($mThreads as $th) {
                        $author = trim($th[1]);
                        $text = trim(strip_tags($th[2]));
                        $tTime = isset($th[3]) ? trim($th[3]) : '';
                        if ($author === 'ลูกค้า' && empty($message)) {
                            $message = $text;
                        } else {
                            $cardReplies[] = [
                                'author' => $author,
                                'message' => $text,
                                'created_at' => $tTime,
                            ];
                        }
                    }
                }

                $counts['all']++;
                if ($status === 'open') $counts['open']++;
                elseif ($status === 'answered') $counts['answered']++;
                elseif ($status === 'closed') $counts['closed']++;

                if ($statusFilter !== '' && $status !== $statusFilter) {
                    continue;
                }

                $replies[$tid] = $cardReplies;
                $tickets[] = [
                    'id' => $tid,
                    'client' => $client,
                    'subject' => $subject,
                    'status' => $status,
                    'created_at' => $createdAt,
                    'message' => $message,
                    'reply' => !empty($cardReplies) ? end($cardReplies)['message'] : '',
                ];
            }
        }
    }

    // Build New Rich Support Desk HTML
    ob_start();
    ?>
    <div class="ticket-desk-container">

      <?php if ($okMsg): ?>
      <div class="adm-ok"><i class="ri-checkbox-circle-fill"></i> <?= $okMsg ?></div>
      <?php endif; ?>
      <?php if ($errMsg): ?>
      <div class="adm-error"><i class="ri-error-warning-fill"></i> <?= $errMsg ?></div>
      <?php endif; ?>

      <!-- Top Hero Header -->
      <div class="ticket-header-row">
        <div class="ticket-header-title">
          <div class="ticket-header-badge"><i class="ri-customer-service-2-line"></i> Support Desk</div>
          <h1>ตั๋วสนับสนุน & ซัพพอร์ตลูกค้า</h1>
          <p class="adm-sub">ศูนย์รับแจ้งปัญหา ตอบกลับลูกค้า เชื่อมโยงข้อมูลออเดอร์ และจัดการจบงานอย่างรวดเร็ว</p>
        </div>
        <div class="ticket-header-actions">
          <button type="button" class="la-btn la-btn-ghost ticket-btn-refresh" onclick="location.reload()">
            <i class="ri-refresh-line"></i> รีเฟรช
          </button>
          <button type="button" class="la-btn ticket-btn-create" onclick="openCreateTicketModal()">
            <i class="ri-add-line"></i> เปิดตั๋วใหม่ถึงลูกค้า
          </button>
        </div>
      </div>

      <!-- KPI Overview Cards -->
      <div class="ticket-kpi-grid">
        <a href="/admin/tickets" id="kpi-all" data-kpi-status="all" onclick="filterTicketsTab('all'); return false;" class="ticket-kpi-card <?= empty($statusFilter)?'active':'' ?>">
          <div class="ticket-kpi-icon is-all"><i class="ri-ticket-2-line"></i></div>
          <div class="ticket-kpi-info">
            <em>ตั๋วทั้งหมด</em>
            <strong id="kpi-count-all"><?= $counts['all'] ?></strong>
            <p>ประวัติตั๋วทั้งหมดในระบบ</p>
          </div>
        </a>
        <a href="/admin/tickets?status=open" id="kpi-open" data-kpi-status="open" onclick="filterTicketsTab('open'); return false;" class="ticket-kpi-card is-pending <?= ($statusFilter==='open')?'active':'' ?>">
          <div class="ticket-kpi-icon is-open">
            <i class="ri-time-line"></i>
            <?php if ($counts['open'] > 0): ?><span class="ticket-pulse-dot"></span><?php endif; ?>
          </div>
          <div class="ticket-kpi-info">
            <em>รอแอดมินตอบ</em>
            <strong class="text-amber" id="kpi-count-open"><?= $counts['open'] ?></strong>
            <p><?= ($counts['open'] > 0)?'ลูกค้ากำลังรอการช่วยเหลือ':'ไม่มีตั๋วค้างตอบ' ?></p>
          </div>
        </a>
        <a href="/admin/tickets?status=answered" id="kpi-answered" data-kpi-status="answered" onclick="filterTicketsTab('answered'); return false;" class="ticket-kpi-card <?= ($statusFilter==='answered')?'active':'' ?>">
          <div class="ticket-kpi-icon is-answered"><i class="ri-chat-check-line"></i></div>
          <div class="ticket-kpi-info">
            <em>ตอบแล้ว</em>
            <strong class="text-indigo" id="kpi-count-answered"><?= $counts['answered'] ?></strong>
            <p>ส่งคำตอบแล้ว รอลูกค้า</p>
          </div>
        </a>
        <a href="/admin/tickets?status=closed" id="kpi-closed" data-kpi-status="closed" onclick="filterTicketsTab('closed'); return false;" class="ticket-kpi-card <?= ($statusFilter==='closed')?'active':'' ?>">
          <div class="ticket-kpi-icon is-closed"><i class="ri-checkbox-circle-line"></i></div>
          <div class="ticket-kpi-info">
            <em>ปิดแล้ว</em>
            <strong class="text-emerald" id="kpi-count-closed"><?= $counts['closed'] ?></strong>
            <p>แก้ไขและจบเรื่องแล้ว</p>
          </div>
        </a>
      </div>

      <!-- Control & Filter Bar -->
      <div class="ticket-control-bar">
        <div class="ticket-tabs">
          <a href="/admin/tickets" id="tab-all" data-tab-status="all" onclick="filterTicketsTab('all'); return false;" class="ticket-tab <?= empty($statusFilter)?'active':'' ?>">
            ทั้งหมด <span class="ticket-tab-count"><?= $counts['all'] ?></span>
          </a>
          <a href="/admin/tickets?status=open" id="tab-open" data-tab-status="open" onclick="filterTicketsTab('open'); return false;" class="ticket-tab <?= ($statusFilter==='open')?'active':'' ?>">
            รอแอดมินตอบ <span class="ticket-tab-count text-amber"><?= $counts['open'] ?></span>
          </a>
          <a href="/admin/tickets?status=answered" id="tab-answered" data-tab-status="answered" onclick="filterTicketsTab('answered'); return false;" class="ticket-tab <?= ($statusFilter==='answered')?'active':'' ?>">
            ตอบแล้ว <span class="ticket-tab-count"><?= $counts['answered'] ?></span>
          </a>
          <a href="/admin/tickets?status=closed" id="tab-closed" data-tab-status="closed" onclick="filterTicketsTab('closed'); return false;" class="ticket-tab <?= ($statusFilter==='closed')?'active':'' ?>">
            ปิดแล้ว <span class="ticket-tab-count"><?= $counts['closed'] ?></span>
          </a>
        </div>
        <div class="ticket-search-box">
          <i class="ri-search-line"></i>
          <input type="search" id="ticketSearchInput" placeholder="ค้นหารหัสตั๋ว, ลูกค้า, ออเดอร์, ข้อความ..." value="<?= htmlspecialchars($searchQuery) ?>" oninput="filterTicketsLive()">
        </div>
      </div>

      <!-- Tickets List -->
      <div class="ticket-list" id="ticketListContainer">
        <?php if (!empty($tickets)): ?>
          <?php foreach ($tickets as $idx => $r):
              $tid = (int)$r['id'];
              $clientName = htmlspecialchars((string)$r['client']);
              $clientInitial = mb_strtoupper(mb_substr($clientName, 0, 1));
              $subject = htmlspecialchars((string)$r['subject']);
              $st = $r['status'] ?: 'open';
              $rawMsg = htmlspecialchars((string)$r['message']);
              $threadReps = $replies[$tid] ?? [];
              $clientInfo = $clientsMap[$r['client']] ?? null;

              // Check if order ID is referenced in message or subject
              $refOrderId = null;
              if (is_numeric(trim((string)$r['message']))) {
                  $refOrderId = (int)trim((string)$r['message']);
              } elseif (preg_match('#(?:order|ออเดอร์|เลขที่)?\s*#?(\d+)#iu', (string)$r['message'], $mO)) {
                  $refOrderId = (int)$mO[1];
              }
              $refOrder = ($refOrderId && isset($ordersMap[$refOrderId])) ? $ordersMap[$refOrderId] : null;
          ?>
            <article class="ticket-card is-<?= $st ?>" id="ticket-item-<?= $tid ?>" data-ticket-id="<?= $tid ?>" data-client="<?= mb_strtolower($clientName) ?>" data-subject="<?= mb_strtolower($subject) ?>" data-status="<?= $st ?>" data-text="<?= mb_strtolower($rawMsg) ?>">
              
              <!-- Accordion Header -->
              <header class="ticket-card-header" onclick="toggleTicketDrawer(<?= $tid ?>)">
                <div class="ticket-header-left">
                  <span class="ticket-badge is-<?= $st ?>">
                    <?php if ($st === 'open' || $st === 'pending'): ?>
                      <i class="ri-time-line"></i> รอตอบ
                    <?php elseif ($st === 'answered'): ?>
                      <i class="ri-chat-check-line"></i> ตอบแล้ว
                    <?php elseif ($st === 'closed'): ?>
                      <i class="ri-checkbox-circle-line"></i> ปิดแล้ว
                    <?php else: ?>
                      <?= htmlspecialchars($st) ?>
                    <?php endif; ?>
                  </span>
                  <span class="ticket-id-tag">#<?= $tid ?></span>
                  <strong class="ticket-subject-title"><?= $subject ?></strong>
                  
                  <div class="ticket-client-pill">
                    <span class="ticket-avatar"><?= $clientInitial ?></span>
                    <span class="ticket-username"><?= $clientName ?></span>
                    <?php if ($clientInfo && isset($clientInfo['balance'])): ?>
                      <span class="ticket-balance-tag">฿<?= number_format((float)$clientInfo['balance'], 2) ?></span>
                    <?php endif; ?>
                  </div>
                </div>

                <div class="ticket-header-right">
                  <?php if ($refOrder): ?>
                  <div class="ticket-order-pill" title="คลิกดูข้อมูลออเดอร์" onclick="event.stopPropagation(); window.open('/admin/orders?q=<?= $refOrder['id'] ?>', '_blank')">
                    <i class="ri-shopping-bag-3-line"></i> ออเดอร์ #<?= $refOrder['id'] ?> · ฿<?= number_format((float)$refOrder['charge'], 2) ?>
                  </div>
                  <?php endif; ?>

                  <div class="ticket-msg-count">
                    <i class="ri-message-3-line"></i> <?= count($threadReps) + 1 ?>
                  </div>
                  <time class="ticket-time"><?= htmlspecialchars((string)$r['created_at']) ?></time>
                  <button type="button" class="ticket-chevron-btn" aria-label="เปิด/ปิด รายละเอียด">
                    <i class="ri-arrow-down-s-line"></i>
                  </button>
                </div>
              </header>

              <!-- Accordion Drawer (Expanded Body) -->
              <div class="ticket-card-drawer" id="ticket-drawer-<?= $tid ?>" style="display: <?= ($idx === 0 && ($st === 'open' || count($tickets) === 1)) ? 'block' : 'none' ?>;">
                
                <!-- Context Insight Strip -->
                <div class="ticket-insight-strip">
                  <div class="ticket-insight-client">
                    <i class="ri-user-smile-line"></i>
                    <span>ลูกค้า: <strong><?= $clientName ?></strong></span>
                    <?php if ($clientInfo): ?>
                      <span class="text-muted">| อีเมล: <?= htmlspecialchars((string)($clientInfo['email'] ?? '-')) ?> | ยอดคงเหลือ: <strong class="text-emerald">฿<?= number_format((float)($clientInfo['balance'] ?? 0), 2) ?></strong></span>
                      <a href="/admin/clients?q=<?= urlencode($clientName) ?>" target="_blank" class="ticket-insight-link"><i class="ri-external-link-line"></i> ดูโปรไฟล์ลูกค้า</a>
                    <?php endif; ?>
                  </div>

                  <?php if ($refOrder): 
                      $stMap = [
                          'pending' => 'รอส่ง',
                          'processing' => 'กำลังทำ',
                          'completed' => 'สำเร็จ',
                          'partial' => 'บางส่วน',
                          'canceled' => 'ยกเลิก',
                      ];
                      $ordStTh = $stMap[$refOrder['status']] ?? $refOrder['status'];
                      $svcTitle = $refOrder['service'] ?? ($refOrder['service_name'] ?? 'บริการ');
                  ?>
                  <div class="ticket-insight-order">
                    <i class="ri-box-3-line"></i>
                    <span>ออเดอร์อ้างอิง: <strong>#<?= $refOrder['id'] ?></strong> (<?= htmlspecialchars((string)$svcTitle) ?>)</span>
                    <span class="text-muted">| ยอดสั่ง: <?= number_format((float)$refOrder['quantity']) ?> | ราคา: ฿<?= number_format((float)$refOrder['charge'], 2) ?> | สถานะ: <span class="ticket-order-st is-<?= $refOrder['status'] ?>"><?= htmlspecialchars((string)$ordStTh) ?></span></span>
                    <a href="/admin/orders?q=<?= $refOrder['id'] ?>" target="_blank" class="ticket-insight-link"><i class="ri-external-link-line"></i> จัดการออเดอร์นี้</a>
                  </div>
                  <?php endif; ?>
                </div>

                <!-- Chat History Thread -->
                <div class="ticket-chat-thread">
                  
                  <!-- Original Customer Message -->
                  <div class="ticket-bubble-row is-client">
                    <div class="ticket-bubble-avatar"><?= $clientInitial ?></div>
                    <div class="ticket-bubble-content">
                      <div class="ticket-bubble-meta">
                        <strong><?= $clientName ?></strong> <span class="ticket-role-badge">ลูกค้า</span>
                        <time><?= htmlspecialchars((string)$r['created_at']) ?></time>
                      </div>
                      <div class="ticket-bubble-body">
                        <?php if ($refOrderId): ?>
                          <p class="text-muted" style="margin-bottom:4px;"><i class="ri-information-line"></i> อ้างอิงถึงออเดอร์หมายเลข <strong>#<?= $refOrderId ?></strong></p>
                        <?php endif; ?>
                        <p><?= nl2br($rawMsg) ?></p>
                      </div>
                    </div>
                  </div>

                  <!-- Follow-up Replies -->
                  <?php if (!empty($threadReps)): ?>
                    <?php foreach ($threadReps as $m):
                        $auth = (string)$m['author'];
                        $isAdmin = (in_array(mb_strtolower($auth), ['admin', 'แอดมิน', 'ทีมงาน', 'staff'], true));
                    ?>
                      <div class="ticket-bubble-row <?= $isAdmin ? 'is-admin' : 'is-client' ?>">
                        <div class="ticket-bubble-avatar">
                          <?php if ($isAdmin): ?><i class="ri-shield-star-fill"></i><?php else: ?><?= mb_strtoupper(mb_substr($auth, 0, 1)) ?><?php endif; ?>
                        </div>
                        <div class="ticket-bubble-content">
                          <div class="ticket-bubble-meta">
                            <strong><?= $isAdmin ? 'ทีมงาน LIKES AUTO (' . htmlspecialchars($auth) . ')' : htmlspecialchars($auth) ?></strong>
                            <?php if ($isAdmin): ?>
                              <span class="ticket-role-badge is-staff"><i class="ri-check-double-line"></i> แอดมิน</span>
                            <?php else: ?>
                              <span class="ticket-role-badge">ลูกค้า</span>
                            <?php endif; ?>
                            <time><?= htmlspecialchars((string)($m['created_at'] ?? '')) ?></time>
                          </div>
                          <div class="ticket-bubble-body">
                            <?= nl2br(htmlspecialchars((string)$m['message'])) ?>
                          </div>
                        </div>
                      </div>
                    <?php endforeach; ?>
                  <?php else: ?>
                    <?php if (!empty($r['reply'])): ?>
                    <div class="ticket-bubble-row is-admin">
                      <div class="ticket-bubble-avatar"><i class="ri-shield-star-fill"></i></div>
                      <div class="ticket-bubble-content">
                        <div class="ticket-bubble-meta">
                          <strong>ทีมงาน LIKES AUTO (แอดมิน)</strong>
                          <span class="ticket-role-badge is-staff"><i class="ri-check-double-line"></i> แอดมิน</span>
                        </div>
                        <div class="ticket-bubble-body">
                          <?= nl2br(htmlspecialchars((string)$r['reply'])) ?>
                        </div>
                      </div>
                    </div>
                    <?php endif; ?>
                  <?php endif; ?>

                </div>

                <!-- Quick Canned Responses Bar -->
                <div class="ticket-canned-bar">
                  <span class="ticket-canned-lbl"><i class="ri-flashlight-line"></i> ข้อความตอบด่วน:</span>
                  <button type="button" class="ticket-canned-chip" onclick="insertCanned(<?= $tid ?>, 'สวัสดีครับ แอดมินรับเรื่องแล้วครับ กำลังเร่งตรวจสอบกับระบบแม่ให้ทันทีครับผม')">⚡ รับเรื่องตรวจสอบ</button>
                  <button type="button" class="ticket-canned-chip" onclick="insertCanned(<?= $tid ?>, 'ตรวจสอบแล้ว ออเดอร์ของคุณดำเนินการเสร็จสมบูรณ์เรียบร้อยแล้วครับ ขอบคุณที่ใช้บริการครับ')">⚡ แจ้งเสร็จสมบูรณ์</button>
                  <button type="button" class="ticket-canned-chip" onclick="insertCanned(<?= $tid ?>, 'แอดมินได้ทำการยกเลิกออเดอร์และคืนยอดเงินเข้ากระเป๋าของคุณเรียบร้อยแล้วครับ สามารถสั่งใหม่ได้ทันทีครับ')">⚡ แจ้งคืนเงินแล้ว</button>
                  <button type="button" class="ticket-canned-chip" onclick="insertCanned(<?= $tid ?>, 'ระบบกำลังเร่งดำเนินการให้อยู่นะครับ อาจมีความล่าช้าเล็กน้อยจากคิวผู้ให้บริการ ขออภัยในความไม่สะดวกครับ')">⚡ กำลังเร่งคิวงาน</button>
                  <button type="button" class="ticket-canned-chip" onclick="insertCanned(<?= $tid ?>, 'รบกวนขอข้อมูลลิงก์เป้าหมาย หรือภาพหน้าจอเพิ่มเติม เพื่อให้ทีมงานช่วยตรวจสอบได้เร็วยิ่งขึ้นครับ')">⚡ ขอข้อมูลเพิ่มเติม</button>
                  <button type="button" class="ticket-canned-chip" onclick="insertCanned(<?= $tid ?>, 'แก้ไขปัญหาให้เรียบร้อยแล้วครับ หากมีข้อสงสัยหรือติดปัญหาด้านใดเพิ่มเติม สามารถติดต่อได้ตลอด 24 ชม. ครับ')">⚡ จบเรื่องเรียบร้อย</button>
                </div>

                <!-- Action & Reply Form -->
                <div class="ticket-action-box">
                  <form method="post" action="/admin/tickets/<?= $tid ?>/reply" class="ticket-reply-form" id="reply-form-<?= $tid ?>">
                    <div class="ticket-textarea-wrap">
                      <textarea class="la-input ticket-textarea" id="reply-text-<?= $tid ?>" name="message" rows="3" placeholder="พิมพ์ข้อความตอบกลับลูกค้าที่นี่..." required></textarea>
                    </div>
                    <input type="hidden" name="and_close" id="and-close-<?= $tid ?>" value="0">

                    <div class="ticket-form-footer">
                      <div class="ticket-footer-left">
                        <button type="submit" class="la-btn ticket-btn-send" onclick="document.getElementById('and-close-<?= $tid ?>').value='0'">
                          <i class="ri-send-plane-fill"></i> ส่งคำตอบ
                        </button>
                        <button type="submit" class="la-btn la-btn-ghost ticket-btn-reply-close" onclick="document.getElementById('and-close-<?= $tid ?>').value='1'">
                          <i class="ri-checkbox-circle-fill"></i> ตอบพร้อมปิดตั๋ว
                        </button>
                      </div>

                      <div class="ticket-footer-right">
                        <?php if ($st !== 'closed'): ?>
                        <button type="button" class="la-btn la-btn-ghost text-amber" onclick="postTicketAction(<?= $tid ?>, 'close')">
                          <i class="ri-lock-line"></i> ปิดตั๋ว
                        </button>
                        <?php else: ?>
                        <button type="button" class="la-btn la-btn-ghost text-indigo" onclick="postTicketAction(<?= $tid ?>, 'reopen')">
                          <i class="ri-restart-line"></i> เปิดตั๋วใหม่
                        </button>
                        <?php endif; ?>

                        <button type="button" class="la-btn la-btn-ghost text-danger" onclick="confirmDeleteTicket(<?= $tid ?>)">
                          <i class="ri-delete-bin-line"></i> ลบตั๋ว
                        </button>
                      </div>
                    </div>
                  </form>
                </div>

              </div>
            </article>
          <?php endforeach; ?>
        <?php endif; ?>
        <div class="ticket-empty-state" id="ticketEmptyState" style="display: <?= empty($tickets) ? 'flex' : 'none' ?>;">
          <div class="ticket-empty-icon"><i class="ri-chat-smile-2-line"></i></div>
          <h3>ไม่มีรายการตั๋วสนับสนุน</h3>
          <p class="adm-sub">ไม่มีตั๋วที่ตรงกับเงื่อนไขการค้นหาในขณะนี้</p>
        </div>
      </div>

    </div>

    <!-- Admin Create Ticket Modal -->
    <div class="ticket-modal-scrim" id="createTicketModal" style="display:none;" onclick="if(event.target===this) closeCreateTicketModal()">
      <div class="ticket-modal-card">
        <div class="ticket-modal-header">
          <h3><i class="ri-add-circle-fill text-indigo"></i> เปิดตั๋วใหม่ถึงลูกค้า</h3>
          <button type="button" class="dash-iconbtn" onclick="closeCreateTicketModal()"><i class="ri-close-line"></i></button>
        </div>
        <form method="post" action="/admin/tickets/create" class="ticket-modal-form">
          <div class="ticket-form-group">
            <label>เลือกลูกค้า <span class="text-danger">*</span></label>
            <select class="la-input" name="client" required>
              <option value="">-- เลือกลูกค้า --</option>
              <?php foreach ($clientsList as $c): ?>
                <option value="<?= htmlspecialchars((string)$c['username']) ?>"><?= htmlspecialchars((string)$c['username']) ?> (ยอดเงิน ฿<?= number_format((float)($c['balance'] ?? 0), 2) ?>)</option>
              <?php endforeach; ?>
            </select>
          </div>
          <div class="ticket-form-group">
            <label>หัวข้อตั๋ว <span class="text-danger">*</span></label>
            <input type="text" class="la-input" name="subject" required placeholder="เช่น แจ้งคืนเงินออเดอร์ / แจ้งความคืบหน้าบริการ">
          </div>
          <div class="ticket-form-group">
            <label>ข้อความเริ่มต้น <span class="text-danger">*</span></label>
            <textarea class="la-input" name="message" rows="4" required placeholder="ระบุข้อความหรือคำชี้แจงถึงลูกค้า..."></textarea>
          </div>
          <div class="ticket-modal-actions">
            <button type="button" class="la-btn la-btn-ghost" onclick="closeCreateTicketModal()">ยกเลิก</button>
            <button type="submit" class="la-btn ticket-btn-send"><i class="ri-send-plane-fill"></i> สร้างและส่งตั๋ว</button>
          </div>
        </form>
      </div>
    </div>

    <script>
    var currentStatusFilter = '<?= $statusFilter ?: "all" ?>';

    function toggleTicketDrawer(id) {
      var drawer = document.getElementById('ticket-drawer-' + id);
      var card = document.getElementById('ticket-item-' + id);
      if (!drawer) return;
      if (drawer.style.display === 'none' || drawer.style.display === '') {
        drawer.style.display = 'block';
        if (card) card.classList.add('is-expanded');
      } else {
        drawer.style.display = 'none';
        if (card) card.classList.remove('is-expanded');
      }
    }

    function insertCanned(id, text) {
      var area = document.getElementById('reply-text-' + id);
      if (area) {
        area.value = text;
        area.focus();
      }
    }

    function postTicketAction(id, action) {
      var form = document.createElement('form');
      form.method = 'POST';
      form.action = '/admin/tickets/' + id + '/' + action;
      document.body.appendChild(form);
      form.submit();
    }

    function confirmDeleteTicket(id) {
      if (confirm('คุณแน่ใจหรือไม่ว่าต้องการลบตั๋ว #' + id + ' นี้? ข้อมูลข้อความทั้งหมดจะถูกลบถาวร')) {
        postTicketAction(id, 'delete');
      }
    }

    function openCreateTicketModal() {
      var m = document.getElementById('createTicketModal');
      if (m) m.style.display = 'flex';
    }

    function closeCreateTicketModal() {
      var m = document.getElementById('createTicketModal');
      if (m) m.style.display = 'none';
    }

    function filterTicketsTab(status) {
      currentStatusFilter = status || 'all';

      document.querySelectorAll('.ticket-tab').forEach(function(t) {
        var tSt = t.getAttribute('data-tab-status') || '';
        if (tSt === currentStatusFilter || (!currentStatusFilter && tSt === 'all')) {
          t.classList.add('active');
        } else {
          t.classList.remove('active');
        }
      });

      document.querySelectorAll('.ticket-kpi-card').forEach(function(k) {
        var kSt = k.getAttribute('data-kpi-status') || '';
        if (kSt === currentStatusFilter || (!currentStatusFilter && kSt === 'all')) {
          k.classList.add('active');
        } else {
          k.classList.remove('active');
        }
      });

      applyCombinedFilter();

      var newUrl = '/admin/tickets' + (currentStatusFilter && currentStatusFilter !== 'all' ? '?status=' + currentStatusFilter : '');
      if (window.history && window.history.replaceState) {
        window.history.replaceState(null, '', newUrl);
      }
    }

    function filterTicketsLive() {
      applyCombinedFilter();
    }

    function applyCombinedFilter() {
      var query = (document.getElementById('ticketSearchInput') ? document.getElementById('ticketSearchInput').value : '').toLowerCase().trim();
      var items = document.querySelectorAll('.ticket-card');
      var visible = 0;

      items.forEach(function(el) {
        var st = el.getAttribute('data-status') || '';
        var id = el.getAttribute('data-ticket-id') || '';
        var client = el.getAttribute('data-client') || '';
        var subject = el.getAttribute('data-subject') || '';
        var text = el.getAttribute('data-text') || '';

        var matchStatus = (currentStatusFilter === 'all' || !currentStatusFilter || st === currentStatusFilter || (currentStatusFilter === 'open' && (st === 'open' || st === 'pending')));
        var matchQuery = (!query || id.indexOf(query) !== -1 || client.indexOf(query) !== -1 || subject.indexOf(query) !== -1 || text.indexOf(query) !== -1);

        if (matchStatus && matchQuery) {
          el.style.display = '';
          visible++;
        } else {
          el.style.display = 'none';
        }
      });

      var emptyEl = document.getElementById('ticketEmptyState');
      if (emptyEl) {
        emptyEl.style.display = (visible === 0) ? 'flex' : 'none';
      }
    }
    </script>
    <?php
    $newContent = ob_get_clean();

    $html = substr($html, 0, $mStart) . '<main class="dash-content">' . $newContent . '</main>' . substr($html, $mEnd + strlen('</main>'));
    return $html;
}
