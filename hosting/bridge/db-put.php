<?php
/**
 * Accept a SQLite backup upload from the Render app and store it as the
 * official restore file for the next Free-plan redeploy.
 *
 * Auth: header X-LA-DB-TOKEN must match token in la-config.php
 *
 * Hard rule: NEVER overwrite with fewer clients / paid / providers / linked services.
 * Intentional shrink only with X-LA-DB-ALLOW_THINNER=1 + reason admin|force.
 * Shutdown / FORCE alone cannot wipe customers or the SMM catalog.
 */
declare(strict_types=1);

$config = require __DIR__ . '/la-config.php';
$token = (string) ($config['db_backup_token'] ?? '');
$got = (string) ($_SERVER['HTTP_X_LA_DB_TOKEN'] ?? '');
if ($token === '' || !hash_equals($token, $got)) {
    http_response_code(401);
    header('Content-Type: application/json; charset=utf-8');
    echo json_encode(['ok' => false, 'error' => 'unauthorized']);
    exit;
}

$raw = file_get_contents('php://input');
if ($raw === false || strlen($raw) < 1024) {
    http_response_code(400);
    header('Content-Type: application/json; charset=utf-8');
    echo json_encode(['ok' => false, 'error' => 'empty_body']);
    exit;
}
if (strncmp($raw, 'SQLite format 3', 15) !== 0) {
    http_response_code(400);
    header('Content-Type: application/json; charset=utf-8');
    echo json_encode(['ok' => false, 'error' => 'not_sqlite']);
    exit;
}

/**
 * @return array{clients:int,paid:int,balance:float,providers:int,services:int,catalog:int}
 */
function la_sqlite_fingerprint(string $path): array
{
    $out = [
        'clients' => -1,
        'paid' => -1,
        'balance' => -1.0,
        'providers' => -1,
        'services' => -1,
        'catalog' => -1,
    ];
    if (!is_file($path)) {
        return $out;
    }
    $probe = sys_get_temp_dir() . '/la-db-probe-' . getmypid() . '-' . bin2hex(random_bytes(4)) . '.db';
    if (!@copy($path, $probe)) {
        return $out;
    }
    try {
        $run = static function ($db) use (&$out): void {
            if (is_object($db) && $db instanceof SQLite3) {
                $c = $db->querySingle('SELECT COUNT(*) FROM clients');
                $p = $db->querySingle("SELECT COUNT(*) FROM payments WHERE status='paid'");
                $b = $db->querySingle('SELECT COALESCE(SUM(balance),0) FROM clients');
                $prov = @$db->querySingle('SELECT COUNT(*) FROM providers');
                $svc = @$db->querySingle('SELECT COUNT(*) FROM services WHERE provider_id IS NOT NULL');
                $cat = @$db->querySingle('SELECT COUNT(*) FROM provider_catalog');
                if (is_numeric($c)) {
                    $out['clients'] = (int) $c;
                }
                if (is_numeric($p)) {
                    $out['paid'] = (int) $p;
                }
                if (is_numeric($b)) {
                    $out['balance'] = (float) $b;
                }
                if (is_numeric($prov)) {
                    $out['providers'] = (int) $prov;
                }
                if (is_numeric($svc)) {
                    $out['services'] = (int) $svc;
                }
                if (is_numeric($cat)) {
                    $out['catalog'] = (int) $cat;
                }
                return;
            }
            if (is_object($db) && $db instanceof PDO) {
                $out['clients'] = (int) $db->query('SELECT COUNT(*) FROM clients')->fetchColumn();
                $out['paid'] = (int) $db->query("SELECT COUNT(*) FROM payments WHERE status='paid'")->fetchColumn();
                $out['balance'] = (float) $db->query('SELECT COALESCE(SUM(balance),0) FROM clients')->fetchColumn();
                try {
                    $out['providers'] = (int) $db->query('SELECT COUNT(*) FROM providers')->fetchColumn();
                } catch (Throwable $e) {
                    $out['providers'] = -1;
                }
                try {
                    $out['services'] = (int) $db->query(
                        'SELECT COUNT(*) FROM services WHERE provider_id IS NOT NULL'
                    )->fetchColumn();
                } catch (Throwable $e) {
                    $out['services'] = -1;
                }
                try {
                    $out['catalog'] = (int) $db->query('SELECT COUNT(*) FROM provider_catalog')->fetchColumn();
                } catch (Throwable $e) {
                    $out['catalog'] = -1;
                }
            }
        };
        if (class_exists('SQLite3')) {
            try {
                $db = new SQLite3($probe, SQLITE3_OPEN_READONLY);
                $run($db);
                $db->close();
                if ($out['clients'] >= 0) {
                    return $out;
                }
            } catch (Throwable $e) {
                // fall through
            }
        }
        if (class_exists('PDO')) {
            try {
                $pdo = new PDO('sqlite:' . $probe, null, null, [
                    PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
                ]);
                $run($pdo);
                $pdo = null;
            } catch (Throwable $e) {
                // keep defaults
            }
        }
        return $out;
    } finally {
        @unlink($probe);
        @unlink($probe . '-wal');
        @unlink($probe . '-shm');
    }
}

