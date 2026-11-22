<?php
/**
 * Likes-Auto Native Automated Cron Engine (Visperhost Server Edition)
 * 
 * Features:
 * - Runs every 1 minute via DirectAdmin Linux crontab / PHP CLI / Webhook
 * - Auto-dispatches all pending orders to upstream providers (JustAnotherPanel API)
 * - Auto-Fallback Engine: If service ID is invalid/deprecated ('Incorrect service ID'),
 *   automatically selects the closest matching active service by platform/type & price rate,
 *   updates the order & service mapping, and dispatches seamlessly!
 * - Auto-syncs status (remains, start count, progress) for active orders
 * - Auto-refunds canceled/partial orders
 * - Auto-syncs provider balance
 * - Pings Render to keep upstream FastAPI warm & synchronized
 */

declare(strict_types=1);

// Increase execution limit for batch processing
@set_time_limit(180);
@ini_set('memory_limit', '256M');

// 1. Authenticate (CLI argument or GET/POST parameter or HTTP Header)
$cliKey = '';
if (PHP_SAPI === 'cli' && !empty($argv)) {
    foreach ($argv as $arg) {
        if (strpos($arg, 'key=') === 0) {
            $cliKey = substr($arg, 4);
        }
    }
}
$reqKey = $_GET['key'] ?? $_POST['key'] ?? $_SERVER['HTTP_X_CRON_KEY'] ?? $cliKey;
$validKeys = ['likesauto2026', 'cron_likesauto_secret_2026'];
if (!in_array($reqKey, $validKeys, true)) {
    http_response_code(401);
    header('Content-Type: application/json; charset=utf-8');
    echo json_encode(['ok' => false, 'error' => 'unauthorized', 'hint' => 'Pass ?key=likesauto2026'], JSON_UNESCAPED_UNICODE);
    exit;
}

// 2. Open SQLite Databases
$dbFiles = [
    __DIR__ . '/.la-db-restore-latest.db',
    __DIR__ . '/.la-db-restore-d1qyg5az73cs4unx8jl9trbw.db',
];

$activeDbFile = null;
$db = null;

foreach ($dbFiles as $f) {
    if (file_exists($f) && is_writable($f)) {
        try {
            $db = new SQLite3($f, SQLITE3_OPEN_READWRITE);
            $db->busyTimeout(10000);
            $activeDbFile = $f;
            break;
        } catch (\Throwable $e) {
            // try next
        }
    }
}

if (!$db) {
    // If not writable or not found, try fallback open
    foreach ($dbFiles as $f) {
        if (file_exists($f)) {
            try {
                $db = new SQLite3($f, SQLITE3_OPEN_READWRITE);
                $db->busyTimeout(10000);
                $activeDbFile = $f;
                break;
            } catch (\Throwable $e) {}
        }
    }
}

if (!$db) {
    header('Content-Type: application/json; charset=utf-8');
    echo json_encode(['ok' => false, 'error' => 'database_not_accessible'], JSON_UNESCAPED_UNICODE);
    exit;
}

// Ensure schema has api_status column
@$db->exec("ALTER TABLE orders ADD COLUMN api_status TEXT");

// Function to sync writes to both database copies
function la_sync_db_copies(string $activeFile, array $allFiles): void {
    if (!file_exists($activeFile)) return;
    foreach ($allFiles as $alt) {
        if ($alt !== $activeFile && file_exists($alt)) {
            @copy($activeFile, $alt);
        }
    }
}

// Helper: Call SMM Provider API
function la_jap_api_call(string $url, array $params, int $timeout = 25): array {
    $ch = curl_init($url);
    curl_setopt_array($ch, [
        CURLOPT_POST => true,
        CURLOPT_POSTFIELDS => http_build_query($params),
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_TIMEOUT => $timeout,
        CURLOPT_SSL_VERIFYPEER => false,
        CURLOPT_SSL_VERIFYHOST => 0,
        CURLOPT_USERAGENT => 'LikesAuto-CronEngine/2.0',
    ]);
    $raw = curl_exec($ch);
    $err = curl_error($ch);
    curl_close($ch);
    if ($err || !$raw) {
        return ['error' => 'curl_error: ' . $err];
    }
    $decoded = json_decode((string)$raw, true);
    return is_array($decoded) ? $decoded : ['error' => 'invalid_json', 'raw' => substr((string)$raw, 0, 200)];
}

