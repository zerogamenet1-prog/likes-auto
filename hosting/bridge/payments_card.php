<?php
declare(strict_types=1);

/**
 * Modern Admin Payments Desk & Slip Inspector for LIKES-AUTO.
 * Fully responsive, showing complete client details, current wallet balance,
 * Thai promptpay digital E-slip visualization, physical slip image viewer with
 * interactive Lightbox zoom modal, admin slip upload/attachment tool,
 * and 1-click approve/reject/recheck/unlock management actions.
 */
function la_patch_admin_payments(string $html): string {
    $mStart = strpos($html, '<main class="dash-content">');
    if ($mStart === false) {
        return $html;
    }
    $mEnd = strpos($html, '</main>', $mStart);
    if ($mEnd === false) {
        return $html;
    }

    // Extract any existing alert from URL or session
    $okMsg = '';
    $errMsg = '';
    if (isset($_GET['ok']) && $_GET['ok'] !== '') {
        $okKey = trim((string)$_GET['ok']);
        $okMap = [
            'paid' => 'อนุมัติการเติมเงินและเพิ่มเครดิตเข้ากระเป๋าลูกค้าสำเร็จเรียบร้อย',
            'canceled' => 'ปฏิเสธรายการเติมเงินเรียบร้อยแล้ว',
            'matched' => 'จับคู่ยอดเงินโอนและอนุมัติเข้ากระเป๋าลูกค้าสำเร็จ',
            'recheck_ok' => 'ตรวจสลิปใหม่ผ่าน — เพิ่มเครดิตเข้ากระเป๋าลูกค้าแล้ว',
            'unlock_ok' => 'ปลดล็อกประวัติสลิปแล้ว สามารถนำมาตรวจใหม่ได้',
            'note_ok' => 'บันทึกโน้ตข้อมูลเรียบร้อยแล้ว',
            'upload_ok' => 'อัปโหลดและแนบไฟล์สลิปใหม่สำเร็จเรียบร้อย',
        ];
        $okMsg = $okMap[$okKey] ?? htmlspecialchars(urldecode($okKey));
    }
    if (isset($_GET['err']) && $_GET['err'] !== '') {
        $errMsg = htmlspecialchars(urldecode((string)$_GET['err']));
    }

    // Active filters
    $statusFilter = isset($_GET['status']) ? trim((string)$_GET['status']) : '';
    $searchQuery = isset($_GET['q']) ? trim((string)$_GET['q']) : '';
    $methodFilter = isset($_GET['method']) ? trim((string)$_GET['method']) : '';

    // Database lookup
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

    $payments = [];
    $clientsMap = [];
    $methodsList = [];

    $counts = [
        'all' => 0,
        'pending' => 0,
        'paid' => 0,
        'canceled' => 0,
    ];
    $sums = [
        'all' => 0.0,
        'pending' => 0.0,
        'paid' => 0.0,
        'canceled' => 0.0,
    ];

    if ($dbPath !== '' && class_exists('SQLite3')) {
        try {
            $db = new SQLite3($dbPath, SQLITE3_OPEN_READONLY);

            // Fetch clients map
            $cRes = @$db->query('SELECT id, username, email, balance FROM clients');
            if ($cRes) {
                while ($cRow = $cRes->fetchArray(SQLITE3_ASSOC)) {
                    $clientsMap[$cRow['username']] = $cRow;
                }
            }

            // Fetch payments
            $pRes = @$db->query('SELECT id, client, method, amount, status, created_at, slip, note, ref_code, method_id, kind, trans_ref FROM payments ORDER BY id DESC');
            if ($pRes) {
                while ($row = $pRes->fetchArray(SQLITE3_ASSOC)) {
                    $st = $row['status'] ?: 'pending';
                    $amt = floatval($row['amount'] ?? 0);
                    $m = trim((string)($row['method'] ?? ''));
                    if ($m !== '' && !in_array($m, $methodsList, true)) {
                        $methodsList[] = $m;
                    }

                    // Counts & sums
                    $counts['all']++;
                    $sums['all'] += $amt;
                    if ($st === 'pending') {
                        $counts['pending']++;
                        $sums['pending'] += $amt;
                    } elseif ($st === 'paid') {
                        $counts['paid']++;
                        $sums['paid'] += $amt;
                    } elseif ($st === 'canceled') {
                        $counts['canceled']++;
                        $sums['canceled'] += $amt;
                    }

                    // Filter
                    if ($statusFilter !== '' && $st !== $statusFilter) {
                        continue;
                    }
                    if ($methodFilter !== '' && $m !== $methodFilter) {
                        continue;
                    }
                    if ($searchQuery !== '') {
                        $ql = mb_strtolower($searchQuery);
                        $tString = mb_strtolower((string)$row['id'] . ' ' . ($row['client'] ?? '') . ' ' . $m . ' ' . ($row['ref_code'] ?? '') . ' ' . ($row['trans_ref'] ?? '') . ' ' . ($row['note'] ?? '') . ' ' . $amt);
                        if (mb_strpos($tString, $ql) === false) {
                            continue;
                        }
                    }

                    $payments[] = $row;
                }
            }
            $db->close();
        } catch (\Throwable $e) {}
    }

    // Merge payments_override.json if exists for instant consistency
    $ovFile = __DIR__ . '/payments_override.json';
    if (is_file($ovFile)) {
        $pOverrides = json_decode((string)file_get_contents($ovFile), true) ?: [];
        foreach ($payments as &$pRow) {
            $pId = (int)$pRow['id'];
            if (isset($pOverrides[$pId])) {
                if (isset($pOverrides[$pId]['status'])) {
                    $pRow['status'] = $pOverrides[$pId]['status'];
                }
                if (isset($pOverrides[$pId]['slip'])) {
                    $pRow['slip'] = $pOverrides[$pId]['slip'];
                }
                if (isset($pOverrides[$pId]['note'])) {
                    $pRow['note'] = $pOverrides[$pId]['note'];
                }
                if (isset($pOverrides[$pId]['trans_ref'])) {
                    $pRow['trans_ref'] = $pOverrides[$pId]['trans_ref'];
                }
            }
        }
        unset($pRow);
    }

    ob_start();
    ?>
    <style>
      /* Reset & Container */
      .pm-desk-wrap {
        display: flex !important;
        flex-direction: column !important;
        gap: 12px !important;
        margin-bottom: 2.5rem !important;
        font-family: inherit !important;
        width: 100% !important;
        max-width: 1200px !important;
        margin-left: auto !important;
        margin-right: auto !important;
        box-sizing: border-box !important;
      }
      .pm-desk-wrap * {
        box-sizing: border-box !important;
      }

      /* KPI Counters: 4 cols on desktop, 2x2 on mobile */
      .pm-kpi-grid {
        display: grid !important;
        grid-template-columns: repeat(4, 1fr) !important;
        gap: 10px !important;
        width: 100% !important;
      }
      @media (max-width: 860px) {
        .pm-kpi-grid {
          grid-template-columns: repeat(2, 1fr) !important;
          gap: 8px !important;
        }
      }

      .pm-kpi-card {
        background: #141c2b !important;
        border: 1px solid #1f2d45 !important;
        border-radius: 10px !important;
        padding: 10px 12px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: space-between !important;
        text-decoration: none !important;
        color: inherit !important;
        transition: transform .18s ease, border-color .18s ease !important;
        min-width: 0 !important;
        overflow: hidden !important;
      }
      .pm-kpi-card:hover {
        transform: translateY(-2px) !important;
        border-color: #3b82f6 !important;
      }
      .pm-kpi-card.is-active {
        border-color: #3b82f6 !important;
        background: linear-gradient(145deg, #162238 0%, #111a29 100%) !important;
        box-shadow: 0 0 0 1px #3b82f6 !important;
      }
      .pm-kpi-card.is-pending-alert {
        border-color: #f59e0b !important;
        background: linear-gradient(145deg, #2a2012 0%, #161a24 100%) !important;
      }
      .pm-kpi-card.is-pending-alert .pm-kpi-icon {
        color: #f59e0b !important;
        background: rgba(245, 158, 11, 0.15) !important;
      }
      .pm-kpi-info {
        min-width: 0 !important;
        flex: 1 !important;
        overflow: hidden !important;
      }
      .pm-kpi-title {
        display: block !important;
        font-size: 11px !important;
        color: #94a3b8 !important;
        font-weight: 500 !important;
        margin-bottom: 2px !important;
        white-space: nowrap !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
      }
      .pm-kpi-val {
        font-size: 20px !important;
        font-weight: 800 !important;
        color: #f8fafc !important;
        line-height: 1.15 !important;
        display: block !important;
        white-space: nowrap !important;
      }
      .pm-kpi-sub {
        display: block !important;
        font-size: 11px !important;
        color: #cbd5e1 !important;
        margin-top: 2px !important;
        white-space: nowrap !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
      }
      .pm-kpi-icon {
        width: 36px !important;
        height: 36px !important;
        border-radius: 8px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        font-size: 18px !important;
        background: rgba(59, 130, 246, 0.12) !important;
        color: #3b82f6 !important;
        flex-shrink: 0 !important;
        margin-left: 6px !important;
      }
      .pm-kpi-card.kpi-paid .pm-kpi-icon {
        color: #10b981 !important;
        background: rgba(16, 185, 129, 0.12) !important;
      }
      .pm-kpi-card.kpi-canceled .pm-kpi-icon {
        color: #ef4444 !important;
        background: rgba(239, 68, 68, 0.12) !important;
      }

      /* Toolbar */
      .pm-toolbar {
        background: #141c2b !important;
        border: 1px solid #1f2d45 !important;
        border-radius: 10px !important;
        padding: 10px 12px !important;
        display: flex !important;
        flex-direction: column !important;
        gap: 8px !important;
        width: 100% !important;
      }
      .pm-toolbar-top {
        display: flex !important;
        align-items: center !important;
        justify-content: space-between !important;
        flex-wrap: wrap !important;
        gap: 6px !important;
      }
      .pm-tabs {
        display: inline-flex !important;
        gap: 3px !important;
        background: #0d131f !important;
        padding: 2px !important;
        border-radius: 6px !important;
        border: 1px solid #1f2d45 !important;
        flex-wrap: wrap !important;
      }
      .pm-tab-btn {
        padding: 5px 9px !important;
        font-size: 11px !important;
        font-weight: 500 !important;
        color: #94a3b8 !important;
        border-radius: 5px !important;
        text-decoration: none !important;
        transition: all .15s ease !important;
        display: inline-flex !important;
        align-items: center !important;
        gap: 4px !important;
        white-space: nowrap !important;
      }
      .pm-tab-btn:hover {
        color: #f8fafc !important;
        background: rgba(255,255,255,0.04) !important;
      }
      .pm-tab-btn.is-active {
        background: #3b82f6 !important;
        color: #fff !important;
        font-weight: 600 !important;
      }
      .pm-tab-badge {
        font-size: 10px !important;
        padding: 1px 4px !important;
        border-radius: 999px !important;
        background: rgba(0,0,0,0.3) !important;
      }

      .pm-quick-actions {
        display: flex !important;
        align-items: center !important;
        gap: 6px !important;
        flex-wrap: wrap !important;
      }
      .pm-match-form {
        display: inline-flex !important;
        align-items: center !important;
        gap: 4px !important;
        background: #0d131f !important;
        border: 1px solid #2a3b5c !important;
        padding: 2px 4px !important;
        border-radius: 6px !important;
      }
      .pm-match-input {
        background: transparent !important;
        border: none !important;
        color: #f8fafc !important;
        font-size: 11px !important;
        padding: 3px 5px !important;
        outline: none !important;
        width: 105px !important;
        font-weight: 600 !important;
      }
      .pm-match-input::placeholder {
        color: #64748b !important;
        font-weight: normal !important;
      }

      .pm-search-row {
        display: flex !important;
        align-items: center !important;
        gap: 6px !important;
        flex-wrap: wrap !important;
        width: 100% !important;
      }
      .pm-search-box {
        position: relative !important;
        flex: 1 !important;
        min-width: 160px !important;
      }
      .pm-search-box i {
        position: absolute !important;
        left: 8px !important;
        top: 50% !important;
        transform: translateY(-50%) !important;
        color: #64748b !important;
        font-size: 13px !important;
      }
      .pm-search-input {
        width: 100% !important;
        background: #0d131f !important;
        border: 1px solid #1f2d45 !important;
        border-radius: 6px !important;
        padding: 5px 8px 5px 26px !important;
        color: #f8fafc !important;
        font-size: 11px !important;
        outline: none !important;
      }
      .pm-search-input:focus {
        border-color: #3b82f6 !important;
      }
      .pm-method-select {
        background: #0d131f !important;
        border: 1px solid #1f2d45 !important;
        border-radius: 6px !important;
        padding: 5px 8px !important;
        color: #f8fafc !important;
        font-size: 11px !important;
        outline: none !important;
      }

      /* Alert */
      .pm-alert-ok {
        background: rgba(16, 185, 129, 0.15) !important;
        border: 1px solid rgba(16, 185, 129, 0.4) !important;
        color: #34d399 !important;
        padding: 8px 12px !important;
        border-radius: 6px !important;
        font-size: 12px !important;
        display: flex !important;
        align-items: center !important;
        gap: 6px !important;
      }
      .pm-alert-err {
        background: rgba(239, 68, 68, 0.15) !important;
        border: 1px solid rgba(239, 68, 68, 0.4) !important;
        color: #f87171 !important;
        padding: 8px 12px !important;
        border-radius: 6px !important;
        font-size: 12px !important;
        display: flex !important;
        align-items: center !important;
        gap: 6px !important;
      }

      /* Cards List */
      .pm-cards-list {
        display: flex !important;
        flex-direction: column !important;
        gap: 8px !important;
        width: 100% !important;
      }
      .pm-card {
        display: flex !important;
        flex-direction: column !important;
        grid-template-columns: none !important;
        width: 100% !important;
        background: #141c2b !important;
        border: 1px solid #1f2d45 !important;
        border-radius: 10px !important;
        overflow: hidden !important;
        transition: border-color .15s ease !important;
      }
      .pm-card:hover {
        border-color: #2b3e61 !important;
      }
      .pm-card.status-pending {
        border-left: 4px solid #f59e0b !important;
      }
      .pm-card.status-paid {
        border-left: 4px solid #10b981 !important;
      }
      .pm-card.status-canceled {
        border-left: 4px solid #64748b !important;
      }

      /* Perfectly Responsive Card Header */
      .pm-card-header {
        padding: 10px 12px !important;
        cursor: pointer !important;
        user-select: none !important;
        background: rgba(255, 255, 255, 0.015) !important;
        display: flex !important;
        flex-direction: column !important;
        gap: 6px !important;
        width: 100% !important;
      }
      .pm-card-header:hover {
        background: rgba(255, 255, 255, 0.035) !important;
      }

      .pm-hdr-top {
        display: flex !important;
        align-items: center !important;
        justify-content: space-between !important;
        width: 100% !important;
        gap: 8px !important;
      }
      .pm-hdr-badges {
        display: flex !important;
        align-items: center !important;
        gap: 6px !important;
        flex-wrap: wrap !important;
        min-width: 0 !important;
      }
      .pm-id-badge {
        font-family: monospace !important;
        font-weight: 700 !important;
        font-size: 11px !important;
        padding: 2px 5px !important;
        background: #1e293b !important;
        color: #cbd5e1 !important;
        border-radius: 4px !important;
        border: 1px solid #334155 !important;
        white-space: nowrap !important;
      }
      .pm-status-pill {
        display: inline-flex !important;
        align-items: center !important;
        gap: 3px !important;
        font-size: 10px !important;
        font-weight: 600 !important;
        padding: 2px 6px !important;
        border-radius: 999px !important;
        white-space: nowrap !important;
      }
      .pm-st-pending {
        background: rgba(245, 158, 11, 0.15) !important;
        color: #f59e0b !important;
        border: 1px solid rgba(245, 158, 11, 0.35) !important;
      }
      .pm-st-paid {
        background: rgba(16, 185, 129, 0.15) !important;
        color: #10b981 !important;
        border: 1px solid rgba(16, 185, 129, 0.35) !important;
      }
      .pm-st-canceled {
        background: rgba(148, 163, 184, 0.15) !important;
        color: #94a3b8 !important;
        border: 1px solid rgba(148, 163, 184, 0.35) !important;
      }

      .pm-amt-box {
        display: inline-flex !important;
        align-items: baseline !important;
        gap: 2px !important;
        white-space: nowrap !important;
        margin-left: 2px !important;
      }
      .pm-amt-num {
        font-size: 15px !important;
        font-weight: 800 !important;
        color: #10b981 !important;
      }
      .pm-card.status-pending .pm-amt-num {
        color: #fbbf24 !important;
      }
      .pm-card.status-canceled .pm-amt-num {
        color: #94a3b8 !important;
      }
      .pm-amt-unit {
        font-size: 10px !important;
        color: #64748b !important;
      }

      .pm-toggle-btn {
        background: #1e293b !important;
        border: 1px solid #334155 !important;
        color: #cbd5e1 !important;
        width: 24px !important;
        height: 24px !important;
        border-radius: 5px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        font-size: 12px !important;
        transition: transform .18s ease !important;
        flex-shrink: 0 !important;
      }
      .pm-card.is-open .pm-toggle-btn {
        transform: rotate(180deg) !important;
        background: #3b82f6 !important;
        color: #fff !important;
      }

      .pm-hdr-sub {
        display: flex !important;
        align-items: center !important;
        gap: 6px 10px !important;
        flex-wrap: wrap !important;
        font-size: 11px !important;
        color: #94a3b8 !important;
        width: 100% !important;
      }
      .pm-client-tag {
        display: inline-flex !important;
        align-items: center !important;
        gap: 3px !important;
        font-size: 11px !important;
        color: #f1f5f9 !important;
        white-space: nowrap !important;
      }
      .pm-client-tag a {
        color: #60a5fa !important;
        text-decoration: none !important;
        font-weight: 600 !important;
      }
      .pm-bal-tag {
        font-size: 10px !important;
        background: #0f172a !important;
        border: 1px solid #1e293b !important;
        color: #94a3b8 !important;
        padding: 1px 4px !important;
        border-radius: 4px !important;
        white-space: nowrap !important;
      }
      .pm-ref-tag {
        font-family: monospace !important;
        font-size: 10px !important;
        color: #93c5fd !important;
        background: #0d131f !important;
        padding: 1px 4px !important;
        border-radius: 4px !important;
        border: 1px solid #1e293b !important;
        white-space: nowrap !important;
      }
      .pm-meta-txt {
        font-size: 10px !important;
        color: #94a3b8 !important;
        display: inline-flex !important;
        align-items: center !important;
        gap: 2px !important;
        white-space: nowrap !important;
      }
      .pm-slip-badge {
        font-size: 10px !important;
        padding: 1px 5px !important;
        border-radius: 4px !important;
        display: inline-flex !important;
        align-items: center !important;
        gap: 2px !important;
        white-space: nowrap !important;
      }
      .pm-slip-has {
        background: rgba(16, 185, 129, 0.15) !important;
        color: #34d399 !important;
        border: 1px solid rgba(16, 185, 129, 0.3) !important;
      }
      .pm-slip-digi {
        background: rgba(59, 130, 246, 0.15) !important;
        color: #60a5fa !important;
        border: 1px solid rgba(59, 130, 246, 0.3) !important;
      }
      .pm-slip-empty {
        background: rgba(148, 163, 184, 0.1) !important;
        color: #94a3b8 !important;
      }

      /* Card Drawer */
      .pm-drawer {
        display: none !important;
        border-top: 1px solid #1f2d45 !important;
        padding: 12px !important;
        background: #0d131f !important;
        width: 100% !important;
      }
      .pm-card.is-open .pm-drawer {
        display: block !important;
      }
      .pm-drawer-grid {
        display: grid !important;
        grid-template-columns: 1fr 1fr 1fr !important;
        gap: 12px !important;
        width: 100% !important;
      }
      @media (max-width: 860px) {
        .pm-drawer-grid {
          grid-template-columns: 1fr !important;
          gap: 10px !important;
        }
      }

      .pm-box {
        background: #141c2b !important;
        border: 1px solid #1f2d45 !important;
        border-radius: 8px !important;
        padding: 10px !important;
        display: flex !important;
        flex-direction: column !important;
        gap: 8px !important;
        width: 100% !important;
        min-width: 0 !important;
      }
      .pm-box-title {
        font-size: 11px !important;
        font-weight: 700 !important;
        color: #f1f5f9 !important;
        display: flex !important;
        align-items: center !important;
        gap: 5px !important;
        border-bottom: 1px solid #1f2d45 !important;
        padding-bottom: 5px !important;
      }
      .pm-box-title i {
        color: #3b82f6 !important;
      }

      .pm-kv-list {
        display: flex !important;
        flex-direction: column !important;
        gap: 5px !important;
        font-size: 11px !important;
        width: 100% !important;
      }
      .pm-kv-row {
        display: flex !important;
        align-items: center !important;
        justify-content: space-between !important;
        gap: 6px !important;
        width: 100% !important;
      }
      .pm-kv-lbl {
        color: #94a3b8 !important;
        white-space: nowrap !important;
        flex-shrink: 0 !important;
      }
      .pm-kv-val {
        color: #f8fafc !important;
        font-weight: 500 !important;
        text-align: right !important;
        word-break: break-all !important;
        min-width: 0 !important;
      }
      .pm-kv-val code {
        font-family: monospace !important;
        background: #0d131f !important;
        padding: 1px 4px !important;
        border-radius: 4px !important;
        border: 1px solid #1e293b !important;
        color: #60a5fa !important;
      }

      /* Slip Photo Box */
      .pm-slip-photo-wrap {
        position: relative !important;
        background: #090d15 !important;
        border: 1px solid #1f2d45 !important;
        border-radius: 6px !important;
        overflow: hidden !important;
        cursor: pointer !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        min-height: 160px !important;
        max-height: 280px !important;
      }
      .pm-slip-thumb {
        max-width: 100% !important;
        max-height: 280px !important;
        object-fit: contain !important;
        display: block !important;
        transition: transform .2s ease !important;
      }
      .pm-slip-photo-wrap:hover .pm-slip-thumb {
        transform: scale(1.02) !important;
      }
      .pm-slip-zoom-hint {
        position: absolute !important;
        bottom: 6px !important;
        right: 6px !important;
        background: rgba(15, 23, 42, 0.85) !important;
        color: #fff !important;
        padding: 2px 6px !important;
        border-radius: 4px !important;
        font-size: 10px !important;
        display: flex !important;
        align-items: center !important;
        gap: 3px !important;
      }
      .pm-slip-actions {
        display: flex !important;
        gap: 5px !important;
        margin-top: 2px !important;
      }

      /* Thai Digital E-Slip Card */
      .pm-eslip-card {
        background: linear-gradient(180deg, #0e1e38 0%, #0a1324 100%) !important;
        border: 1px solid #23385d !important;
        border-radius: 8px !important;
        padding: 10px !important;
        display: flex !important;
        flex-direction: column !important;
        gap: 6px !important;
        position: relative !important;
        overflow: hidden !important;
        box-shadow: 0 4px 10px rgba(0,0,0,0.3) !important;
      }
      .pm-eslip-card::before {
        content: '' !important;
        position: absolute !important;
        top: 0 !important;
        left: 0 !important;
        right: 0 !important;
        height: 3px !important;
        background: linear-gradient(90deg, #0056b3, #00a86b) !important;
      }
      .pm-eslip-header {
        display: flex !important;
        align-items: center !important;
        justify-content: space-between !important;
        border-bottom: 1px dashed #23385d !important;
        padding-bottom: 5px !important;
      }
      .pm-promptpay-tag {
        font-size: 10px !important;
        font-weight: 700 !important;
        color: #38bdf8 !important;
        display: flex !important;
        align-items: center !important;
        gap: 3px !important;
      }
      .pm-eslip-status-tag {
        font-size: 9px !important;
        padding: 1px 5px !important;
        border-radius: 999px !important;
        font-weight: 600 !important;
        display: flex !important;
        align-items: center !important;
        gap: 2px !important;
      }
      .pm-eslip-status-tag.tag-paid {
        background: rgba(16, 185, 129, 0.2) !important;
        color: #34d399 !important;
        border: 1px solid rgba(16, 185, 129, 0.4) !important;
      }
      .pm-eslip-status-tag.tag-pending {
        background: rgba(245, 158, 11, 0.2) !important;
        color: #fbbf24 !important;
        border: 1px solid rgba(245, 158, 11, 0.4) !important;
      }

      .pm-eslip-amt-box {
        text-align: center !important;
        padding: 5px 0 !important;
        background: rgba(15, 23, 42, 0.5) !important;
        border-radius: 6px !important;
        border: 1px solid #1e293b !important;
      }
      .pm-eslip-amt-lbl {
        display: block !important;
        font-size: 9px !important;
        color: #94a3b8 !important;
      }
      .pm-eslip-amt-val {
        font-size: 18px !important;
        font-weight: 800 !important;
        color: #34d399 !important;
      }

      .pm-eslip-row {
        display: flex !important;
        justify-content: space-between !important;
        align-items: center !important;
        font-size: 10px !important;
        gap: 4px !important;
      }
      .pm-eslip-lbl {
        color: #94a3b8 !important;
        display: flex !important;
        align-items: center !important;
        gap: 3px !important;
        white-space: nowrap !important;
      }
      .pm-eslip-val {
        color: #f8fafc !important;
        text-align: right !important;
        white-space: nowrap !important;
      }
      .pm-eslip-code {
        font-family: monospace !important;
        font-size: 10px !important;
        background: #090e18 !important;
        padding: 1px 3px !important;
        border-radius: 3px !important;
        border: 1px solid #1e293b !important;
        color: #93c5fd !important;
      }

      /* Admin Upload Tool */
      .pm-upload-box {
        margin-top: 2px !important;
        background: #0a0f19 !important;
        border: 1px dashed #2a3b5c !important;
        border-radius: 6px !important;
        padding: 6px !important;
        display: flex !important;
        flex-direction: column !important;
        gap: 4px !important;
      }
      .pm-upload-lbl {
        font-size: 10px !important;
        color: #94a3b8 !important;
        display: flex !important;
        align-items: center !important;
        gap: 3px !important;
      }
      .pm-upload-inputs {
        display: flex !important;
        gap: 4px !important;
        align-items: center !important;
      }
      .pm-upload-file {
        flex: 1 !important;
        font-size: 10px !important;
        color: #94a3b8 !important;
      }

      /* Action Buttons */
      .pm-act-group {
        display: flex !important;
        flex-direction: column !important;
        gap: 6px !important;
      }
      .pm-act-btn {
        width: 100% !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        gap: 4px !important;
        padding: 7px 10px !important;
        border-radius: 6px !important;
        font-weight: 600 !important;
        font-size: 11px !important;
        cursor: pointer !important;
        transition: all .15s ease !important;
        border: none !important;
      }
      .pm-btn-approve {
        background: #059669 !important;
        color: #fff !important;
        border: 1px solid #10b981 !important;
      }
      .pm-btn-approve:hover {
        background: #10b981 !important;
      }
      .pm-btn-reject {
        background: #dc2626 !important;
        color: #fff !important;
        border: 1px solid #ef4444 !important;
      }
      .pm-btn-reject:hover {
        background: #ef4444 !important;
      }
      .pm-reject-box {
        display: flex !important;
        flex-direction: column !important;
        gap: 4px !important;
        background: #0d131f !important;
        padding: 6px !important;
        border-radius: 6px !important;
        border: 1px solid #3b2020 !important;
      }
      .pm-reject-input {
        background: #141c2b !important;
        border: 1px solid #4a2828 !important;
        border-radius: 4px !important;
        padding: 4px 6px !important;
        color: #f8fafc !important;
        font-size: 11px !important;
        outline: none !important;
      }
      .pm-note-form {
        display: flex !important;
        gap: 4px !important;
      }
      .pm-note-input {
        flex: 1 !important;
        background: #0d131f !important;
        border: 1px solid #1f2d45 !important;
        border-radius: 4px !important;
        padding: 4px 6px !important;
        color: #f8fafc !important;
        font-size: 11px !important;
        outline: none !important;
      }

      /* Modal */
      .pm-modal {
        display: none;
        position: fixed;
        inset: 0;
        z-index: 999999;
        background: rgba(0, 0, 0, 0.85);
        backdrop-filter: blur(4px);
        align-items: center;
        justify-content: center;
        padding: 1rem;
      }
      .pm-modal.is-active {
        display: flex !important;
      }
      .pm-modal-content {
        max-width: 800px;
        width: 100%;
        max-height: 90vh;
        background: #141c2b;
        border: 1px solid #1f2d45;
        border-radius: 10px;
        overflow: hidden;
        display: flex;
        flex-direction: column;
        box-shadow: 0 20px 40px rgba(0,0,0,0.6);
      }
      .pm-modal-bar {
        padding: 8px 12px;
        background: #0d131f;
        border-bottom: 1px solid #1f2d45;
        display: flex;
        align-items: center;
        justify-content: space-between;
      }
      .pm-modal-title {
        font-size: 12px;
        font-weight: 700;
        color: #f8fafc;
      }
      .pm-modal-actions {
        display: flex;
        align-items: center;
        gap: 5px;
      }
      .pm-modal-close {
        background: #1e293b;
        border: 1px solid #334155;
        color: #f8fafc;
        width: 26px;
        height: 26px;
        border-radius: 5px;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 14px;
      }
      .pm-modal-close:hover {
        background: #ef4444;
      }
      .pm-modal-body {
        padding: 10px;
        overflow: auto;
        display: flex;
        align-items: center;
        justify-content: center;
        background: #090d15;
      }
      .pm-modal-body img {
        max-width: 100%;
        max-height: 75vh;
        object-fit: contain;
        border-radius: 5px;
      }
    </style>

    <div class="pm-desk-wrap">
      <!-- Flash Alert -->
      <?php if ($okMsg !== ''): ?>
        <div class="pm-alert-ok">
          <i class="ri-checkbox-circle-fill"></i>
          <span><?= $okMsg ?></span>
        </div>
      <?php endif; ?>
      <?php if ($errMsg !== ''): ?>
        <div class="pm-alert-err">
          <i class="ri-error-warning-fill"></i>
          <span><?= $errMsg ?></span>
        </div>
      <?php endif; ?>

      <!-- 4 KPI Summary Cards (Clean 4 cols on desktop, 2x2 on mobile) -->
      <div class="pm-kpi-grid">
        <a class="pm-kpi-card <?= $statusFilter === '' ? 'is-active' : '' ?>" href="/admin/payments">
          <div class="pm-kpi-info">
            <span class="pm-kpi-title">รายการทั้งหมด</span>
            <b class="pm-kpi-val"><?= number_format($counts['all']) ?></b>
            <small class="pm-kpi-sub">ยอดรวม ฿<?= number_format($sums['all'], 2) ?></small>
          </div>
          <div class="pm-kpi-icon"><i class="ri-wallet-3-line"></i></div>
        </a>

        <a class="pm-kpi-card kpi-pending <?= $statusFilter === 'pending' ? 'is-active' : '' ?> <?= $counts['pending'] > 0 ? 'is-pending-alert' : '' ?>" href="/admin/payments?status=pending">
          <div class="pm-kpi-info">
            <span class="pm-kpi-title">รอตรวจสอบยอด</span>
            <b class="pm-kpi-val"><?= number_format($counts['pending']) ?></b>
            <small class="pm-kpi-sub">รอยืนยัน ฿<?= number_format($sums['pending'], 2) ?></small>
          </div>
          <div class="pm-kpi-icon"><i class="ri-time-line"></i></div>
        </a>

        <a class="pm-kpi-card kpi-paid <?= $statusFilter === 'paid' ? 'is-active' : '' ?>" href="/admin/payments?status=paid">
          <div class="pm-kpi-info">
            <span class="pm-kpi-title">อนุมัติสำเร็จแล้ว</span>
            <b class="pm-kpi-val"><?= number_format($counts['paid']) ?></b>
            <small class="pm-kpi-sub">สำเร็จ ฿<?= number_format($sums['paid'], 2) ?></small>
          </div>
          <div class="pm-kpi-icon"><i class="ri-checkbox-circle-line"></i></div>
        </a>

        <a class="pm-kpi-card kpi-canceled <?= $statusFilter === 'canceled' ? 'is-active' : '' ?>" href="/admin/payments?status=canceled">
          <div class="pm-kpi-info">
            <span class="pm-kpi-title">ปฏิเสธ / ยกเลิก</span>
            <b class="pm-kpi-val"><?= number_format($counts['canceled']) ?></b>
            <small class="pm-kpi-sub">ยกเลิก ฿<?= number_format($sums['canceled'], 2) ?></small>
          </div>
          <div class="pm-kpi-icon"><i class="ri-close-circle-line"></i></div>
        </a>
      </div>

      <!-- Quick Toolbar & Matcher -->
      <div class="pm-toolbar">
        <div class="pm-toolbar-top">
          <!-- Status Tabs -->
          <div class="pm-tabs">
            <a href="/admin/payments" class="pm-tab-btn <?= $statusFilter === '' ? 'is-active' : '' ?>">
              ทั้งหมด <span class="pm-tab-badge"><?= $counts['all'] ?></span>
            </a>
            <a href="/admin/payments?status=pending" class="pm-tab-btn <?= $statusFilter === 'pending' ? 'is-active' : '' ?>">
              รอตรวจ <span class="pm-tab-badge"><?= $counts['pending'] ?></span>
            </a>
            <a href="/admin/payments?status=paid" class="pm-tab-btn <?= $statusFilter === 'paid' ? 'is-active' : '' ?>">
              อนุมัติแล้ว <span class="pm-tab-badge"><?= $counts['paid'] ?></span>
            </a>
            <a href="/admin/payments?status=canceled" class="pm-tab-btn <?= $statusFilter === 'canceled' ? 'is-active' : '' ?>">
              ปฏิเสธ <span class="pm-tab-badge"><?= $counts['canceled'] ?></span>
            </a>
          </div>

          <!-- Quick Actions -->
          <div class="pm-quick-actions">
            <form class="pm-match-form" method="post" action="/admin/payments/match">
              <input type="hidden" name="next" value="<?= htmlspecialchars($statusFilter) ?>">
              <i class="ri-focus-3-line" style="color:#60a5fa; margin-left:2px;"></i>
              <input class="pm-match-input" name="amount" inputmode="decimal" placeholder="จับคู่ยอด เช่น 14.16" required>
              <button type="submit" class="la-btn la-btn-mini la-btn-primary" style="padding:3px 7px; font-size:11px;"><i class="ri-link"></i> จับคู่ & อนุมัติ</button>
            </form>
            <a href="/admin/settings/payments" class="la-btn la-btn-mini la-btn-ghost" style="padding:3px 7px; font-size:11px;"><i class="ri-settings-3-line"></i> ตั้งค่า</a>
            <a href="/addfunds" target="_blank" class="la-btn la-btn-mini la-btn-ghost" style="padding:3px 7px; font-size:11px;"><i class="ri-external-link-line"></i> หน้าลูกค้า</a>
          </div>
        </div>

        <!-- Live Search Bar -->
        <div class="pm-search-row">
          <div class="pm-search-box">
            <i class="ri-search-line"></i>
            <input type="text" id="pmLiveSearch" class="pm-search-input" placeholder="ค้นหาด่วน: #ID, ลูกค้า, ยอดเงิน, รหัสอ้างอิง..." value="<?= htmlspecialchars($searchQuery) ?>" oninput="onPmLiveSearch(this.value)">
          </div>
          <?php if (!empty($methodsList)): ?>
            <select class="pm-method-select" onchange="onPmMethodFilter(this.value)">
              <option value="">ทุกช่องทาง (<?= count($methodsList) ?>)</option>
              <?php foreach ($methodsList as $mItem): ?>
                <option value="<?= htmlspecialchars($mItem) ?>" <?= $methodFilter === $mItem ? 'selected' : '' ?>><?= htmlspecialchars($mItem) ?></option>
              <?php endforeach; ?>
            </select>
          <?php endif; ?>
        </div>
      </div>

      <!-- Payment Cards Accordion List -->
      <div class="pm-cards-list" id="pmCardsContainer">
        <?php if (empty($payments)): ?>
          <div style="background:#141c2b; border:1px solid #1f2d45; border-radius:10px; padding:2.5rem 1.5rem; text-align:center; color:#94a3b8;">
            <i class="ri-inbox-line" style="font-size:2.2rem; color:#475569; display:block; margin-bottom:0.5rem;"></i>
            <h3 style="color:#f8fafc; font-size:1rem; margin-bottom:0.2rem;">ไม่พบรายการเติมเงิน</h3>
            <p style="font-size:0.8rem;">ยังไม่มีรายการที่ตรงกับเงื่อนไขการค้นหาหรือตัวกรองในขณะนี้</p>
          </div>
        <?php endif; ?>

        <?php foreach ($payments as $p): ?>
          <?php
            $pid = (int)$p['id'];
            $st = $p['status'] ?: 'pending';
            $amt = floatval($p['amount'] ?? 0);
            $cl = trim((string)($p['client'] ?? ''));
            $cData = $clientsMap[$cl] ?? [];
            $cBal = isset($cData['balance']) ? floatval($cData['balance']) : null;
            $cEmail = trim((string)($cData['email'] ?? ''));
            $m = trim((string)($p['method'] ?? 'PromptPay'));
            $slip = trim((string)($p['slip'] ?? ''));
            $transRef = trim((string)($p['trans_ref'] ?? ''));
            $refCode = trim((string)($p['ref_code'] ?? ''));
            $note = trim((string)($p['note'] ?? ''));
            $createdAt = trim((string)($p['created_at'] ?? ''));

            // Check physical file existence
            $hasPhysicalSlip = false;
            $docRoot = $_SERVER['DOCUMENT_ROOT'] ?? '';
            if ($slip !== '') {
                $cleanPath = ltrim($slip, '/');
                if ($docRoot !== '' && is_file($docRoot . '/' . $cleanPath)) {
                    $hasPhysicalSlip = true;
                } elseif (is_file(__DIR__ . '/' . $cleanPath)) {
                    $hasPhysicalSlip = true;
                } elseif (is_file(__DIR__ . '/../' . $cleanPath)) {
                    $hasPhysicalSlip = true;
                } elseif (is_file(dirname(__DIR__, 2) . '/' . $cleanPath)) {
                    $hasPhysicalSlip = true;
                }
            }
            // Auto-discover slip file by PID if exact path not matched
            if (!$hasPhysicalSlip && $pid > 0) {
                $searchDirs = [
                    ($docRoot !== '' ? $docRoot : __DIR__) . '/static/uploads/slips',
                    __DIR__ . '/static/uploads/slips',
                    __DIR__ . '/../static/uploads/slips',
                    dirname(__DIR__, 2) . '/py-app/static/uploads/slips',
                ];
                foreach ($searchDirs as $sDir) {
                    if (is_dir($sDir)) {
                        $matches = glob($sDir . '/p' . $pid . '_*.*');
                        if (empty($matches)) {
                            $matches = glob($sDir . '/p' . $pid . '.*');
                        }
                        if (!empty($matches)) {
                            $hasPhysicalSlip = true;
                            $slip = '/static/uploads/slips/' . basename($matches[0]);
                            break;
                        }
                    }
                }
            }
          ?>
          <article class="pm-card status-<?= $st ?> <?= $st === 'pending' ? 'is-open' : '' ?>"
                   id="pmCard-<?= $pid ?>"
                   data-pid="<?= $pid ?>"
                   data-status="<?= $st ?>"
                   data-client="<?= htmlspecialchars(mb_strtolower($cl)) ?>"
                   data-method="<?= htmlspecialchars(mb_strtolower($m)) ?>"
                   data-search="<?= htmlspecialchars(mb_strtolower($pid . ' ' . $cl . ' ' . $amt . ' ' . $m . ' ' . $refCode . ' ' . $transRef . ' ' . $note)) ?>">

            <!-- Card Header: Row 1 = Badges + Amount + Toggle Button; Row 2 = Metadata -->
            <div class="pm-card-header" onclick="togglePmDrawer(<?= $pid ?>)">
              <div class="pm-hdr-top">
                <div class="pm-hdr-badges">
                  <span class="pm-id-badge">#<?= $pid ?></span>
                  <?php if ($st === 'pending'): ?>
                    <span class="pm-status-pill pm-st-pending"><i class="ri-time-line"></i> รอตรวจ</span>
                  <?php elseif ($st === 'paid'): ?>
                    <span class="pm-status-pill pm-st-paid"><i class="ri-checkbox-circle-fill"></i> อนุมัติแล้ว</span>
                  <?php else: ?>
                    <span class="pm-status-pill pm-st-canceled"><i class="ri-close-circle-fill"></i> ปฏิเสธ</span>
                  <?php endif; ?>
                  <div class="pm-amt-box">
                    <span class="pm-amt-num">฿<?= number_format($amt, 2) ?></span>
                    <span class="pm-amt-unit">บาท</span>
                  </div>
                </div>
                <div class="pm-toggle-btn" aria-label="ดูรายละเอียด">
                  <i class="ri-arrow-down-s-line"></i>
                </div>
              </div>

              <div class="pm-hdr-sub">
                <div class="pm-client-tag">
                  <i class="ri-user-3-line" style="color:#64748b;"></i>
                  <a href="/admin/clients?q=<?= urlencode($cl) ?>" onclick="event.stopPropagation()"><b><?= htmlspecialchars($cl) ?></b></a>
                  <?php if ($cBal !== null): ?>
                    <span class="pm-bal-tag">คงเหลือ ฿<?= number_format($cBal, 2) ?></span>
                  <?php endif; ?>
                </div>

                <?php if ($refCode !== ''): ?>
                  <span class="pm-ref-tag"><?= htmlspecialchars($refCode) ?></span>
                <?php endif; ?>

                <span class="pm-meta-txt"><i class="ri-qr-code-line"></i> <?= htmlspecialchars($m) ?></span>
                <span class="pm-meta-txt"><i class="ri-time-line"></i> <?= htmlspecialchars($createdAt) ?></span>

                <?php if ($hasPhysicalSlip): ?>
                  <span class="pm-slip-badge pm-slip-has"><i class="ri-image-line"></i> มีสลิป</span>
                <?php elseif ($transRef !== ''): ?>
                  <span class="pm-slip-badge pm-slip-digi"><i class="ri-file-shield-line"></i> สลิปดิจิทัล</span>
                <?php else: ?>
                  <span class="pm-slip-badge pm-slip-empty"><i class="ri-attachment-line"></i> รอสลิป</span>
                <?php endif; ?>
              </div>
            </div>

            <!-- Card Drawer -->
            <div class="pm-drawer">
              <div class="pm-drawer-grid">

                <!-- Box 1: Payment Info -->
                <div class="pm-box">
                  <div class="pm-box-title">
                    <i class="ri-file-list-3-line"></i>
                    <span>ข้อมูลการเติมเงิน (#<?= $pid ?>)</span>
                  </div>
                  <div class="pm-kv-list">
                    <div class="pm-kv-row">
                      <span class="pm-kv-lbl">รหัสรายการ:</span>
                      <span class="pm-kv-val">#<?= $pid ?></span>
                    </div>
                    <div class="pm-kv-row">
                      <span class="pm-kv-lbl">ชื่อลูกค้า:</span>
                      <span class="pm-kv-val">
                        <a href="/admin/clients?q=<?= urlencode($cl) ?>" style="color:#60a5fa; text-decoration:none;"><b><?= htmlspecialchars($cl) ?></b></a>
                        <?php if ($cEmail !== ''): ?>
                          <div style="font-size:10px; color:#64748b;"><?= htmlspecialchars($cEmail) ?></div>
                        <?php endif; ?>
                      </span>
                    </div>
                    <div class="pm-kv-row">
                      <span class="pm-kv-lbl">ยอดกระเป๋าปัจจุบัน:</span>
                      <span class="pm-kv-val" style="color:#34d399; font-weight:700;">฿<?= $cBal !== null ? number_format($cBal, 2) : '-' ?></span>
                    </div>
                    <div class="pm-kv-row">
                      <span class="pm-kv-lbl">ยอดที่ต้องโอน:</span>
                      <span class="pm-kv-val" style="color:#fbbf24; font-size:13px; font-weight:800;">฿<?= number_format($amt, 2) ?></span>
                    </div>
                    <div class="pm-kv-row">
                      <span class="pm-kv-lbl">ช่องทางชำระเงิน:</span>
                      <span class="pm-kv-val"><?= htmlspecialchars($m) ?></span>
                    </div>
                    <div class="pm-kv-row">
                      <span class="pm-kv-lbl">รหัสอ้างอิง (Ref):</span>
                      <span class="pm-kv-val"><code><?= htmlspecialchars($refCode ?: '-') ?></code></span>
                    </div>
                    <?php if ($transRef !== ''): ?>
                      <div class="pm-kv-row">
                        <span class="pm-kv-lbl">Bank Trans Ref:</span>
                        <span class="pm-kv-val"><code style="color:#fbbf24; border-color:#78350f;"><?= htmlspecialchars($transRef) ?></code></span>
                      </div>
                    <?php endif; ?>
                    <div class="pm-kv-row">
                      <span class="pm-kv-lbl">วันที่/เวลา:</span>
                      <span class="pm-kv-val"><?= htmlspecialchars($createdAt) ?></span>
                    </div>
                    <div class="pm-kv-row">
                      <span class="pm-kv-lbl">สถานะ:</span>
                      <span class="pm-kv-val">
                        <?php if ($st === 'pending'): ?>
                          <span style="color:#fbbf24; font-weight:700;">รอตรวจสอบยอด</span>
                        <?php elseif ($st === 'paid'): ?>
                          <span style="color:#34d399; font-weight:700;">อนุมัติเข้ากระเป๋าแล้ว</span>
                        <?php else: ?>
                          <span style="color:#94a3b8; font-weight:700;">ปฏิเสธรายการ</span>
                        <?php endif; ?>
                      </span>
                    </div>
                    <?php if ($note !== ''): ?>
                      <div class="pm-kv-row" style="align-items:flex-start; margin-top:3px; padding-top:3px; border-top:1px dashed #1f2d45;">
                        <span class="pm-kv-lbl">บันทึก:</span>
                        <span class="pm-kv-val" style="color:#cbd5e1;"><?= nl2br(htmlspecialchars($note)) ?></span>
                      </div>
                    <?php endif; ?>
                  </div>
                </div>

                <!-- Box 2: Payment Slip Inspector -->
                <div class="pm-box">
                  <div class="pm-box-title">
                    <i class="ri-shield-check-line"></i>
                    <span>หลักฐานสลิปโอนเงิน</span>
                  </div>

                  <?php if ($hasPhysicalSlip): ?>
                    <!-- Real Attached Slip Image -->
                    <div class="pm-slip-photo-wrap" onclick="openPmLighbox('<?= htmlspecialchars($slip) ?>', <?= $pid ?>, '<?= htmlspecialchars($cl) ?>', '<?= number_format($amt,2) ?>')">
                      <img src="<?= htmlspecialchars($slip) ?>" alt="สลิปโอนเงิน #<?= $pid ?>" class="pm-slip-thumb" loading="lazy">
                      <div class="pm-slip-zoom-hint"><i class="ri-zoom-in-line"></i> คลิกซูมดูรูปใหญ่</div>
                    </div>
                    <div class="pm-slip-actions">
                      <a href="<?= htmlspecialchars($slip) ?>" target="_blank" class="la-btn la-btn-mini la-btn-ghost" style="padding:3px 7px; font-size:11px;"><i class="ri-external-link-line"></i> เปิดภาพเต็ม</a>
                      <a href="<?= htmlspecialchars($slip) ?>" download="slip-<?= $pid ?>.jpg" class="la-btn la-btn-mini la-btn-ghost" style="padding:3px 7px; font-size:11px;"><i class="ri-download-2-line"></i> ดาวน์โหลด</a>
                    </div>
                  <?php else: ?>
                    <!-- Thai PromptPay Digital E-Slip Card -->
                    <div class="pm-eslip-card">
                      <div class="pm-eslip-header">
                        <span class="pm-promptpay-tag"><i class="ri-qr-code-line"></i> PromptPay</span>
                        <span class="pm-eslip-status-tag <?= $st === 'paid' ? 'tag-paid' : 'tag-pending' ?>">
                          <i class="<?= $st === 'paid' ? 'ri-checkbox-circle-fill' : 'ri-time-line' ?>"></i>
                          <?= $st === 'paid' ? 'ชำระเงินสำเร็จ' : 'รอตรวจสอบยอด' ?>
                        </span>
                      </div>
                      <div class="pm-eslip-amt-box">
                        <span class="pm-eslip-amt-lbl">จำนวนเงินที่โอน</span>
                        <span class="pm-eslip-amt-val">฿<?= number_format($amt, 2) ?></span>
                      </div>
                      <div class="pm-eslip-row">
                        <span class="pm-eslip-lbl"><i class="ri-user-line"></i> ลูกค้า:</span>
                        <span class="pm-eslip-val"><b><?= htmlspecialchars($cl) ?></b></span>
                      </div>
                      <div class="pm-eslip-row">
                        <span class="pm-eslip-lbl"><i class="ri-bank-card-line"></i> ช่องทาง:</span>
                        <span class="pm-eslip-val"><?= htmlspecialchars($m ?: 'PromptPay') ?></span>
                      </div>
                      <div class="pm-eslip-row">
                        <span class="pm-eslip-lbl"><i class="ri-hashtag"></i> รหัสอ้างอิง:</span>
                        <span class="pm-eslip-val"><code class="pm-eslip-code"><?= htmlspecialchars($refCode ?: 'LA' . $pid) ?></code></span>
                      </div>
                      <?php if ($transRef !== ''): ?>
                        <div class="pm-eslip-row">
                          <span class="pm-eslip-lbl"><i class="ri-barcode-line"></i> Bank Trans Ref:</span>
                          <span class="pm-eslip-val"><code class="pm-eslip-code" style="color:#fbbf24; border-color:#78350f;"><?= htmlspecialchars($transRef) ?></code></span>
                        </div>
                      <?php endif; ?>
                      <div class="pm-eslip-row">
                        <span class="pm-eslip-lbl"><i class="ri-time-line"></i> เวลาทำรายการ:</span>
                        <span class="pm-eslip-val"><?= htmlspecialchars($createdAt) ?></span>
                      </div>
                    </div>
                  <?php endif; ?>

                  <!-- Admin Attach/Replace Slip Upload Form -->
                  <form class="pm-upload-box" method="post" action="/admin/payments/<?= $pid ?>/upload-slip" enctype="multipart/form-data">
                    <input type="hidden" name="next" value="<?= htmlspecialchars($statusFilter) ?>">
                    <div class="pm-upload-lbl">
                      <i class="ri-upload-cloud-line"></i>
                      <span><?= $hasPhysicalSlip ? 'เปลี่ยนรูปสลิป / อัปโหลดทับ:' : 'แนบรูปสลิปหลักฐานโอนเงิน:' ?></span>
                    </div>
                    <div class="pm-upload-inputs">
                      <input type="file" name="slip_file" accept="image/*" required class="pm-upload-file">
                      <button type="submit" class="la-btn la-btn-mini la-btn-primary" style="padding:3px 7px; font-size:10px;"><i class="ri-save-line"></i> บันทึก</button>
                    </div>
                  </form>
                </div>

                <!-- Box 3: Management Actions -->
                <div class="pm-box">
                  <div class="pm-box-title">
                    <i class="ri-tools-line"></i>
                    <span>เครื่องมือจัดการ & แอ็กชัน</span>
                  </div>

                  <div class="pm-act-group">
                    <?php if ($st === 'pending'): ?>
                      <!-- 1. Approve & Credit Button -->
                      <form method="post" action="/admin/payments/<?= $pid ?>/approve" onsubmit="return confirm('ยืนยันอนุมัติและเติมเงิน ฿<?= number_format($amt,2) ?> เข้ากระเป๋าคุณ <?= htmlspecialchars($cl) ?> ?')">
                        <input type="hidden" name="next" value="<?= htmlspecialchars($statusFilter) ?>">
                        <button type="submit" class="pm-act-btn pm-btn-approve">
                          <i class="ri-checkbox-circle-fill"></i> อนุมัติ & เติมเครดิตทันที
                        </button>
                      </form>

                      <!-- 2. Recheck Slip QR/Satang -->
                      <form method="post" action="/admin/payments/<?= $pid ?>/recheck">
                        <input type="hidden" name="next" value="<?= htmlspecialchars($statusFilter) ?>">
                        <button type="submit" class="la-btn la-btn-ghost pm-act-btn" style="border-color:#334155;">
                          <i class="ri-refresh-line"></i> ตรวจสลิปซ้ำ (Recheck)
                        </button>
                      </form>

                      <!-- 3. Unlock Slip Hash Duplicate -->
                      <form method="post" action="/admin/payments/<?= $pid ?>/unlock-slip" onsubmit="return confirm('ปลดล็อกประวัติสลิป #<?= $pid ?> เพื่อให้สามารถตรวจซ้ำได้?')">
                        <input type="hidden" name="next" value="<?= htmlspecialchars($statusFilter) ?>">
                        <button type="submit" class="la-btn la-btn-ghost pm-act-btn" style="border-color:#334155;">
                          <i class="ri-lock-unlock-line"></i> ปลดล็อกสลิปซ้ำ (Unlock)
                        </button>
                      </form>

                      <!-- 4. Reject Payment Form -->
                      <form class="pm-reject-box" method="post" action="/admin/payments/<?= $pid ?>/reject" onsubmit="return confirm('ยืนยันปฏิเสธรายการเติมเงิน #<?= $pid ?> ?')">
                        <input type="hidden" name="next" value="<?= htmlspecialchars($statusFilter) ?>">
                        <div style="font-size:10px; color:#f87171; font-weight:600;"><i class="ri-close-circle-line"></i> ปฏิเสธรายการ:</div>
                        <input type="text" class="pm-reject-input" name="note" placeholder="เหตุผล (เช่น สลิปปลอม, ยอดไม่เข้า)" value="<?= htmlspecialchars($note) ?>">
                        <button type="submit" class="pm-act-btn pm-btn-reject" style="padding:5px 8px;">
                          <i class="ri-close-line"></i> ยืนยันปฏิเสธ
                        </button>
                      </form>
                    <?php else: ?>
                      <!-- Already Paid or Canceled -->
                      <div style="background:#0d131f; padding:6px; border-radius:6px; border:1px solid #1f2d45; text-align:center;">
                        <span style="font-size:11px; font-weight:600; color:<?= $st === 'paid' ? '#34d399' : '#94a3b8' ?>;">
                          <i class="<?= $st === 'paid' ? 'ri-checkbox-circle-fill' : 'ri-close-circle-fill' ?>"></i>
                          รายการนี้<?= $st === 'paid' ? 'อนุมัติเรียบร้อยแล้ว' : 'ถูกปฏิเสธแล้ว' ?>
                        </span>
                      </div>
                    <?php endif; ?>

                    <!-- Internal Note Form -->
                    <form class="pm-note-form" method="post" action="/admin/payments/<?= $pid ?>/note">
                      <input type="hidden" name="next" value="<?= htmlspecialchars($statusFilter) ?>">
                      <input type="text" class="pm-note-input" name="note" placeholder="บันทึกข้อความภายใน..." value="<?= htmlspecialchars($note) ?>">
                      <button type="submit" class="la-btn la-btn-mini la-btn-ghost" style="padding:3px 7px; font-size:10px;"><i class="ri-save-line"></i> โน้ต</button>
                    </form>
                  </div>
                </div>

              </div>
            </div>
          </article>
        <?php endforeach; ?>
      </div>
    </div>

    <!-- Interactive Slip Lightbox Modal -->
    <div id="pmLightboxModal" class="pm-modal" onclick="closePmLighbox(event)">
      <div class="pm-modal-content" onclick="event.stopPropagation()">
        <div class="pm-modal-bar">
          <div>
            <div id="pmModalTitle" class="pm-modal-title">หลักฐานสลิปโอนเงิน</div>
            <div id="pmModalSub" style="font-size:10px; color:#94a3b8;"></div>
          </div>
          <div class="pm-modal-actions">
            <a id="pmModalOpenLink" href="#" target="_blank" class="la-btn la-btn-mini la-btn-ghost" style="padding:3px 7px; font-size:11px;"><i class="ri-external-link-line"></i> ภาพเต็ม</a>
            <a id="pmModalDlLink" href="#" download class="la-btn la-btn-mini la-btn-ghost" style="padding:3px 7px; font-size:11px;"><i class="ri-download-2-line"></i> ดาวน์โหลด</a>
            <button type="button" class="pm-modal-close" onclick="closePmLighbox()"><i class="ri-close-line"></i></button>
          </div>
        </div>
        <div class="pm-modal-body">
          <img id="pmModalImg" src="" alt="ภาพสลิป">
        </div>
      </div>
    </div>

    <script>
    function togglePmDrawer(pid) {
      var card = document.getElementById('pmCard-' + pid);
      if (card) {
        card.classList.toggle('is-open');
      }
    }

    function openPmLighbox(url, pid, client, amount) {
      var modal = document.getElementById('pmLightboxModal');
      var img = document.getElementById('pmModalImg');
      var title = document.getElementById('pmModalTitle');
      var sub = document.getElementById('pmModalSub');
      var openLink = document.getElementById('pmModalOpenLink');
      var dlLink = document.getElementById('pmModalDlLink');

      if (!modal || !img) return;

      img.src = url;
      title.innerText = 'หลักฐานสลิปโอนเงิน #' + pid;
      if (sub && client && amount) {
        sub.innerText = 'ลูกค้า: ' + client + ' · ยอดโอน: ฿' + amount + ' บาท';
      }
      if (openLink) openLink.href = url;
      if (dlLink) {
        dlLink.href = url;
        dlLink.setAttribute('download', 'slip-' + pid + '.jpg');
      }

      modal.classList.add('is-active');
      document.body.style.overflow = 'hidden';
    }

    function closePmLighbox(event) {
      if (event && event.target && event.target.closest('.pm-modal-content')) {
        return;
      }
      var modal = document.getElementById('pmLightboxModal');
      if (modal) {
        modal.classList.remove('is-active');
        document.body.style.overflow = '';
      }
    }

    document.addEventListener('keydown', function(e) {
      if (e.key === 'Escape') {
        closePmLighbox();
      }
    });

    function onPmLiveSearch(query) {
      var q = (query || '').toLowerCase().trim();
      var cards = document.querySelectorAll('.pm-card');
      cards.forEach(function(card) {
        var sData = card.getAttribute('data-search') || '';
        if (!q || sData.indexOf(q) !== -1) {
          card.style.display = '';
        } else {
          card.style.display = 'none';
        }
      });
    }

    function onPmMethodFilter(method) {
      var m = (method || '').toLowerCase().trim();
      var cards = document.querySelectorAll('.pm-card');
      cards.forEach(function(card) {
        var cMethod = (card.getAttribute('data-method') || '').toLowerCase().trim();
        if (!m || cMethod === m) {
          card.style.display = '';
        } else {
          card.style.display = 'none';
        }
      });
    }
    </script>
    <?php
    $newContent = ob_get_clean();

    $html = substr($html, 0, $mStart) . '<main class="dash-content">' . $newContent . '</main>' . substr($html, $mEnd + strlen('</main>'));
    return $html;
}