$name = (string) ($config['db_restore_name'] ?? '.la-db-restore-d1qyg5az73cs4unx8jl9trbw.db');
$path = __DIR__ . '/' . $name;
$tmp = $path . '.incoming-' . getmypid() . '-' . bin2hex(random_bytes(4));
if (file_put_contents($tmp, $raw) === false) {
    http_response_code(500);
    header('Content-Type: application/json; charset=utf-8');
    echo json_encode(['ok' => false, 'error' => 'write_failed']);
    exit;
}

$reason = strtolower(trim((string) ($_SERVER['HTTP_X_LA_DB_REASON'] ?? '')));
$allowThinner = ((string) ($_SERVER['HTTP_X_LA_DB_ALLOW_THINNER'] ?? '') === '1')
    && in_array($reason, ['admin', 'force'], true);

$incoming = la_sqlite_fingerprint($tmp);
$existing = is_file($path)
    ? la_sqlite_fingerprint($path)
    : [
        'clients' => -1,
        'paid' => -1,
        'balance' => -1.0,
        'providers' => -1,
        'services' => -1,
        'catalog' => -1,
    ];
$existingBytes = is_file($path) ? (int) filesize($path) : 0;
$incomingBytes = strlen($raw);

$reject = null;
if ($incoming['clients'] < 0) {
    $reject = 'incoming_unreadable';
} elseif (!$allowThinner && $existing['clients'] >= 0 && $incoming['clients'] < $existing['clients']) {
    $reject = 'thinner_than_existing';
} elseif (
    !$allowThinner
    && $existing['clients'] >= 0
    && $incoming['clients'] === $existing['clients']
    && $existing['paid'] >= 0
    && $incoming['paid'] >= 0
    && $incoming['paid'] < $existing['paid']
) {
    $reject = 'fewer_paid_payments';
} elseif (
    !$allowThinner
    && ($existing['providers'] ?? -1) >= 0
    && ($incoming['providers'] ?? -1) >= 0
    && $incoming['providers'] < $existing['providers']
) {
    $reject = 'fewer_providers';
} elseif (
    !$allowThinner
    && ($existing['services'] ?? -1) >= 0
    && ($incoming['services'] ?? -1) >= 0
    && $incoming['services'] < $existing['services']
) {
    $reject = 'fewer_linked_services';
} elseif (
    !$allowThinner
    && ($existing['catalog'] ?? -1) >= 0
    && ($incoming['catalog'] ?? -1) >= 0
    && $incoming['catalog'] < $existing['catalog']
) {
    $reject = 'fewer_catalog_rows';
} elseif (!$allowThinner && $existing['clients'] < 0 && $existingBytes > 0 && $incomingBytes + 4096 < $existingBytes) {
    $reject = 'smaller_than_existing_unreadable';
} elseif (!$allowThinner && $existingBytes > 0 && $incoming['clients'] === 0 && $existingBytes >= 100000) {
    $reject = 'zero_clients_overwrite';
}

if ($reject !== null) {
    @unlink($tmp);
    http_response_code(409);
    header('Content-Type: application/json; charset=utf-8');
    echo json_encode([
        'ok' => false,
        'error' => $reject,
        'incoming' => $incoming,
        'existing' => $existing,
        'incoming_bytes' => $incomingBytes,
        'existing_bytes' => $existingBytes,
        'reason' => $reason,
    ], JSON_UNESCAPED_UNICODE);
    exit;
}

if (!rename($tmp, $path)) {
    @unlink($tmp);
    http_response_code(500);
    header('Content-Type: application/json; charset=utf-8');
    echo json_encode(['ok' => false, 'error' => 'rename_failed']);
    exit;
}
@chmod($path, 0644);

$alias = __DIR__ . '/.la-db-restore-latest.db';
@copy($path, $alias);
@chmod($alias, 0644);

$histDir = __DIR__ . '/.la-db-history';
if (!is_dir($histDir)) {
    @mkdir($histDir, 0755, true);
}
$stamp = gmdate('Ymd-His');
$hist = $histDir . '/app-' . $stamp . '.db';
@copy($path, $hist);
@chmod($hist, 0644);
$files = glob($histDir . '/app-*.db') ?: [];
rsort($files);
// Keep more history so a bad push can be recovered manually.
foreach (array_slice($files, 30) as $old) {
    @unlink($old);
}

http_response_code(200);
header('Content-Type: application/json; charset=utf-8');
header('Cache-Control: no-store');
echo json_encode([
    'ok' => true,
    'bytes' => $incomingBytes,
    'file' => $name,
    'alias' => '.la-db-restore-latest.db',
    'history' => basename($hist),
    'reason' => $reason,
    'clients' => $incoming['clients'],
    'paid' => $incoming['paid'],
], JSON_UNESCAPED_UNICODE);
