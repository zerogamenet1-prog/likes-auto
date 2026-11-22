<?php
declare(strict_types=1);

/**
 * Modern Admin Dashboard Live Database Synchronizer for LIKES-AUTO.
 * Synchronizes:
 * 1. "ออเดอร์ล่าสุด" (Latest Orders table): live statuses, JAP IDs, exact badge classes matching /admin/orders.
 * 2. KPI metrics: total clients, total orders, total revenue (paid payments sum), pending payments.
 * 3. "เติมเงินรออนุมัติ" (Pending payments widget).
 * 4. "ตั๋วที่เปิดอยู่" (Open tickets widget).
 */
function la_patch_admin_dashboard(string $html): string {
    $dbPaths = [
        __DIR__ . '/.la-db-restore-latest.db',
        __DIR__ . '/.la-db-restore-d1qyg5az73cs4unx8jl9trbw.db',
        __DIR__ . '/../.la-db-restore-latest.db',
        __DIR__ . '/../.la-db-restore-d1qyg5az73cs4unx8jl9trbw.db',
        dirname(__DIR__, 2) . '/live_app.db',
        dirname(__DIR__, 2) . '/live_server_latest.db',
    ];

    $dbFile = null;
    foreach ($dbPaths as $p) {
        if (file_exists($p)) {
            $dbFile = $p;
            break;
        }
    }
    if (!$dbFile || !class_exists('SQLite3')) {
        return $html;
    }

    try {
        $db = new SQLite3($dbFile, SQLITE3_OPEN_READONLY);
        $db->busyTimeout(5000);

        // 1. Live Orders (8 latest)
        $ordRes = @$db->query("SELECT id, client, service, quantity, status, api_orderid, charge, created_at FROM orders ORDER BY id DESC LIMIT 8");
        if ($ordRes) {
            $rowsHtml = '';
            $stLabels = [
                'pending' => 'รอส่ง',
                'processing' => 'กำลังทำ',
                'inprogress' => 'กำลังทำ',
                'completed' => 'สำเร็จ',
                'partial' => 'บางส่วน',
                'canceled' => 'ยกเลิก',
                'refunded' => 'คืนเงิน',
            ];

            while ($row = $ordRes->fetchArray(SQLITE3_ASSOC)) {
                $oid = (int)$row['id'];
                $client = (string)($row['client'] ?? '');
                $service = (string)($row['service'] ?? '');
                $quantity = (int)($row['quantity'] ?? 0);
                $st = strtolower(trim((string)($row['status'] ?? 'pending')));
                $apiOid = trim((string)($row['api_orderid'] ?? ''));

                // Determine badge and label
                $badgeClass = $st;
                $stText = $stLabels[$st] ?? $st;
                if ($st === 'inprogress') {
                    $badgeClass = 'processing';
                    $stText = 'กำลังทำ';
                } elseif ($st === 'pending' && $apiOid !== '' && $apiOid !== '-') {
                    $badgeClass = 'processing';
                    $stText = 'กำลังทำ';
                }

                $rowsHtml .= "\n          <tr>\n";
                $rowsHtml .= "            <td>{$oid}</td>";
                $rowsHtml .= "<td>" . htmlspecialchars($client, ENT_QUOTES, 'UTF-8') . "</td>";
                $rowsHtml .= "<td class=\"wrap\">" . htmlspecialchars($service, ENT_QUOTES, 'UTF-8') . "</td>";
                $rowsHtml .= "<td>" . number_format($quantity) . "</td>\n";
                $rowsHtml .= "            <td><span class=\"adm-badge {$badgeClass}\">{$stText}</span></td>\n";
                $rowsHtml .= "          </tr>";
            }

            if ($rowsHtml !== '') {
                // Replace tbody in latest orders table
                $tablePattern = '#(<div class="dash-card-head">\s*<h2>ออเดอร์ล่าสุด</h2>.*?<table class="adm-table">.*?<tbody>)(.*?)(</tbody>)#su';
                if (preg_match($tablePattern, $html)) {
                    $html = preg_replace($tablePattern, '${1}' . $rowsHtml . "\n        \${3}", $html, 1);
                }
            }
        }

        // 2. Live KPI Counters
        $cntClients = (int)@$db->querySingle("SELECT count(*) FROM clients");
        $cntOrders = (int)@$db->querySingle("SELECT count(*) FROM orders");
        $sumRev = (float)@$db->querySingle("SELECT coalesce(sum(amount), 0) FROM payments WHERE status = 'paid'");
        $cntPendingPay = (int)@$db->querySingle("SELECT count(*) FROM payments WHERE status = 'pending'");

        // Replace KPI values in the first kpi-grid
        $html = preg_replace('#(<span>ลูกค้า</span><b>)(\d+)(</b>)#u', '${1}' . $cntClients . '${3}', $html, 1);
        $html = preg_replace('#(<span>ออเดอร์</span><b>)(\d+)(</b>)#u', '${1}' . $cntOrders . '${3}', $html, 1);
        $html = preg_replace('#(<span>รายได้ \(บาท\)</span><b>)([\d,]+)(</b>)#u', '${1}' . number_format(round($sumRev)) . '${3}', $html, 1);
        $html = preg_replace('#(<span>เติมเงินรอตรวจ</span><b>)(\d+)(</b>)#u', '${1}' . $cntPendingPay . '${3}', $html, 1);

        // 3. Pending Payments widget ("เติมเงินรออนุมัติ")
        $payRes = @$db->query("SELECT id, client, amount, method FROM payments WHERE status = 'pending' ORDER BY id DESC LIMIT 6");
        $payHtml = '';
        if ($payRes) {
            while ($p = $payRes->fetchArray(SQLITE3_ASSOC)) {
                $pid = (int)$p['id'];
                $pcl = (string)($p['client'] ?? '');
                $pamt = (float)($p['amount'] ?? 0);
                $payHtml .= "\n    <div class=\"queue-item\">\n";
                $payHtml .= "      <span>#{$pid} " . htmlspecialchars($pcl, ENT_QUOTES, 'UTF-8') . " · ฿" . number_format($pamt, 2) . "</span>\n";
                $payHtml .= "      <a class=\"la-btn la-btn-mini\" href=\"/admin/payments\">ตรวจ</a>\n";
                $payHtml .= "    </div>";
            }
        }
        if ($payHtml === '') {
            $payHtml = "\n    <p class=\"adm-empty\">ไม่มีรายการค้าง</p>\n  ";
        }
        $payWidgetPattern = '#(<div class="dash-card-head">\s*<h2>เติมเงินรออนุมัติ</h2>\s*<a href="/admin/payments">ทั้งหมด</a>\s*</div>)(.*?)(</article>)#su';
        if (preg_match($payWidgetPattern, $html)) {
            $html = preg_replace($payWidgetPattern, '${1}' . $payHtml . "\${3}", $html, 1);
        }

        // 4. Open Tickets widget ("ตั๋วที่เปิดอยู่")
        $tickRes = @$db->query("SELECT id, client, subject, status FROM tickets WHERE status in ('open', 'answered') ORDER BY id DESC LIMIT 6");
        $tickHtml = '';
        if ($tickRes) {
            while ($t = $tickRes->fetchArray(SQLITE3_ASSOC)) {
                $tid = (int)$t['id'];
                $tcl = (string)($t['client'] ?? '');
                $tsub = (string)($t['subject'] ?? '');
                $tickHtml .= "\n    <div class=\"queue-item\">\n";
                $tickHtml .= "      <span>#{$tid} " . htmlspecialchars($tsub, ENT_QUOTES, 'UTF-8') . " · " . htmlspecialchars($tcl, ENT_QUOTES, 'UTF-8') . "</span>\n";
                $tickHtml .= "      <a class=\"la-btn la-btn-mini\" href=\"/admin/tickets\">ตอบ</a>\n";
                $tickHtml .= "    </div>";
            }
        }
        if ($tickHtml === '') {
            $tickHtml = "\n    <p class=\"adm-empty\">ไม่มีตั๋วค้าง</p>\n  ";
        }
        $tickWidgetPattern = '#(<div class="dash-card-head">\s*<h2>ตั๋วที่เปิดอยู่</h2>\s*<a href="/admin/tickets">ตอบตั๋ว</a>\s*</div>)(.*?)(</article>)#su';
        if (preg_match($tickWidgetPattern, $html)) {
            $html = preg_replace($tickWidgetPattern, '${1}' . $tickHtml . "\${3}", $html, 1);
        }

        $db->close();
    } catch (\Throwable $e) {}

    return $html;
}