// Helper: Find intelligent fallback service
function la_find_fallback_service(SQLite3 $db, array $order, array $svc, array $provider): ?array {
    $targetRate = (float)($svc['rate'] ?? 0);
    $targetPlatform = strtolower(trim((string)($svc['platform'] ?? '')));
    $targetName = strtolower(trim((string)($svc['name'] ?? '')));
    $qty = (int)($order['quantity'] ?? 0);
    $origApiSvc = (string)($svc['api_service'] ?? '');

    $keywords = [];
    foreach (['likes', 'views', 'followers', 'subscribers', 'comments', 'shares', 'reposts', 'members', 'hours', 'members'] as $kw) {
        if (strpos($targetName, $kw) !== false) {
            $keywords[] = $kw;
        }
    }

    $subtypes = ['auto', 'comment', 'live', 'story', 'save', 'share', 'repost'];
    $excludeSubtypes = [];
    foreach ($subtypes as $st) {
        if (strpos($targetName, $st) === false) {
            $excludeSubtypes[] = $st;
        }
    }

    $stmt = $db->prepare("
        SELECT id, name, platform, rate, cost_rate, api_service, min_qty, max_qty
        FROM services
        WHERE provider_id = :pid
          AND LOWER(platform) = :plat
          AND api_service IS NOT NULL
          AND api_service != ''
          AND api_service != :orig_api
          AND status = 'active'
    ");
    $stmt->bindValue(':pid', (int)$provider['id'], SQLITE3_INTEGER);
    $stmt->bindValue(':plat', $targetPlatform, SQLITE3_TEXT);
    $stmt->bindValue(':orig_api', $origApiSvc, SQLITE3_TEXT);
    $res = $stmt->execute();

    $matched = [];
    while ($row = $res->fetchArray(SQLITE3_ASSOC)) {
        $cName = strtolower((string)$row['name']);
        
        // Keyword filter
        if (!empty($keywords)) {
            $hasKw = false;
            foreach ($keywords as $kw) {
                if (strpos($cName, $kw) !== false) {
                    $hasKw = true;
                    break;
                }
            }
            if (!$hasKw) continue;
        }

        // Subtype exclusion
        $hasExclude = false;
        foreach ($excludeSubtypes as $ex) {
            if (strpos($cName, $ex) !== false) {
                $hasExclude = true;
                break;
            }
        }
        if ($hasExclude) continue;

        // Country exclusion
        $countries = ['brazil', 'russia', 'ukraine', 'turkey', 'indonesia', 'india'];
        $hasTargetCountry = false;
        foreach ($countries as $co) {
            if (strpos($targetName, $co) !== false) {
                $hasTargetCountry = true;
                break;
            }
        }
        if (!$hasTargetCountry) {
            $hasCandCountry = false;
            foreach ($countries as $co) {
                if (strpos($cName, $co) !== false) {
                    $hasCandCountry = true;
                    break;
                }
            }
            if ($hasCandCountry) continue;
        }

        // Quantity bounds
        $minQ = (int)($row['min_qty'] ?? 0);
        $maxQ = (int)($row['max_qty'] ?? 0);
        if ($minQ > 0 && $qty < $minQ) continue;
        if ($maxQ > 0 && $qty > $maxQ) continue;

        $diff = abs((float)($row['rate'] ?? 0) - $targetRate);
        $matched[] = ['diff' => $diff, 'item' => $row];
    }

    usort($matched, fn($a, $b) => $a['diff'] <=> $b['diff']);

    // Test top candidate services against provider API
    foreach (array_slice($matched, 0, 8) as $candWrap) {
        $cand = $candWrap['item'];
        $candApiId = (string)$cand['api_service'];
        $testPayload = [
            'key' => $provider['api_key'],
            'action' => 'add',
            'service' => $candApiId,
            'quantity' => $qty,
        ];
        if (!empty($order['link'])) $testPayload['link'] = $order['link'];
        if (!empty($order['comments'])) $testPayload['comments'] = $order['comments'];

        $apiRes = la_jap_api_call($provider['api_url'], $testPayload, 20);
        if (!empty($apiRes['order'])) {
            return [
                'order_id' => (string)$apiRes['order'],
                'fallback_service_id' => $candApiId,
                'fallback_name' => $cand['name'],
                'fallback_cost' => $cand['cost_rate'] ?? 0,
            ];
        }
    }

    return null;
}

// ── 3. GET DEFAULT PROVIDER (JustAnotherPanel) ──
$provider = null;
$provRes = $db->query("SELECT * FROM providers WHERE id = 1 OR name LIKE '%justanotherpanel%' LIMIT 1");
if ($provRow = $provRes->fetchArray(SQLITE3_ASSOC)) {
    $provider = $provRow;
}
if (!$provider) {
    $provider = [
        'id' => 1,
        'name' => 'justanotherpanel.com',
        'api_url' => 'https://justanotherpanel.com/api/v2',
        'api_key' => '691eaf10c7412219464b2d67d4082c24',
    ];
}

$results = [
    'ok' => true,
    'timestamp' => date('Y-m-d H:i:s'),
    'orders_sent' => 0,
    'orders_synced' => 0,
    'orders_failed' => 0,
    'dispatches' => [],
    'syncs' => [],
];

// ── 4. DISPATCH PENDING ORDERS (IDEMPOTENT & MULTI-LAYER GUARDED) ──
$dispatchLockFp = @fopen(sys_get_temp_dir() . '/la_cron_dispatch.lock', 'c+');
$hasDispatchLock = ($dispatchLockFp && @flock($dispatchLockFp, LOCK_EX | LOCK_NB));

if ($hasDispatchLock) {
    // Auto-recover any order stuck in 'SENDING' for > 5 minutes
    @$db->exec("UPDATE orders SET api_orderid = NULL, api_error = 'sending_timeout_recovered' WHERE api_orderid = 'SENDING' AND (created_at <= datetime('now', '-5 minutes'))");

    // Query pending orders with a 2-minute grace period to prevent race conditions with Render
    $pendingSql = "
        SELECT o.*, s.api_service, s.platform, s.name as svc_name, s.rate as svc_rate, s.category, s.cost_rate
        FROM orders o
        LEFT JOIN services s ON o.service_id = s.id
        WHERE (o.api_orderid IS NULL OR o.api_orderid = '' OR o.api_orderid = '-')
          AND o.status NOT IN ('completed', 'canceled', 'refunded')
          AND (o.created_at IS NULL OR o.created_at <= datetime('now', '-2 minutes'))
        ORDER BY o.id ASC
    ";
    $pendRes = $db->query($pendingSql);
    $pendingOrders = [];
    while ($row = $pendRes->fetchArray(SQLITE3_ASSOC)) {
        $pendingOrders[] = $row;
    }

    foreach ($pendingOrders as $ord) {
        $oid = (int)$ord['id'];
        $apiSvcId = trim((string)($ord['api_service'] ?? ''));
        $qty = (int)$ord['quantity'];
        $link = (string)($ord['link'] ?? '');
        $serviceId = (int)($ord['service_id'] ?? 0);

        // Layer 1: Atomic Row Claim Token
        $stmtClaim = $db->prepare("UPDATE orders SET api_orderid = 'SENDING', api_status = 'Pending' WHERE id = :oid AND (api_orderid IS NULL OR api_orderid = '' OR api_orderid = '-')");
        $stmtClaim->bindValue(':oid', $oid, SQLITE3_INTEGER);
        $stmtClaim->execute();
        if ($db->changes() !== 1) {
            continue; // Claimed or sent by another worker/thread
        }

        // Layer 2: 10-Minute Identical Order Deduplication Guard
        if (!empty($link) && $serviceId > 0 && $qty > 0) {
            $stmtDup = $db->prepare("
                SELECT id, api_orderid FROM orders
                WHERE service_id = :sid AND quantity = :qty AND link = :link
                  AND id != :oid
                  AND api_orderid IS NOT NULL AND api_orderid != '' AND api_orderid NOT IN ('-', 'SENDING')
                  AND created_at >= datetime('now', '-10 minutes')
                ORDER BY id DESC LIMIT 1
            ");
            $stmtDup->bindValue(':sid', $serviceId, SQLITE3_INTEGER);
            $stmtDup->bindValue(':qty', $qty, SQLITE3_INTEGER);
            $stmtDup->bindValue(':link', $link, SQLITE3_TEXT);
            $stmtDup->bindValue(':oid', $oid, SQLITE3_INTEGER);
            $dupRes = $stmtDup->execute();
            if ($dupRow = $dupRes->fetchArray(SQLITE3_ASSOC)) {
                $dupApiOid = (string)$dupRow['api_orderid'];
                $stmtUp = $db->prepare("UPDATE orders SET status = 'processing', api_orderid = :aoid, api_status = 'Pending', api_error = :err WHERE id = :oid");
                $stmtUp->bindValue(':aoid', $dupApiOid, SQLITE3_TEXT);
                $stmtUp->bindValue(':err', 'duplicate_prevented_linked_to_order_' . $dupRow['id'], SQLITE3_TEXT);
                $stmtUp->bindValue(':oid', $oid, SQLITE3_INTEGER);
                $stmtUp->execute();

                $results['orders_sent']++;
                $results['dispatches'][] = [
                    'order_id' => $oid,
                    'api_orderid' => $dupApiOid,
                    'status' => 'processing',
                    'duplicate_prevented' => true
                ];
                continue;
            }
        }
        
        $payload = [
            'key' => $provider['api_key'],
            'action' => 'add',
            'service' => $apiSvcId,
            'quantity' => $qty,
        ];
        if (!empty($link)) $payload['link'] = $link;
        if (!empty($ord['comments'])) $payload['comments'] = $ord['comments'];

        $apiRes = null;
        if (!empty($apiSvcId)) {
            $apiRes = la_jap_api_call($provider['api_url'], $payload);
        }

        $apiOrderId = $apiRes['order'] ?? null;
        $errStr = isset($apiRes['error']) ? (is_array($apiRes['error']) ? json_encode($apiRes['error']) : (string)$apiRes['error']) : '';

        // If successful directly
        if (!empty($apiOrderId)) {
            $stmtUp = $db->prepare("UPDATE orders SET status = 'processing', api_orderid = :aoid, api_status = 'Pending', api_error = '-' WHERE id = :oid");
            $stmtUp->bindValue(':aoid', (string)$apiOrderId, SQLITE3_TEXT);
            $stmtUp->bindValue(':oid', $oid, SQLITE3_INTEGER);
            $stmtUp->execute();

            $results['orders_sent']++;
            $results['dispatches'][] = [
                'order_id' => $oid,
                'api_orderid' => (string)$apiOrderId,
                'service_id' => $apiSvcId,
                'status' => 'processing',
                'api_status' => 'Pending',
                'fallback' => false
            ];
            continue;
        }

        // Auto-Fallback: If service ID rejected ('Incorrect service ID') or missing
        if (strpos($errStr, 'Incorrect service ID') !== false || empty($apiSvcId)) {
            $svcData = [
                'id' => $ord['service_id'],
                'name' => $ord['svc_name'] ?? $ord['service'] ?? '',
                'platform' => $ord['platform'] ?? '',
                'rate' => $ord['svc_rate'] ?? 0,
                'api_service' => $apiSvcId,
            ];
            
            $fallback = la_find_fallback_service($db, $ord, $svcData, $provider);
            if ($fallback && !empty($fallback['order_id'])) {
                $fbOid = $fallback['order_id'];
                $fbSid = $fallback['fallback_service_id'];
                
                $stmtUp = $db->prepare("UPDATE orders SET status = 'processing', api_orderid = :aoid, api_status = 'Pending', api_error = '-' WHERE id = :oid");
                $stmtUp->bindValue(':aoid', (string)$fbOid, SQLITE3_TEXT);
                $stmtUp->bindValue(':oid', $oid, SQLITE3_INTEGER);
                $stmtUp->execute();

                // Update service record so future orders use working service
                if (!empty($ord['service_id'])) {
                    $stmtSvc = $db->prepare("UPDATE services SET api_service = :fb_sid WHERE id = :sid");
                    $stmtSvc->bindValue(':fb_sid', $fbSid, SQLITE3_TEXT);
                    $stmtSvc->bindValue(':sid', (int)$ord['service_id'], SQLITE3_INTEGER);
                    $stmtSvc->execute();
                }

                $results['orders_sent']++;
                $results['dispatches'][] = [
                    'order_id' => $oid,
                    'api_orderid' => (string)$fbOid,
                    'service_id' => $fbSid,
                    'status' => 'processing',
                    'fallback' => true,
                    'fallback_service_name' => $fallback['fallback_name']
                ];
                continue;
            }
        }

        // Record error on order and unlock row (reset api_orderid = NULL)
        $cleanErr = substr($errStr ?: 'dispatch_failed', 0, 300);
        $stmtErr = $db->prepare("UPDATE orders SET api_orderid = NULL, api_error = :err, status = 'pending' WHERE id = :oid");
        $stmtErr->bindValue(':err', $cleanErr, SQLITE3_TEXT);
        $stmtErr->bindValue(':oid', $oid, SQLITE3_INTEGER);
        $stmtErr->execute();

        $results['orders_failed']++;
        $results['dispatches'][] = [
            'order_id' => $oid,
            'status' => 'pending',
            'error' => $cleanErr
        ];
    }

    @flock($dispatchLockFp, LOCK_UN);
    @fclose($dispatchLockFp);
}

// ── 5. HIGH-SPEED BATCH AUTO-SYNC ORDER STATUSES ──
$syncSql = "
    SELECT id, api_orderid, client, charge, quantity, status, refunded
    FROM orders
    WHERE api_orderid IS NOT NULL AND api_orderid != '' AND api_orderid != '-'
      AND (
        status IN ('processing', 'pending', 'inprogress', 'partial')
        OR (status = 'completed' AND (remains IS NULL OR remains = '' OR remains > 0))
        OR id IN (SELECT id FROM orders WHERE api_orderid IS NOT NULL AND api_orderid != '' AND api_orderid != '-' ORDER BY id DESC LIMIT 50)
      )
    ORDER BY id DESC LIMIT 100
";
$syncRes = $db->query($syncSql);
$ordersToSync = [];
$chunkApiIds = [];
$chunkMap = [];

while ($row = $syncRes->fetchArray(SQLITE3_ASSOC)) {
    $ordersToSync[] = $row;
    $aId = trim((string)$row['api_orderid']);
    if ($aId !== '' && $aId !== '-') {
        $chunkApiIds[] = $aId;
        $chunkMap[$aId] = $row;
    }
}

if (!empty($chunkApiIds)) {
    $chunks = array_chunk($chunkApiIds, 100);
    foreach ($chunks as $cIds) {
        $batchRes = la_jap_api_call($provider['api_url'], [
            'key' => $provider['api_key'],
            'action' => 'status',
            'orders' => implode(',', $cIds),
        ]);

        if (is_array($batchRes)) {
            foreach ($cIds as $apiId) {
                if (!isset($batchRes[$apiId]) || !is_array($batchRes[$apiId])) continue;
                $stRes = $batchRes[$apiId];
                if (empty($stRes['status'])) continue;

                $sOrd = $chunkMap[$apiId] ?? null;
                if (!$sOrd) continue;
                $oid = (int)$sOrd['id'];

                $stRaw = strtolower(trim((string)$stRes['status']));
                $startCount = (string)($stRes['start_count'] ?? '0');
                $remains = (string)($stRes['remains'] ?? '0');

                $mappedStatus = 'processing';
                if (in_array($stRaw, ['completed', 'complete', 'success'], true)) {
                    $mappedStatus = 'completed';
                    $remains = '0';
                } elseif ($stRaw === 'partial') {
                    $mappedStatus = 'partial';
                } elseif (in_array($stRaw, ['canceled', 'cancelled', 'refunded'], true)) {
                    $mappedStatus = 'canceled';
                } elseif (in_array($stRaw, ['pending'], true)) {
                    $mappedStatus = 'pending';
                } elseif (in_array($stRaw, ['in progress', 'inprogress', 'processing'], true)) {
                    $mappedStatus = 'processing';
                }

                $stmtSt = $db->prepare("
                    UPDATE orders 
                    SET status = :st, api_status = :api_st, start_count = :sc, remains = :rem, api_error = '-'
                    WHERE id = :oid
                ");
                $stmtSt->bindValue(':st', $mappedStatus, SQLITE3_TEXT);
                $stmtSt->bindValue(':api_st', (string)($stRes['status'] ?? ''), SQLITE3_TEXT);
                $stmtSt->bindValue(':sc', $startCount, SQLITE3_TEXT);
                $stmtSt->bindValue(':rem', $remains, SQLITE3_TEXT);
                $stmtSt->bindValue(':oid', $oid, SQLITE3_INTEGER);
                $stmtSt->execute();

                // Handle Auto-Refund for canceled or partial
                if (($mappedStatus === 'canceled' || $mappedStatus === 'partial') && empty($sOrd['refunded'])) {
                    $refundAmt = 0.0;
                    $charge = (float)($sOrd['charge'] ?? 0);
                    $qty = (float)($sOrd['quantity'] ?? 0);
                    $rem = (float)$remains;

                    if ($mappedStatus === 'canceled') {
                        $refundAmt = $charge;
                    } elseif ($mappedStatus === 'partial' && $qty > 0 && $rem > 0) {
                        $refundAmt = round($charge * ($rem / $qty), 2);
                    }

                    if ($refundAmt > 0 && !empty($sOrd['client'])) {
                        $stmtRef = $db->prepare("UPDATE clients SET balance = balance + :amt WHERE username = :u");
                        $stmtRef->bindValue(':amt', $refundAmt, SQLITE3_FLOAT);
                        $stmtRef->bindValue(':u', (string)$sOrd['client'], SQLITE3_TEXT);
                        $stmtRef->execute();

                        $stmtMark = $db->prepare("UPDATE orders SET refunded = 1 WHERE id = :oid");
                        $stmtMark->bindValue(':oid', $oid, SQLITE3_INTEGER);
                        $stmtMark->execute();
                    }
                }

                $results['orders_synced']++;
                $results['syncs'][] = [
                    'order_id' => $oid,
                    'api_orderid' => $apiId,
                    'provider_status' => $stRes['status'],
                    'mapped_status' => $mappedStatus,
                    'remains' => $remains,
                    'start_count' => $startCount,
                ];
            }
        }
    }
}

// Clean up stale orders_override.json so real database state is never shadowed
$ovFile = __DIR__ . '/orders_override.json';
if (is_file($ovFile)) {
    @unlink($ovFile);
}

// ── 6. SYNC PROVIDER BALANCE ──
$balRes = la_jap_api_call($provider['api_url'], [
    'key' => $provider['api_key'],
    'action' => 'balance',
]);
if (!empty($balRes['balance'])) {
    $curBal = (string)$balRes['balance'];
    $curCurr = (string)($balRes['currency'] ?? 'USD');
    $stmtB = $db->prepare("UPDATE providers SET balance = :b, currency = :c WHERE id = :pid");
    $stmtB->bindValue(':b', $curBal, SQLITE3_TEXT);
    $stmtB->bindValue(':c', $curCurr, SQLITE3_TEXT);
    $stmtB->bindValue(':pid', (int)$provider['id'], SQLITE3_INTEGER);
    $stmtB->execute();
    $results['provider_balance'] = $curBal . ' ' . $curCurr;
}

// ── 7. RECORD CRON EXECUTION LOG IN DATABASE ──
try {
    $stmtCLog = $db->prepare("INSERT INTO cron_logs (job, detail, created_at) VALUES ('orders_sync', :detail, :dt)");
    $detailStr = sprintf("sent=%d synced=%d failed=%d balance=%s trigger=%s",
        $results['orders_sent'],
        $results['orders_synced'],
        $results['orders_failed'],
        $results['provider_balance'] ?? '-',
        (PHP_SAPI === 'cli') ? 'directadmin_cli' : 'webhook'
    );
    $stmtCLog->bindValue(':detail', $detailStr, SQLITE3_TEXT);
    $stmtCLog->bindValue(':dt', date('Y-m-d H:i'), SQLITE3_TEXT);
    $stmtCLog->execute();
} catch (\Throwable $e) {}

$db->close();

// Sync database changes to replica
la_sync_db_copies($activeDbFile, $dbFiles);

// ── 7. UPDATE CRON STATE FILE ──
$stateFile = __DIR__ . '/cron_state.json';
$cronState = [
    'last_run' => time(),
    'last_run_fmt' => date('Y-m-d H:i:s'),
    'status' => 'success',
    'orders_sent' => $results['orders_sent'],
    'orders_synced' => $results['orders_synced'],
    'trigger' => (PHP_SAPI === 'cli') ? 'directadmin_cli' : 'webhook',
];
@file_put_contents($stateFile, json_encode($cronState, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE));

// ── 8. PING RENDER IN BACKGROUND (WARM-UP) ──
$chPing = curl_init('https://likes-auto.onrender.com/ping.php');
curl_setopt_array($chPing, [
    CURLOPT_RETURNTRANSFER => true,
    CURLOPT_TIMEOUT_MS => 1000,
    CURLOPT_NOSIGNAL => 1,
    CURLOPT_SSL_VERIFYPEER => false,
]);
@curl_exec($chPing);
@curl_close($chPing);

header('Content-Type: application/json; charset=utf-8');
echo json_encode($results, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE);
