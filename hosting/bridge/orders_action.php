<?php
/**
 * Direct Live Execution Engine for Admin Order Actions:
 * - บันทึก (Status change)
 * - ส่ง API (API Resend with Intelligent Auto-Fallback)
 * - ดึงสถานะ (Status & Progress Sync)
 * - คืนเงิน (Safe Balance Refund & Cancellation)
 */

declare(strict_types=1);

function la_handle_admin_order_action(string $path, string $method): void {
    if ($method !== 'POST' || !preg_match('#^/admin/orders/(\d+)/(status|resend|sync|refund)#', $path, $m)) {
        return;
    }

    $oid = (int)$m[1];
    $actionType = $m[2];

    $dbFiles = [
        __DIR__ . '/.la-db-restore-latest.db',
        __DIR__ . '/.la-db-restore-d1qyg5az73cs4unx8jl9trbw.db',
    ];
    $activeDb = null;
    $db = null;
    foreach ($dbFiles as $f) {
        if (file_exists($f) && is_writable($f)) {
            try {
                $db = new SQLite3($f, SQLITE3_OPEN_READWRITE);
                $db->busyTimeout(10000);
                $activeDb = $f;
                break;
            } catch (\Throwable $e) {}
        }
    }
    if (!$db) {
        foreach ($dbFiles as $f) {
            if (file_exists($f)) {
                try {
                    $db = new SQLite3($f, SQLITE3_OPEN_READWRITE);
                    $db->busyTimeout(10000);
                    $activeDb = $f;
                    break;
                } catch (\Throwable $e) {}
            }
        }
    }

    // Provider config
    $provKey = '691eaf10c7412219464b2d67d4082c24';
    $provUrl = 'https://justanotherpanel.com/api/v2';
    if ($db) {
        $pRes = $db->query("SELECT api_key, api_url FROM providers WHERE id=1 OR name LIKE '%justanotherpanel%' LIMIT 1");
        if ($pRow = $pRes->fetchArray(SQLITE3_ASSOC)) {
            if (!empty($pRow['api_key'])) $provKey = (string)$pRow['api_key'];
            if (!empty($pRow['api_url'])) $provUrl = (string)$pRow['api_url'];
        }
    }

    $ovFile = __DIR__ . '/orders_override.json';
    $overrides = is_file($ovFile) ? (json_decode((string)file_get_contents($ovFile), true) ?: []) : [];

    // Helper: JAP API call
    $japCall = function(array $params) use ($provUrl, $provKey): array {
        $params['key'] = $provKey;
        $ch = curl_init($provUrl);
        curl_setopt_array($ch, [
            CURLOPT_POST => true,
            CURLOPT_POSTFIELDS => http_build_query($params),
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_TIMEOUT => 25,
            CURLOPT_SSL_VERIFYPEER => false,
            CURLOPT_SSL_VERIFYHOST => 0,
            CURLOPT_USERAGENT => 'LikesAuto-AdminAction/2.0',
        ]);
        $raw = curl_exec($ch);
        curl_close($ch);
        $dec = json_decode((string)$raw, true);
        return is_array($dec) ? $dec : ['error' => 'invalid_response', 'raw' => substr((string)$raw, 0, 150)];
    };

    // Helper to sync DB copies
    $syncDb = function() use ($activeDb, $dbFiles) {
        if ($activeDb && file_exists($activeDb)) {
            foreach ($dbFiles as $f) {
                if ($f !== $activeDb && file_exists($f)) {
                    @copy($activeDb, $f);
                }
            }
        }
    };

    // ── 1. ACTION: STATUS (บันทึกเปลี่ยนสถานะ) ──
    if ($actionType === 'status') {
        $newStatus = trim((string)($_POST['status'] ?? 'processing'));
        $lbls = [
            'pending' => 'รอส่ง',
            'processing' => 'กำลังทำ',
            'completed' => 'สำเร็จ',
            'partial' => 'บางส่วน',
            'canceled' => 'ยกเลิก',
        ];
        $lbl = $lbls[$newStatus] ?? $newStatus;

        if ($db) {
            $st = $db->prepare("UPDATE orders SET status = :st WHERE id = :oid");
            $st->bindValue(':st', $newStatus, SQLITE3_TEXT);
            $st->bindValue(':oid', $oid, SQLITE3_INTEGER);
            $st->execute();
            $syncDb();
        }

        $overrides[$oid] = array_merge($overrides[$oid] ?? [], [
            'status_cls' => $newStatus,
            'status_lbl' => $lbl,
        ]);
        if ($newStatus === 'completed') {
            $overrides[$oid]['remains'] = '0';
            $overrides[$oid]['prog_pct'] = 100;
        }
        file_put_contents($ovFile, json_encode($overrides, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE));

        $msg = 'บันทึกสถานะออเดอร์ #' . $oid . ' เป็น ' . $lbl . ' เรียบร้อยแล้ว';
        header('Location: /admin/orders?ok=' . urlencode($msg), true, 303);
        exit;
    }

    // ── 2. ACTION: RESEND (ส่ง API พร้อม Auto-Fallback Service) ──
    if ($actionType === 'resend') {
        $order = null;
        if ($db) {
            $st = $db->prepare("
                SELECT o.*, s.api_service, s.platform, s.name as svc_name, s.rate as svc_rate, s.cost_rate, s.min_qty, s.max_qty
                FROM orders o
                LEFT JOIN services s ON o.service_id = s.id
                WHERE o.id = :oid
            ");
            $st->bindValue(':oid', $oid, SQLITE3_INTEGER);
            $r = $st->execute();
            if ($row = $r->fetchArray(SQLITE3_ASSOC)) {
                $order = $row;
            }
        }

        if (!$order) {
            header('Location: /admin/orders?err=' . urlencode('ไม่พบข้อมูลออเดอร์ #' . $oid), true, 303);
            exit;
        }

        $qty = (int)$order['quantity'];
        $link = (string)($order['link'] ?? '');
        $apiSvc = trim((string)($order['api_service'] ?? ''));

        $payload = [
            'action' => 'add',
            'service' => $apiSvc,
            'quantity' => $qty,
        ];
        if (!empty($link)) $payload['link'] = $link;
        if (!empty($order['comments'])) $payload['comments'] = $order['comments'];

        $apiRes = null;
        if (!empty($apiSvc)) {
            $apiRes = $japCall($payload);
        }

        $apiOid = $apiRes['order'] ?? null;
        $errStr = isset($apiRes['error']) ? (is_array($apiRes['error']) ? json_encode($apiRes['error']) : (string)$apiRes['error']) : '';

        // If direct API call succeeded
        if (!empty($apiOid)) {
            if ($db) {
                $stUp = $db->prepare("UPDATE orders SET status = 'processing', api_orderid = :aoid, api_error = '-' WHERE id = :oid");
                $stUp->bindValue(':aoid', (string)$apiOid, SQLITE3_TEXT);
                $stUp->bindValue(':oid', $oid, SQLITE3_INTEGER);
                $stUp->execute();
                $syncDb();
            }

            $overrides[$oid] = array_merge($overrides[$oid] ?? [], [
                'api_id' => (string)$apiOid,
                'status_cls' => 'processing',
                'status_lbl' => 'กำลังทำ',
                'err' => '',
                'has_err' => false,
            ]);
            file_put_contents($ovFile, json_encode($overrides, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE));

            $msg = 'ส่งออเดอร์ #' . $oid . ' ไปยัง API สำเร็จ (รหัส API #' . $apiOid . ')';
            header('Location: /admin/orders?ok=' . urlencode($msg), true, 303);
            exit;
        }

        // Auto-Fallback: If 'Incorrect service ID' or missing service ID
        if (strpos($errStr, 'Incorrect service ID') !== false || empty($apiSvc)) {
            if ($db) {
                // Find closest active service
                $targetRate = (float)($order['svc_rate'] ?? 0);
                $targetPlatform = strtolower(trim((string)($order['platform'] ?? '')));
                $targetName = strtolower(trim((string)($order['svc_name'] ?? $order['service'] ?? '')));

                $keywords = [];
                foreach (['likes', 'views', 'followers', 'subscribers', 'comments', 'shares', 'reposts', 'members', 'hours'] as $kw) {
                    if (strpos($targetName, $kw) !== false) $keywords[] = $kw;
                }
                $subtypes = ['auto', 'comment', 'live', 'story', 'save', 'share', 'repost'];
                $excludeSubtypes = [];
                foreach ($subtypes as $stype) {
                    if (strpos($targetName, $stype) === false) $excludeSubtypes[] = $stype;
                }

                $stC = $db->prepare("
                    SELECT id, name, platform, rate, cost_rate, api_service, min_qty, max_qty
                    FROM services
                    WHERE LOWER(platform) = :plat
                      AND api_service IS NOT NULL
                      AND api_service != ''
                      AND api_service != :orig_api
                      AND status = 'active'
                ");
                $stC->bindValue(':plat', $targetPlatform, SQLITE3_TEXT);
                $stC->bindValue(':orig_api', $apiSvc, SQLITE3_TEXT);
                $resC = $stC->execute();

                $matched = [];
                while ($c = $resC->fetchArray(SQLITE3_ASSOC)) {
                    $cName = strtolower((string)$c['name']);
                    if (!empty($keywords)) {
                        $hasKw = false;
                        foreach ($keywords as $kw) {
                            if (strpos($cName, $kw) !== false) { $hasKw = true; break; }
                        }
                        if (!$hasKw) continue;
                    }
                    $hasEx = false;
                    foreach ($excludeSubtypes as $ex) {
                        if (strpos($cName, $ex) !== false) { $hasEx = true; break; }
                    }
                    if ($hasEx) continue;

                    $minQ = (int)($c['min_qty'] ?? 0);
                    $maxQ = (int)($c['max_qty'] ?? 0);
                    if ($minQ > 0 && $qty < $minQ) continue;
                    if ($maxQ > 0 && $qty > $maxQ) continue;

                    $diff = abs((float)($c['rate'] ?? 0) - $targetRate);
                    $matched[] = ['diff' => $diff, 'item' => $c];
                }

                usort($matched, fn($a, $b) => $a['diff'] <=> $b['diff']);

                // Try top candidates
                foreach (array_slice($matched, 0, 8) as $mCand) {
                    $cand = $mCand['item'];
                    $candApiId = (string)$cand['api_service'];
                    $fbPayload = [
                        'action' => 'add',
                        'service' => $candApiId,
                        'quantity' => $qty,
                    ];
                    if (!empty($link)) $fbPayload['link'] = $link;
                    if (!empty($order['comments'])) $fbPayload['comments'] = $order['comments'];

                    $fbRes = $japCall($fbPayload);
                    if (!empty($fbRes['order'])) {
                        $fbOid = (string)$fbRes['order'];
                        
                        $stUp = $db->prepare("UPDATE orders SET status = 'processing', api_orderid = :aoid, api_error = '-' WHERE id = :oid");
                        $stUp->bindValue(':aoid', $fbOid, SQLITE3_TEXT);
                        $stUp->bindValue(':oid', $oid, SQLITE3_INTEGER);
                        $stUp->execute();

                        if (!empty($order['service_id'])) {
                            $stS = $db->prepare("UPDATE services SET api_service = :cand_api WHERE id = :sid");
                            $stS->bindValue(':cand_api', $candApiId, SQLITE3_TEXT);
                            $stS->bindValue(':sid', (int)$order['service_id'], SQLITE3_INTEGER);
                            $stS->execute();
                        }
                        $syncDb();

                        $overrides[$oid] = array_merge($overrides[$oid] ?? [], [
                            'api_id' => $fbOid,
                            'provider_svc' => $candApiId,
                            'status_cls' => 'processing',
                            'status_lbl' => 'กำลังทำ',
                            'err' => '',
                            'has_err' => false,
                        ]);
                        file_put_contents($ovFile, json_encode($overrides, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE));

                        $msg = 'ส่งออเดอร์ #' . $oid . ' สำเร็จโดยใช้บริการทดแทน #' . $candApiId . ' (รหัส API #' . $fbOid . ')';
                        header('Location: /admin/orders?ok=' . urlencode($msg), true, 303);
                        exit;
                    }
                }
            }
        }

        // If all attempts failed
        $cleanErr = substr($errStr ?: 'ส่งไม่สำเร็จ', 0, 200);
        if ($db) {
            $stErr = $db->prepare("UPDATE orders SET api_error = :err, status = 'pending' WHERE id = :oid");
            $stErr->bindValue(':err', $cleanErr, SQLITE3_TEXT);
            $stErr->bindValue(':oid', $oid, SQLITE3_INTEGER);
            $stErr->execute();
            $syncDb();
        }

        $overrides[$oid] = array_merge($overrides[$oid] ?? [], [
            'status_cls' => 'pending',
            'status_lbl' => 'รอส่ง',
            'err' => $cleanErr,
            'has_err' => true,
        ]);
        file_put_contents($ovFile, json_encode($overrides, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE));

        header('Location: /admin/orders?err=' . urlencode('ส่ง API ไม่สำเร็จ: ' . $cleanErr), true, 303);
        exit;
    }

    // ── 3. ACTION: SYNC (ดึงสถานะล่าสุดจาก Provider API) ──
    if ($actionType === 'sync') {
        $apiId = '';
        if ($db) {
            $st = $db->prepare("SELECT api_orderid, client, charge, quantity, refunded FROM orders WHERE id = :oid");
            $st->bindValue(':oid', $oid, SQLITE3_INTEGER);
            $res = $st->execute();
            if ($row = $res->fetchArray(SQLITE3_ASSOC)) {
                $apiId = trim((string)($row['api_orderid'] ?? ''));
                $ordData = $row;
            }
        }
        if (empty($apiId)) {
            $apiId = (string)($overrides[$oid]['api_id'] ?? '');
        }

        if (empty($apiId) || $apiId === '-') {
            header('Location: /admin/orders?err=' . urlencode('ออเดอร์ #' . $oid . ' ยังไม่มีรหัส API'), true, 303);
            exit;
        }

        $stRes = $japCall([
            'action' => 'status',
            'order' => $apiId,
        ]);

        if (!empty($stRes['status'])) {
            $stRaw = strtolower(trim((string)$stRes['status']));
            $startCount = (string)($stRes['start_count'] ?? '-');
            $remains = (string)($stRes['remains'] ?? '-');

            $mappedCls = 'processing';
            $mappedLbl = 'กำลังทำ';
            $prog = 0;
            if (in_array($stRaw, ['completed', 'complete', 'success'], true)) {
                $mappedCls = 'completed';
                $mappedLbl = 'สำเร็จ';
                $prog = 100;
            } elseif ($stRaw === 'partial') {
                $mappedCls = 'partial';
                $mappedLbl = 'บางส่วน';
                $prog = 50;
            } elseif (in_array($stRaw, ['canceled', 'cancelled', 'refunded'], true)) {
                $mappedCls = 'canceled';
                $mappedLbl = 'ยกเลิก';
            }

            if ($db) {
                $stUp = $db->prepare("UPDATE orders SET status = :st, start_count = :sc, remains = :rem, api_error = '-' WHERE id = :oid");
                $stUp->bindValue(':st', $mappedCls, SQLITE3_TEXT);
                $stUp->bindValue(':sc', $startCount, SQLITE3_TEXT);
                $stUp->bindValue(':rem', $remains, SQLITE3_TEXT);
                $stUp->bindValue(':oid', $oid, SQLITE3_INTEGER);
                $stUp->execute();
                $syncDb();
            }

            $overrides[$oid] = array_merge($overrides[$oid] ?? [], [
                'api_id' => $apiId,
                'status_cls' => $mappedCls,
                'status_lbl' => $mappedLbl,
                'remains' => $remains,
                'start' => $startCount,
                'done' => '0',
                'prog_pct' => $prog,
                'err' => '',
                'has_err' => false,
            ]);
            file_put_contents($ovFile, json_encode($overrides, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE));

            $msg = 'ดึงสถานะออเดอร์ #' . $oid . ' สำเร็จ: ' . $stRes['status'] . ' (คงเหลือ ' . $remains . ')';
            header('Location: /admin/orders?ok=' . urlencode($msg), true, 303);
            exit;
        }

        $err = $stRes['error'] ?? 'ดึงสถานะไม่สำเร็จ';
        header('Location: /admin/orders?err=' . urlencode('ดึงสถานะไม่สำเร็จ: ' . $err), true, 303);
        exit;
    }

    // ── 4. ACTION: REFUND (คืนเงินและยกเลิกออเดอร์) ──
    if ($actionType === 'refund') {
        $order = null;
        if ($db) {
            $st = $db->prepare("SELECT client, charge, refunded, status FROM orders WHERE id = :oid");
            $st->bindValue(':oid', $oid, SQLITE3_INTEGER);
            $res = $st->execute();
            if ($row = $res->fetchArray(SQLITE3_ASSOC)) {
                $order = $row;
            }
        }

        if (!$order) {
            header('Location: /admin/orders?err=' . urlencode('ไม่พบออเดอร์ #' . $oid), true, 303);
            exit;
        }

        if (!empty($order['refunded'])) {
            header('Location: /admin/orders?err=' . urlencode('ออเดอร์ #' . $oid . ' ได้รับการคืนเงินไปแล้ว'), true, 303);
            exit;
        }

        $charge = (float)($order['charge'] ?? 0);
        $client = (string)($order['client'] ?? '');

        if ($charge > 0 && !empty($client) && $db) {
            $stRef = $db->prepare("UPDATE clients SET balance = balance + :amt WHERE username = :u");
            $stRef->bindValue(':amt', $charge, SQLITE3_FLOAT);
            $stRef->bindValue(':u', $client, SQLITE3_TEXT);
            $stRef->execute();

            $stOrd = $db->prepare("UPDATE orders SET status = 'canceled', refunded = 1 WHERE id = :oid");
            $stOrd->bindValue(':oid', $oid, SQLITE3_INTEGER);
            $stOrd->execute();
            $syncDb();
        }

        $overrides[$oid] = array_merge($overrides[$oid] ?? [], [
            'status_cls' => 'canceled',
            'status_lbl' => 'ยกเลิก',
        ]);
        file_put_contents($ovFile, json_encode($overrides, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE));

        $msg = 'คืนเงิน ฿' . number_format($charge, 2) . ' เข้ากระเป๋าลูกค้า @' . $client . ' และยกเลิกออเดอร์ #' . $oid . ' เรียบร้อยแล้ว';
        header('Location: /admin/orders?ok=' . urlencode($msg), true, 303);
        exit;
    }
}
