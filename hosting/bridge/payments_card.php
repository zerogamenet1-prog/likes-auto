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
      .pay-desk-wrap {
        display: flex;
        flex-direction: column;
        gap: 1.25rem;
        margin-bottom: 2.5rem;
        font-family: inherit;
      }
      /* KPI Counters */
      .pay-kpi-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 1rem;
      }
      .pay-kpi-card {
        background: #141c2b;
        border: 1px solid #1f2d45;
        border-radius: 12px;
        padding: 1.1rem 1.25rem;
        display: flex;
        align-items: center;
        justify-content: space-between;
        text-decoration: none;
        color: inherit;
        transition: transform .18s ease, border-color .18s ease, box-shadow .18s ease;
        position: relative;
        overflow: hidden;
      }
      .pay-kpi-card:hover {
        transform: translateY(-2px);
        border-color: #3b82f6;
        box-shadow: 0 8px 20px rgba(0,0,0,0.3);
      }
      .pay-kpi-card.is-active {
        border-color: #3b82f6;
        background: linear-gradient(145deg, #162238 0%, #111a29 100%);
        box-shadow: 0 0 0 1px #3b82f6;
      }
      .pay-kpi-card.is-pending-alert {
        border-color: #f59e0b;
        background: linear-gradient(145deg, #2a2012 0%, #161a24 100%);
      }
      .pay-kpi-card.is-pending-alert .pay-kpi-icon {
        color: #f59e0b;
        background: rgba(245, 158, 11, 0.15);
      }
      .pay-kpi-info span {
        display: block;
        font-size: 0.8rem;
        color: #94a3b8;
        font-weight: 500;
        margin-bottom: 0.25rem;
      }
      .pay-kpi-info b {
        font-size: 1.6rem;
        font-weight: 700;
        color: #f8fafc;
        line-height: 1.1;
      }
      .pay-kpi-info small {
        display: block;
        font-size: 0.75rem;
        color: #cbd5e1;
        margin-top: 0.3rem;
      }
      .pay-kpi-icon {
        width: 46px;
        height: 46px;
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.4rem;
        background: rgba(59, 130, 246, 0.12);
        color: #3b82f6;
        flex-shrink: 0;
      }
      .pay-kpi-card.kpi-paid .pay-kpi-icon {
        color: #10b981;
        background: rgba(16, 185, 129, 0.12);
      }
      .pay-kpi-card.kpi-canceled .pay-kpi-icon {
        color: #ef4444;
        background: rgba(239, 68, 68, 0.12);
      }

      /* Quick Control & Match Bar */
      .pay-toolbar {
        background: #141c2b;
        border: 1px solid #1f2d45;
        border-radius: 12px;
        padding: 1rem 1.25rem;
        display: flex;
        flex-direction: column;
        gap: 1rem;
      }
      .pay-toolbar-top {
        display: flex;
        align-items: center;
        justify-content: space-between;
        flex-wrap: wrap;
        gap: 0.75rem;
      }
      .pay-tabs {
        display: flex;
        gap: 0.4rem;
        background: #0d131f;
        padding: 0.3rem;
        border-radius: 8px;
        border: 1px solid #1f2d45;
      }
      .pay-tab-btn {
        padding: 0.45rem 0.9rem;
        font-size: 0.82rem;
        font-weight: 500;
        color: #94a3b8;
        border-radius: 6px;
        text-decoration: none;
        transition: all .15s ease;
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
      }
      .pay-tab-btn:hover {
        color: #f8fafc;
        background: rgba(255,255,255,0.04);
      }
      .pay-tab-btn.is-active {
        background: #3b82f6;
        color: #fff;
        font-weight: 600;
      }
      .pay-tab-badge {
        font-size: 0.7rem;
        padding: 0.1rem 0.45rem;
        border-radius: 999px;
        background: rgba(0,0,0,0.3);
      }

      .pay-quick-match-wrap {
        display: flex;
        align-items: center;
        gap: 0.6rem;
        flex-wrap: wrap;
      }
      .pay-match-form {
        display: flex;
        align-items: center;
        gap: 0.4rem;
        background: #0d131f;
        border: 1px solid #2a3b5c;
        padding: 0.25rem 0.4rem;
        border-radius: 8px;
      }
      .pay-match-input {
        background: transparent;
        border: none;
        color: #f8fafc;
        font-size: 0.85rem;
        padding: 0.35rem 0.5rem;
        outline: none;
        width: 130px;
        font-weight: 600;
      }
      .pay-match-input::placeholder {
        color: #64748b;
        font-weight: normal;
      }

      /* Search & Filter Bar */
      .pay-search-row {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        flex-wrap: wrap;
      }
      .pay-search-box {
        position: relative;
        flex: 1;
        min-width: 260px;
      }
      .pay-search-box i {
        position: absolute;
        left: 0.85rem;
        top: 50%;
        transform: translateY(-50%);
        color: #64748b;
        font-size: 1rem;
      }
      .pay-search-box input {
        width: 100%;
        background: #0d131f;
        border: 1px solid #1f2d45;
        border-radius: 8px;
        padding: 0.55rem 0.85rem 0.55rem 2.4rem;
        color: #f8fafc;
        font-size: 0.85rem;
        outline: none;
        transition: border-color .15s ease;
      }
      .pay-search-box input:focus {
        border-color: #3b82f6;
      }
      .pay-method-select {
        background: #0d131f;
        border: 1px solid #1f2d45;
        border-radius: 8px;
        padding: 0.55rem 0.85rem;
        color: #f8fafc;
        font-size: 0.85rem;
        outline: none;
      }

      /* Flash Alerts */
      .pay-alert-ok {
        background: rgba(16, 185, 129, 0.15);
        border: 1px solid rgba(16, 185, 129, 0.4);
        color: #34d399;
        padding: 0.85rem 1.1rem;
        border-radius: 8px;
        font-size: 0.9rem;
        display: flex;
        align-items: center;
        gap: 0.6rem;
      }
      .pay-alert-err {
        background: rgba(239, 68, 68, 0.15);
        border: 1px solid rgba(239, 68, 68, 0.4);
        color: #f87171;
        padding: 0.85rem 1.1rem;
        border-radius: 8px;
        font-size: 0.9rem;
        display: flex;
        align-items: center;
        gap: 0.6rem;
      }

      /* Payments Cards List */
      .pay-cards-list {
        display: flex;
        flex-direction: column;
        gap: 0.85rem;
      }
      .pay-card {
        background: #141c2b;
        border: 1px solid #1f2d45;
        border-radius: 12px;
        overflow: hidden;
        transition: border-color .15s ease, box-shadow .15s ease;
      }
      .pay-card:hover {
        border-color: #2b3e61;
      }
      .pay-card.status-pending {
        border-left: 4px solid #f59e0b;
      }
      .pay-card.status-paid {
        border-left: 4px solid #10b981;
      }
      .pay-card.status-canceled {
        border-left: 4px solid #64748b;
      }

      /* Card Header Bar */
      .pay-card-header {
        padding: 0.9rem 1.25rem;
        display: flex;
        align-items: center;
        justify-content: space-between;
        cursor: pointer;
        user-select: none;
        gap: 1rem;
        background: rgba(255, 255, 255, 0.015);
      }
      .pay-card-header:hover {
        background: rgba(255, 255, 255, 0.03);
      }
      .pay-header-left {
        display: flex;
        align-items: center;
        gap: 0.85rem;
        flex-wrap: wrap;
      }
      .pay-id-badge {
        font-family: monospace;
        font-weight: 700;
        font-size: 0.85rem;
        padding: 0.2rem 0.55rem;
        background: #1e293b;
        color: #cbd5e1;
        border-radius: 6px;
        border: 1px solid #334155;
      }
      .pay-status-pill {
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
        font-size: 0.78rem;
        font-weight: 600;
        padding: 0.25rem 0.65rem;
        border-radius: 999px;
      }
      .status-pill-pending {
        background: rgba(245, 158, 11, 0.15);
        color: #f59e0b;
        border: 1px solid rgba(245, 158, 11, 0.35);
      }
      .status-pill-paid {
        background: rgba(16, 185, 129, 0.15);
        color: #10b981;
        border: 1px solid rgba(16, 185, 129, 0.35);
      }
      .status-pill-canceled {
        background: rgba(148, 163, 184, 0.15);
        color: #94a3b8;
        border: 1px solid rgba(148, 163, 184, 0.35);
      }
      .pulse-dot {
        width: 7px;
        height: 7px;
        border-radius: 50%;
        background: currentColor;
        box-shadow: 0 0 0 0 rgba(245, 158, 11, 0.7);
        animation: pulseAnimation 1.6s infinite;
      }
      @keyframes pulseAnimation {
        0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(245, 158, 11, 0.7); }
        70% { transform: scale(1); box-shadow: 0 0 0 6px rgba(245, 158, 11, 0); }
        100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(245, 158, 11, 0); }
      }

      .pay-amount-box {
        display: flex;
        align-items: baseline;
        gap: 0.3rem;
      }
      .pay-amount-num {
        font-size: 1.25rem;
        font-weight: 800;
        color: #10b981;
        letter-spacing: -0.02em;
      }
      .status-pending .pay-amount-num {
        color: #fbbf24;
      }
      .status-canceled .pay-amount-num {
        color: #94a3b8;
      }
      .pay-amount-unit {
        font-size: 0.8rem;
        color: #64748b;
      }

      .pay-client-pill {
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
        font-size: 0.82rem;
        color: #f1f5f9;
        font-weight: 500;
      }
      .pay-client-pill a {
        color: #60a5fa;
        text-decoration: none;
      }
      .pay-client-pill a:hover {
        text-decoration: underline;
      }
      .pay-bal-pill {
        font-size: 0.72rem;
        background: #0f172a;
        border: 1px solid #1e293b;
        color: #94a3b8;
        padding: 0.15rem 0.45rem;
        border-radius: 4px;
      }

      .pay-header-right {
        display: flex;
        align-items: center;
        gap: 0.85rem;
      }
      .pay-method-pill {
        font-size: 0.78rem;
        color: #94a3b8;
        display: inline-flex;
        align-items: center;
        gap: 0.3rem;
      }
      .pay-date-pill {
        font-size: 0.75rem;
        color: #64748b;
      }
      .pay-slip-badge {
        font-size: 0.74rem;
        padding: 0.18rem 0.5rem;
        border-radius: 6px;
        display: inline-flex;
        align-items: center;
        gap: 0.3rem;
      }
      .slip-badge-real {
        background: rgba(16, 185, 129, 0.12);
        color: #34d399;
        border: 1px solid rgba(16, 185, 129, 0.25);
      }
      .slip-badge-eslip {
        background: rgba(59, 130, 246, 0.12);
        color: #60a5fa;
        border: 1px solid rgba(59, 130, 246, 0.25);
      }
      .slip-badge-none {
        background: rgba(148, 163, 184, 0.1);
        color: #94a3b8;
      }

      .pay-toggle-btn {
        background: #1e293b;
        border: 1px solid #334155;
        color: #cbd5e1;
        width: 32px;
        height: 32px;
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1rem;
        transition: transform .18s ease;
      }
      .pay-card.is-open .pay-toggle-btn {
        transform: rotate(180deg);
        background: #3b82f6;
        color: #fff;
        border-color: #3b82f6;
      }

      /* Card Drawer */
      .pay-drawer {
        display: none;
        border-top: 1px solid #1f2d45;
        padding: 1.25rem;
        background: #0d131f;
      }
      .pay-card.is-open .pay-drawer {
        display: block;
      }
      .pay-drawer-grid {
        display: grid;
        grid-template-columns: 1fr 1fr 1fr;
        gap: 1.25rem;
      }
      @media (max-width: 1024px) {
        .pay-drawer-grid {
          grid-template-columns: 1fr;
        }
      }

      /* Drawer Box */
      .pay-box {
        background: #141c2b;
        border: 1px solid #1f2d45;
        border-radius: 10px;
        padding: 1rem 1.1rem;
        display: flex;
        flex-direction: column;
        gap: 0.85rem;
      }
      .pay-box-title {
        font-size: 0.85rem;
        font-weight: 700;
        color: #f1f5f9;
        display: flex;
        align-items: center;
        gap: 0.45rem;
        border-bottom: 1px solid #1f2d45;
        padding-bottom: 0.6rem;
      }
      .pay-box-title i {
        color: #3b82f6;
        font-size: 1.05rem;
      }

      /* Detail Pairs */
      .pay-kv-list {
        display: flex;
        flex-direction: column;
        gap: 0.55rem;
        font-size: 0.82rem;
      }
      .pay-kv-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 0.75rem;
      }
      .pay-kv-label {
        color: #94a3b8;
      }
      .pay-kv-val {
        color: #f8fafc;
        font-weight: 500;
        text-align: right;
      }
      .pay-kv-val code {
        font-family: monospace;
        background: #0d131f;
        padding: 0.15rem 0.4rem;
        border-radius: 4px;
        border: 1px solid #1e293b;
        color: #60a5fa;
      }

      /* Slip Box - Image Preview */
      .slip-photo-box {
        position: relative;
        background: #090d15;
        border: 1px solid #1f2d45;
        border-radius: 8px;
        overflow: hidden;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        min-height: 200px;
        max-height: 320px;
      }
      .slip-photo-box:hover .slip-photo-zoom-hint {
        opacity: 1;
      }
      .slip-img-thumb {
        max-width: 100%;
        max-height: 320px;
        object-fit: contain;
        display: block;
        transition: transform .2s ease;
      }
      .slip-photo-box:hover .slip-img-thumb {
        transform: scale(1.02);
      }
      .slip-photo-zoom-hint {
        position: absolute;
        bottom: 10px;
        right: 10px;
        background: rgba(15, 23, 42, 0.85);
        color: #fff;
        padding: 0.3rem 0.65rem;
        border-radius: 6px;
        font-size: 0.75rem;
        opacity: 0.85;
        transition: opacity .15s ease;
        display: flex;
        align-items: center;
        gap: 0.35rem;
      }
      .slip-photo-actions {
        display: flex;
        gap: 0.5rem;
        margin-top: 0.4rem;
      }

      /* Thai Bank Digital E-Slip Card */
      .thai-eslip-card {
        background: linear-gradient(180deg, #0e1e38 0%, #0a1324 100%);
        border: 1px solid #23385d;
        border-radius: 12px;
        padding: 1.1rem;
        box-shadow: 0 4px 15px rgba(0,0,0,0.35);
        display: flex;
        flex-direction: column;
        gap: 0.75rem;
        position: relative;
        overflow: hidden;
      }
      .thai-eslip-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(90deg, #0056b3, #00a86b);
      }
      .thai-eslip-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        border-bottom: 1px dashed #23385d;
        padding-bottom: 0.75rem;
      }
      .thai-eslip-brand {
        display: flex;
        flex-direction: column;
        gap: 0.2rem;
      }
      .promptpay-badge {
        font-size: 0.75rem;
        font-weight: 700;
        color: #38bdf8;
        display: flex;
        align-items: center;
        gap: 0.3rem;
      }
      .eslip-title {
        font-size: 0.85rem;
        font-weight: 600;
        color: #f1f5f9;
      }
      .eslip-verified-tag {
        font-size: 0.72rem;
        padding: 0.2rem 0.5rem;
        border-radius: 999px;
        font-weight: 600;
        display: flex;
        align-items: center;
        gap: 0.3rem;
      }
      .eslip-verified-tag.tag-paid {
        background: rgba(16, 185, 129, 0.2);
        color: #34d399;
        border: 1px solid rgba(16, 185, 129, 0.4);
      }
      .eslip-verified-tag.tag-pending {
        background: rgba(245, 158, 11, 0.2);
        color: #fbbf24;
        border: 1px solid rgba(245, 158, 11, 0.4);
      }

      .thai-eslip-amount-box {
        text-align: center;
        padding: 0.6rem 0;
        background: rgba(15, 23, 42, 0.5);
        border-radius: 8px;
        border: 1px solid #1e293b;
      }
      .eslip-amt-label {
        display: block;
        font-size: 0.72rem;
        color: #94a3b8;
      }
      .eslip-amt-val {
        font-size: 1.7rem;
        font-weight: 800;
        color: #34d399;
        letter-spacing: -0.02em;
      }
      .eslip-currency {
        font-size: 0.75rem;
        color: #64748b;
        margin-left: 0.2rem;
      }

      .thai-eslip-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-size: 0.78rem;
        gap: 0.5rem;
      }
      .eslip-lbl {
        color: #94a3b8;
        display: flex;
        align-items: center;
        gap: 0.3rem;
      }
      .eslip-val {
        color: #f8fafc;
        text-align: right;
      }
      .eslip-code {
        font-family: monospace;
        font-size: 0.76rem;
        background: #090e18;
        padding: 0.15rem 0.4rem;
        border-radius: 4px;
        border: 1px solid #1e293b;
        color: #93c5fd;
      }
      .eslip-ref-highlight {
        color: #fbbf24;
        border-color: #78350f;
        background: #1c1508;
      }
      .thai-eslip-footer {
        border-top: 1px dashed #23385d;
        padding-top: 0.6rem;
        font-size: 0.72rem;
        color: #64748b;
        text-align: center;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 0.35rem;
      }

      /* Admin Upload Box */
      .slip-upload-box {
        margin-top: 0.5rem;
        background: #0a0f19;
        border: 1px dashed #2a3b5c;
        border-radius: 8px;
        padding: 0.75rem;
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
      }
      .slip-upload-label {
        font-size: 0.76rem;
        color: #94a3b8;
        display: flex;
        align-items: center;
        gap: 0.35rem;
      }
      .slip-upload-input-wrap {
        display: flex;
        gap: 0.4rem;
        align-items: center;
      }
      .slip-file-input {
        flex: 1;
        font-size: 0.75rem;
        color: #94a3b8;
      }

      /* Action Panel */
      .pay-action-group {
        display: flex;
        flex-direction: column;
        gap: 0.6rem;
      }
      .pay-action-btn {
        width: 100%;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 0.45rem;
        padding: 0.6rem 1rem;
        border-radius: 8px;
        font-weight: 600;
        font-size: 0.85rem;
        cursor: pointer;
        transition: all .15s ease;
      }
      .pay-btn-approve {
        background: #059669;
        color: #fff;
        border: 1px solid #10b981;
      }
      .pay-btn-approve:hover {
        background: #10b981;
      }
      .pay-btn-reject {
        background: #dc2626;
        color: #fff;
        border: 1px solid #ef4444;
      }
      .pay-btn-reject:hover {
        background: #ef4444;
      }
      .pay-reject-form {
        display: flex;
        flex-direction: column;
        gap: 0.4rem;
        background: #0d131f;
        padding: 0.65rem;
        border-radius: 8px;
        border: 1px solid #2a1f1f;
      }
      .pay-reject-input {
        background: #141c2b;
        border: 1px solid #3b2a2a;
        border-radius: 6px;
        padding: 0.4rem 0.6rem;
        color: #f8fafc;
        font-size: 0.8rem;
        outline: none;
      }
      .pay-note-form {
        display: flex;
        gap: 0.4rem;
      }
      .pay-note-input {
        flex: 1;
        background: #0d131f;
        border: 1px solid #1f2d45;
        border-radius: 6px;
        padding: 0.4rem 0.6rem;
        color: #f8fafc;
        font-size: 0.8rem;
        outline: none;
      }

      /* Lightbox Modal */
      .slip-lightbox-modal {
        display: none;
        position: fixed;
        inset: 0;
        z-index: 999999;
        background: rgba(0, 0, 0, 0.85);
        backdrop-filter: blur(4px);
        align-items: center;
        justify-content: center;
        padding: 1.5rem;
      }
      .slip-lightbox-modal.is-active {
        display: flex;
      }
      .slip-lightbox-content {
        max-width: 900px;
        width: 100%;
        max-height: 90vh;
        background: #141c2b;
        border: 1px solid #1f2d45;
        border-radius: 14px;
        overflow: hidden;
        display: flex;
        flex-direction: column;
        box-shadow: 0 20px 40px rgba(0,0,0,0.6);
      }
      .slip-lightbox-bar {
        padding: 0.85rem 1.25rem;
        background: #0d131f;
        border-bottom: 1px solid #1f2d45;
        display: flex;
        align-items: center;
        justify-content: space-between;
      }
      .slip-lightbox-title {
        font-size: 0.95rem;
        font-weight: 700;
        color: #f8fafc;
      }
      .slip-lightbox-actions {
        display: flex;
        align-items: center;
        gap: 0.5rem;
      }
      .slip-lightbox-close {
        background: #1e293b;
        border: 1px solid #334155;
        color: #f8fafc;
        width: 32px;
        height: 32px;
        border-radius: 6px;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.1rem;
      }
      .slip-lightbox-close:hover {
        background: #ef4444;
        border-color: #ef4444;
      }
      .slip-lightbox-image-wrap {
        padding: 1.25rem;
        overflow: auto;
        display: flex;
        align-items: center;
        justify-content: center;
        background: #090d15;
      }
      .slip-lightbox-image-wrap img {
        max-width: 100%;
        max-height: 75vh;
        object-fit: contain;
        border-radius: 8px;
        box-shadow: 0 5px 20px rgba(0,0,0,0.4);
      }
    </style>

    <div class="pay-desk-wrap">
      <!-- Flash Alert -->
      <?php if ($okMsg !== ''): ?>
        <div class="pay-alert-ok">
          <i class="ri-checkbox-circle-fill"></i>
          <span><?= $okMsg ?></span>
        </div>
      <?php endif; ?>
      <?php if ($errMsg !== ''): ?>
        <div class="pay-alert-err">
          <i class="ri-error-warning-fill"></i>
          <span><?= $errMsg ?></span>
        </div>
      <?php endif; ?>

      <!-- 4 KPI Summary Cards -->
      <div class="pay-kpi-grid">
        <a class="pay-kpi-card <?= $statusFilter === '' ? 'is-active' : '' ?>" href="/admin/payments">
          <div class="pay-kpi-info">
            <span>รายการเติมเงินทั้งหมด</span>
            <b><?= number_format($counts['all']) ?></b>
            <small>ยอดรวม ฿<?= number_format($sums['all'], 2) ?></small>
          </div>
          <div class="pay-kpi-icon"><i class="ri-wallet-3-line"></i></div>
        </a>

        <a class="pay-kpi-card <?= $statusFilter === 'pending' ? 'is-active' : '' ?> <?= $counts['pending'] > 0 ? 'is-pending-alert' : '' ?>" href="/admin/payments?status=pending">
          <div class="pay-kpi-info">
            <span>รอตรวจสอบยอด</span>
            <b><?= number_format($counts['pending']) ?></b>
            <small>รอยืนยัน ฿<?= number_format($sums['pending'], 2) ?></small>
          </div>
          <div class="pay-kpi-icon"><i class="ri-time-line"></i></div>
        </a>

        <a class="pay-kpi-card kpi-paid <?= $statusFilter === 'paid' ? 'is-active' : '' ?>" href="/admin/payments?status=paid">
          <div class="pay-kpi-info">
            <span>อนุมัติสำเร็จแล้ว</span>
            <b><?= number_format($counts['paid']) ?></b>
            <small>สำเร็จ ฿<?= number_format($sums['paid'], 2) ?></small>
          </div>
          <div class="pay-kpi-icon"><i class="ri-checkbox-circle-line"></i></div>
        </a>

        <a class="pay-kpi-card kpi-canceled <?= $statusFilter === 'canceled' ? 'is-active' : '' ?>" href="/admin/payments?status=canceled">
          <div class="pay-kpi-info">
            <span>ปฏิเสธ / ยกเลิก</span>
            <b><?= number_format($counts['canceled']) ?></b>
            <small>ยกเลิก ฿<?= number_format($sums['canceled'], 2) ?></small>
          </div>
          <div class="pay-kpi-icon"><i class="ri-close-circle-line"></i></div>
        </a>
      </div>

      <!-- Quick Toolbar & Matcher -->
      <div class="pay-toolbar">
        <div class="pay-toolbar-top">
          <!-- Status Filter Pills -->
          <div class="pay-tabs">
            <a href="/admin/payments" class="pay-tab-btn <?= $statusFilter === '' ? 'is-active' : '' ?>">
              ทั้งหมด <span class="pay-tab-badge"><?= $counts['all'] ?></span>
            </a>
            <a href="/admin/payments?status=pending" class="pay-tab-btn <?= $statusFilter === 'pending' ? 'is-active' : '' ?>">
              รอตรวจ <span class="pay-tab-badge"><?= $counts['pending'] ?></span>
            </a>
            <a href="/admin/payments?status=paid" class="pay-tab-btn <?= $statusFilter === 'paid' ? 'is-active' : '' ?>">
              อนุมัติแล้ว <span class="pay-tab-badge"><?= $counts['paid'] ?></span>
            </a>
            <a href="/admin/payments?status=canceled" class="pay-tab-btn <?= $statusFilter === 'canceled' ? 'is-active' : '' ?>">
              ปฏิเสธ <span class="pay-tab-badge"><?= $counts['canceled'] ?></span>
            </a>
          </div>

          <!-- Quick Match Bank Amount -->
          <div class="pay-quick-match-wrap">
            <form class="pay-match-form" method="post" action="/admin/payments/match">
              <input type="hidden" name="next" value="<?= htmlspecialchars($statusFilter) ?>">
              <i class="ri-focus-3-line" style="color:#60a5fa; margin-left:0.3rem;"></i>
              <input class="pay-match-input" name="amount" inputmode="decimal" placeholder="จับคู่ยอด เช่น 14.16" required>
              <button type="submit" class="la-btn la-btn-mini la-btn-primary"><i class="ri-link"></i> จับคู่ & อนุมัติ</button>
            </form>
            <a href="/admin/settings/payments" class="la-btn la-btn-mini la-btn-ghost"><i class="ri-settings-3-line"></i> ตั้งค่าเติมเงิน</a>
            <a href="/addfunds" target="_blank" class="la-btn la-btn-mini la-btn-ghost"><i class="ri-external-link-line"></i> หน้าเติมเงินลูกค้า</a>
          </div>
        </div>

        <!-- Live Search Bar -->
        <div class="pay-search-row">
          <div class="pay-search-box">
            <i class="ri-search-line"></i>
            <input type="text" id="payLiveSearch" placeholder="ค้นหาด่วน: #ID, ลูกค้า, ยอดเงิน, รหัสอ้างอิง, Bank Trans Ref..." value="<?= htmlspecialchars($searchQuery) ?>" oninput="onPayLiveSearch(this.value)">
          </div>
          <?php if (!empty($methodsList)): ?>
            <select class="pay-method-select" onchange="onPayMethodFilter(this.value)">
              <option value="">ทุกช่องทาง (<?= count($methodsList) ?>)</option>
              <?php foreach ($methodsList as $mItem): ?>
                <option value="<?= htmlspecialchars($mItem) ?>" <?= $methodFilter === $mItem ? 'selected' : '' ?>><?= htmlspecialchars($mItem) ?></option>
              <?php endforeach; ?>
            </select>
          <?php endif; ?>
        </div>
      </div>

      <!-- Payment Cards Accordion List -->
      <div class="pay-cards-list" id="payCardsContainer">
        <?php if (empty($payments)): ?>
          <div style="background:#141c2b; border:1px solid #1f2d45; border-radius:12px; padding:3rem 1.5rem; text-align:center; color:#94a3b8;">
            <i class="ri-inbox-line" style="font-size:2.5rem; color:#475569; display:block; margin-bottom:0.75rem;"></i>
            <h3 style="color:#f8fafc; font-size:1.1rem; margin-bottom:0.3rem;">ไม่พบรายการเติมเงิน</h3>
            <p style="font-size:0.85rem;">ยังไม่มีรายการที่ตรงกับเงื่อนไขการค้นหาหรือตัวกรองในขณะนี้</p>
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
            if ($slip !== '') {
                $cleanPath = ltrim($slip, '/');
                $docRoot = $_SERVER['DOCUMENT_ROOT'] ?? '';
                if ($docRoot !== '' && is_file($docRoot . '/' . $cleanPath)) {
                    $hasPhysicalSlip = true;
                } elseif (is_file(__DIR__ . '/../' . $cleanPath)) {
                    $hasPhysicalSlip = true;
                } elseif (is_file(dirname(__DIR__, 2) . '/' . $cleanPath)) {
                    $hasPhysicalSlip = true;
                }
            }
          ?>
          <article class="pay-card status-<?= $st ?> <?= $st === 'pending' ? 'is-open' : '' ?>"
                   id="payCard-<?= $pid ?>"
                   data-pid="<?= $pid ?>"
                   data-status="<?= $st ?>"
                   data-client="<?= htmlspecialchars(mb_strtolower($cl)) ?>"
                   data-method="<?= htmlspecialchars(mb_strtolower($m)) ?>"
                   data-search="<?= htmlspecialchars(mb_strtolower($pid . ' ' . $cl . ' ' . $amt . ' ' . $m . ' ' . $refCode . ' ' . $transRef . ' ' . $note)) ?>">

            <!-- Card Header -->
            <div class="pay-card-header" onclick="togglePayDrawer(<?= $pid ?>)">
              <div class="pay-header-left">
                <span class="pay-id-badge">#<?= $pid ?></span>

                <!-- Status Badge -->
                <?php if ($st === 'pending'): ?>
                  <span class="pay-status-pill status-pill-pending"><span class="pulse-dot"></span> รอตรวจ</span>
                <?php elseif ($st === 'paid'): ?>
                  <span class="pay-status-pill status-pill-paid"><i class="ri-checkbox-circle-fill"></i> อนุมัติแล้ว</span>
                <?php else: ?>
                  <span class="pay-status-pill status-pill-canceled"><i class="ri-close-circle-fill"></i> ปฏิเสธ</span>
                <?php endif; ?>

                <!-- Amount -->
                <div class="pay-amount-box">
                  <span class="pay-amount-num">฿<?= number_format($amt, 2) ?></span>
                  <span class="pay-amount-unit">บาท</span>
                </div>

                <!-- Client & Current Balance -->
                <div class="pay-client-pill">
                  <i class="ri-user-3-line" style="color:#64748b;"></i>
                  <a href="/admin/clients?q=<?= urlencode($cl) ?>" onclick="event.stopPropagation()"><b><?= htmlspecialchars($cl) ?></b></a>
                  <?php if ($cBal !== null): ?>
                    <span class="pay-bal-pill" title="ยอดเงินคงเหลือในกระเป๋าปัจจุบัน">คงเหลือ: ฿<?= number_format($cBal, 2) ?></span>
                  <?php endif; ?>
                </div>

                <!-- Ref code / Trans ref preview -->
                <?php if ($refCode !== ''): ?>
                  <code style="font-size:0.75rem; color:#93c5fd; background:#0d131f; padding:0.15rem 0.4rem; border-radius:4px; border:1px solid #1e293b;"><?= htmlspecialchars($refCode) ?></code>
                <?php endif; ?>
              </div>

              <div class="pay-header-right">
                <!-- Method & Date -->
                <span class="pay-method-pill"><i class="ri-qr-code-line"></i> <?= htmlspecialchars($m) ?></span>
                <span class="pay-date-pill"><i class="ri-time-line"></i> <?= htmlspecialchars($createdAt) ?></span>

                <!-- Slip Badge -->
                <?php if ($hasPhysicalSlip): ?>
                  <span class="pay-slip-badge slip-badge-real"><i class="ri-image-line"></i> มีรูปสลิป</span>
                <?php elseif ($transRef !== ''): ?>
                  <span class="pay-slip-badge slip-badge-eslip"><i class="ri-file-shield-line"></i> สลิปดิจิทัล</span>
                <?php else: ?>
                  <span class="pay-slip-badge slip-badge-none"><i class="ri-attachment-line"></i> รอแนบสลิป</span>
                <?php endif; ?>

                <!-- Accordion Toggle Button -->
                <button type="button" class="pay-toggle-btn" aria-label="ดูรายละเอียด">
                  <i class="ri-arrow-down-s-line"></i>
                </button>
              </div>
            </div>

            <!-- Card Expanded Drawer -->
            <div class="pay-drawer">
              <div class="pay-drawer-grid">

                <!-- Box 1: Payment Metadata -->
                <div class="pay-box">
                  <div class="pay-box-title">
                    <i class="ri-file-list-3-line"></i>
                    <span>ข้อมูลการเติมเงิน (#<?= $pid ?>)</span>
                  </div>
                  <div class="pay-kv-list">
                    <div class="pay-kv-row">
                      <span class="pay-kv-label">รหัสรายการ:</span>
                      <span class="pay-kv-val">#<?= $pid ?></span>
                    </div>
                    <div class="pay-kv-row">
                      <span class="pay-kv-label">ชื่อลูกค้า:</span>
                      <span class="pay-kv-val">
                        <a href="/admin/clients?q=<?= urlencode($cl) ?>" style="color:#60a5fa; text-decoration:none;"><b><?= htmlspecialchars($cl) ?></b></a>
                        <?php if ($cEmail !== ''): ?>
                          <div style="font-size:0.75rem; color:#64748b;"><?= htmlspecialchars($cEmail) ?></div>
                        <?php endif; ?>
                      </span>
                    </div>
                    <div class="pay-kv-row">
                      <span class="pay-kv-label">ยอดกระเป๋าปัจจุบัน:</span>
                      <span class="pay-kv-val" style="color:#34d399; font-weight:700;">฿<?= $cBal !== null ? number_format($cBal, 2) : '-' ?></span>
                    </div>
                    <div class="pay-kv-row">
                      <span class="pay-kv-label">ยอดที่ต้องโอน:</span>
                      <span class="pay-kv-val" style="color:#fbbf24; font-size:1.05rem; font-weight:800;">฿<?= number_format($amt, 2) ?></span>
                    </div>
                    <div class="pay-kv-row">
                      <span class="pay-kv-label">ช่องทางชำระเงิน:</span>
                      <span class="pay-kv-val"><?= htmlspecialchars($m) ?></span>
                    </div>
                    <div class="pay-kv-row">
                      <span class="pay-kv-label">รหัสอ้างอิงระบบ (Ref):</span>
                      <span class="pay-kv-val"><code><?= htmlspecialchars($refCode ?: '-') ?></code></span>
                    </div>
                    <?php if ($transRef !== ''): ?>
                      <div class="pay-kv-row">
                        <span class="pay-kv-label">Bank Trans Ref:</span>
                        <span class="pay-kv-val"><code style="color:#fbbf24; border-color:#78350f;"><?= htmlspecialchars($transRef) ?></code></span>
                      </div>
                    <?php endif; ?>
                    <div class="pay-kv-row">
                      <span class="pay-kv-label">วันที่/เวลาแจ้งโอน:</span>
                      <span class="pay-kv-val"><?= htmlspecialchars($createdAt) ?></span>
                    </div>
                    <div class="pay-kv-row">
                      <span class="pay-kv-label">สถานะปัจจุบัน:</span>
                      <span class="pay-kv-val">
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
                      <div class="pay-kv-row" style="align-items:flex-start; margin-top:0.4rem; padding-top:0.4rem; border-top:1px dashed #1f2d45;">
                        <span class="pay-kv-label">บันทึกช่วยจำ:</span>
                        <span class="pay-kv-val" style="color:#cbd5e1;"><?= nl2br(htmlspecialchars($note)) ?></span>
                      </div>
                    <?php endif; ?>
                  </div>
                </div>

                <!-- Box 2: Payment Slip Inspector -->
                <div class="pay-box">
                  <div class="pay-box-title">
                    <i class="ri-shield-check-line"></i>
                    <span>หลักฐานสลิปโอนเงิน</span>
                  </div>

                  <?php if ($hasPhysicalSlip): ?>
                    <!-- Real Attached Slip Image -->
                    <div class="slip-photo-box" onclick="openSlipLightbox('<?= htmlspecialchars($slip) ?>', <?= $pid ?>, '<?= htmlspecialchars($cl) ?>', '<?= number_format($amt,2) ?>')">
                      <img src="<?= htmlspecialchars($slip) ?>" alt="สลิปโอนเงิน #<?= $pid ?>" class="slip-img-thumb" loading="lazy">
                      <div class="slip-photo-zoom-hint"><i class="ri-zoom-in-line"></i> คลิกซูมดูรูปใหญ่</div>
                    </div>
                    <div class="slip-photo-actions">
                      <a href="<?= htmlspecialchars($slip) ?>" target="_blank" class="la-btn la-btn-mini la-btn-ghost"><i class="ri-external-link-line"></i> เปิดภาพเต็มจอ</a>
                      <a href="<?= htmlspecialchars($slip) ?>" download="slip-<?= $pid ?>.jpg" class="la-btn la-btn-mini la-btn-ghost"><i class="ri-download-2-line"></i> บันทึกรูปลงเครื่อง</a>
                    </div>
                  <?php else: ?>
                    <!-- Thai PromptPay Digital E-Slip Card -->
                    <div class="thai-eslip-card">
                      <div class="thai-eslip-header">
                        <div class="thai-eslip-brand">
                          <span class="promptpay-badge"><i class="ri-qr-code-line"></i> PromptPay</span>
                          <span class="eslip-title">สลิปโอนเงินดิจิทัล</span>
                        </div>
                        <div class="eslip-verified-tag <?= $st === 'paid' ? 'tag-paid' : 'tag-pending' ?>">
                          <i class="<?= $st === 'paid' ? 'ri-checkbox-circle-fill' : 'ri-time-line' ?>"></i>
                          <?= $st === 'paid' ? 'ชำระเงินสำเร็จ' : 'รอตรวจสอบยอด' ?>
                        </div>
                      </div>
                      <div class="thai-eslip-amount-box">
                        <span class="eslip-amt-label">จำนวนเงินที่โอน</span>
                        <span class="eslip-amt-val">฿<?= number_format($amt, 2) ?></span>
                        <span class="eslip-currency">บาท</span>
                      </div>
                      <div class="thai-eslip-row">
                        <span class="eslip-lbl"><i class="ri-user-line"></i> ลูกค้า:</span>
                        <span class="eslip-val"><b><?= htmlspecialchars($cl) ?></b></span>
                      </div>
                      <div class="thai-eslip-row">
                        <span class="eslip-lbl"><i class="ri-bank-card-line"></i> ช่องทาง:</span>
                        <span class="eslip-val"><?= htmlspecialchars($m ?: 'PromptPay') ?></span>
                      </div>
                      <div class="thai-eslip-row">
                        <span class="eslip-lbl"><i class="ri-hashtag"></i> รหัสอ้างอิง:</span>
                        <span class="eslip-val"><code class="eslip-code"><?= htmlspecialchars($refCode ?: 'LA' . $pid) ?></code></span>
                      </div>
                      <?php if ($transRef !== ''): ?>
                        <div class="thai-eslip-row">
                          <span class="eslip-lbl"><i class="ri-barcode-line"></i> Bank Trans Ref:</span>
                          <span class="eslip-val"><code class="eslip-code eslip-ref-highlight"><?= htmlspecialchars($transRef) ?></code></span>
                        </div>
                      <?php endif; ?>
                      <div class="thai-eslip-row">
                        <span class="eslip-lbl"><i class="ri-time-line"></i> เวลาทำรายการ:</span>
                        <span class="eslip-val"><?= htmlspecialchars($createdAt) ?></span>
                      </div>
                      <div class="thai-eslip-footer">
                        <i class="ri-shield-check-fill"></i> ระบบตรวจสอบการเงินอัตโนมัติ LIKES-AUTO
                      </div>
                    </div>
                  <?php endif; ?>

                  <!-- Admin Attach/Replace Slip Upload Form -->
                  <form class="slip-upload-box" method="post" action="/admin/payments/<?= $pid ?>/upload-slip" enctype="multipart/form-data">
                    <input type="hidden" name="next" value="<?= htmlspecialchars($statusFilter) ?>">
                    <div class="slip-upload-label">
                      <i class="ri-upload-cloud-line"></i>
                      <span><?= $hasPhysicalSlip ? 'เปลี่ยนรูปสลิป / อัปโหลดทับ:' : 'แนบรูปสลิปหลักฐานโอนเงิน:' ?></span>
                    </div>
                    <div class="slip-upload-input-wrap">
                      <input type="file" name="slip_file" accept="image/*" required class="slip-file-input">
                      <button type="submit" class="la-btn la-btn-mini la-btn-primary"><i class="ri-save-line"></i> อัปโหลด</button>
                    </div>
                  </form>
                </div>

                <!-- Box 3: Management & Actions Panel -->
                <div class="pay-box">
                  <div class="pay-box-title">
                    <i class="ri-tools-line"></i>
                    <span>เครื่องมือจัดการ & แอ็กชัน</span>
                  </div>

                  <div class="pay-action-group">
                    <?php if ($st === 'pending'): ?>
                      <!-- 1. Approve & Credit Button -->
                      <form method="post" action="/admin/payments/<?= $pid ?>/approve" onsubmit="return confirm('ยืนยันอนุมัติและเติมเงิน ฿<?= number_format($amt,2) ?> เข้ากระเป๋าคุณ <?= htmlspecialchars($cl) ?> ?')">
                        <input type="hidden" name="next" value="<?= htmlspecialchars($statusFilter) ?>">
                        <button type="submit" class="pay-action-btn pay-btn-approve">
                          <i class="ri-checkbox-circle-fill"></i> อนุมัติ & เติมเครดิตทันที
                        </button>
                      </form>

                      <!-- 2. Recheck Slip QR/Satang -->
                      <form method="post" action="/admin/payments/<?= $pid ?>/recheck">
                        <input type="hidden" name="next" value="<?= htmlspecialchars($statusFilter) ?>">
                        <button type="submit" class="la-btn la-btn-ghost pay-action-btn" style="border-color:#334155;">
                          <i class="ri-refresh-line"></i> ตรวจสลิปซ้ำ (Recheck)
                        </button>
                      </form>

                      <!-- 3. Unlock Slip Hash Duplicate -->
                      <form method="post" action="/admin/payments/<?= $pid ?>/unlock-slip" onsubmit="return confirm('ปลดล็อกประวัติสลิป #<?= $pid ?> เพื่อให้สามารถตรวจซ้ำได้?')">
                        <input type="hidden" name="next" value="<?= htmlspecialchars($statusFilter) ?>">
                        <button type="submit" class="la-btn la-btn-ghost pay-action-btn" style="border-color:#334155;">
                          <i class="ri-lock-unlock-line"></i> ปลดล็อกสลิปซ้ำ (Unlock)
                        </button>
                      </form>

                      <!-- 4. Reject Payment Form -->
                      <form class="pay-reject-form" method="post" action="/admin/payments/<?= $pid ?>/reject" onsubmit="return confirm('ยืนยันปฏิเสธรายการเติมเงิน #<?= $pid ?> ?')">
                        <input type="hidden" name="next" value="<?= htmlspecialchars($statusFilter) ?>">
                        <div style="font-size:0.75rem; color:#f87171; font-weight:600;"><i class="ri-close-circle-line"></i> ปฏิเสธรายการ:</div>
                        <input type="text" class="pay-reject-input" name="note" placeholder="เหตุผล (เช่น สลิปปลอม, ยอดไม่เข้า)" value="<?= htmlspecialchars($note) ?>">
                        <button type="submit" class="pay-action-btn pay-btn-reject">
                          <i class="ri-close-line"></i> ปฏิเสธรายการ
                        </button>
                      </form>
                    <?php else: ?>
                      <!-- Already Paid or Canceled -->
                      <div style="background:#0d131f; padding:0.75rem; border-radius:8px; border:1px solid #1f2d45; text-align:center;">
                        <span style="font-size:0.85rem; font-weight:600; color:<?= $st === 'paid' ? '#34d399' : '#94a3b8' ?>;">
                          <i class="<?= $st === 'paid' ? 'ri-checkbox-circle-fill' : 'ri-close-circle-fill' ?>"></i>
                          รายการนี้<?= $st === 'paid' ? 'อนุมัติเรียบร้อยแล้ว' : 'ถูกปฏิเสธแล้ว' ?>
                        </span>
                      </div>
                    <?php endif; ?>

                    <!-- Internal Note Form -->
                    <form class="pay-note-form" method="post" action="/admin/payments/<?= $pid ?>/note" style="margin-top:0.4rem;">
                      <input type="hidden" name="next" value="<?= htmlspecialchars($statusFilter) ?>">
                      <input type="text" class="pay-note-input" name="note" placeholder="บันทึกข้อความภายใน..." value="<?= htmlspecialchars($note) ?>">
                      <button type="submit" class="la-btn la-btn-mini la-btn-ghost"><i class="ri-save-line"></i> บันทึกโน้ต</button>
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
    <div id="slipLightboxModal" class="slip-lightbox-modal" onclick="closeSlipLightbox(event)">
      <div class="slip-lightbox-content" onclick="event.stopPropagation()">
        <div class="slip-lightbox-bar">
          <div>
            <div id="slipLightboxTitle" class="slip-lightbox-title">หลักฐานสลิปโอนเงิน</div>
            <div id="slipLightboxSub" style="font-size:0.75rem; color:#94a3b8;"></div>
          </div>
          <div class="slip-lightbox-actions">
            <a id="slipLightboxOpenLink" href="#" target="_blank" class="la-btn la-btn-mini la-btn-ghost"><i class="ri-external-link-line"></i> เปิดภาพเต็มจอ</a>
            <a id="slipLightboxDownloadLink" href="#" download class="la-btn la-btn-mini la-btn-ghost"><i class="ri-download-2-line"></i> ดาวน์โหลด</a>
            <button type="button" class="slip-lightbox-close" onclick="closeSlipLightbox()"><i class="ri-close-line"></i></button>
          </div>
        </div>
        <div class="slip-lightbox-image-wrap">
          <img id="slipLightboxImg" src="" alt="ภาพสลิป">
        </div>
      </div>
    </div>

    <script>
    function togglePayDrawer(pid) {
      var card = document.getElementById('payCard-' + pid);
      if (card) {
        card.classList.toggle('is-open');
      }
    }

    function openSlipLightbox(url, pid, client, amount) {
      var modal = document.getElementById('slipLightboxModal');
      var img = document.getElementById('slipLightboxImg');
      var title = document.getElementById('slipLightboxTitle');
      var sub = document.getElementById('slipLightboxSub');
      var openLink = document.getElementById('slipLightboxOpenLink');
      var dlLink = document.getElementById('slipLightboxDownloadLink');

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

    function closeSlipLightbox(event) {
      if (event && event.target && event.target.closest('.slip-lightbox-content')) {
        return;
      }
      var modal = document.getElementById('slipLightboxModal');
      if (modal) {
        modal.classList.remove('is-active');
        document.body.style.overflow = '';
      }
    }

    document.addEventListener('keydown', function(e) {
      if (e.key === 'Escape') {
        closeSlipLightbox();
      }
    });

    // Live search in cards
    function onPayLiveSearch(query) {
      var q = (query || '').toLowerCase().trim();
      var cards = document.querySelectorAll('.pay-card');
      cards.forEach(function(card) {
        var sData = card.getAttribute('data-search') || '';
        if (!q || sData.indexOf(q) !== -1) {
          card.style.display = '';
        } else {
          card.style.display = 'none';
        }
      });
    }

    // Method filter
    function onPayMethodFilter(method) {
      var m = (method || '').toLowerCase().trim();
      var cards = document.querySelectorAll('.pay-card');
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
