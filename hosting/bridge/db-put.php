<?php
/**
 * Accept a SQLite backup upload from the Render app and store it as the
 * official restore file for the next Free-plan redeploy.
 *
 * Auth: header X-LA-DB-TOKEN must match token in la-config.php
 *
 * Safety: rejects thinner uploads (fewer clients / smaller than current)
 * unless X-LA-DB-FORCE=1 or reason is admin/shutdown/force.
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
 * Count clients without creating -wal/-shm beside the restore file.
 *
 * @return int client count, or -1 if unreadable
 */
function la_sqlite_client_count(string $path): int
{
    if (!is_file($path)) {
        return -1;
    }
    // Copy to a private temp so SQLite never touches the published restore path.
    $probe = sys_get_temp_dir() . '/la-db-probe-' . getmypid() . '-' . bin2hex(random_bytes(4)) . '.db';
    if (!@copy($path, $probe)) {
        return -1;
    }
    try {
        if (class_exists('SQLite3')) {
            try {
                $db = new SQLite3($probe, SQLITE3_OPEN_READONLY);
                $row = $db->querySingle('SELECT COUNT(*) FROM clients');
                $db->close();
                if (is_numeric($row)) {
                    return (int) $row;
                }
            } catch (Throwable $e) {
                // fall through to PDO
            }
        }
        if (class_exists('PDO')) {
            try {
                $pdo = new PDO('sqlite:' . $probe, null, null, [
                    PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
                ]);
                $n = (int) $pdo->query('SELECT COUNT(*) FROM clients')->fetchColumn();
                $pdo = null;
                return $n;
            } catch (Throwable $e) {
                return -1;
            }
        }
        return -1;
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
// Intentional wipe only via explicit admin allow-thinner header (never from Render shutdown).
$allowThinner = ((string) ($_SERVER['HTTP_X_LA_DB_ALLOW_THINNER'] ?? '') === '1')
    && in_array($reason, ['admin', 'force'], true);

$incoming = la_sqlite_client_count($tmp);
$existing = is_file($path) ? la_sqlite_client_count($path) : -1;
$existingBytes = is_file($path) ? (int) filesize($path) : 0;
$incomingBytes = strlen($raw);

$reject = null;
if ($incoming < 0) {
    $reject = 'incoming_unreadable';
} elseif (!$allowThinner && $existing >= 0 && $incoming < $existing) {
    // Absolute rule: never drop customers, even if caller sends FORCE/shutdown.
    $reject = 'thinner_than_existing';
} elseif (!$allowThinner && $existing < 0 && $existingBytes > 0 && $incomingBytes + 4096 < $existingBytes) {
    $reject = 'smaller_than_existing_unreadable';
} elseif (!$allowThinner && $existingBytes > 0 && $incoming === 0 && $existingBytes >= 100000) {
    $reject = 'zero_clients_overwrite';
}

if ($reject !== null) {
    @unlink($tmp);
    http_response_code(409);
    header('Content-Type: application/json; charset=utf-8');
    echo json_encode([
        'ok' => false,
        'error' => $reject,
        'incoming_clients' => $incoming,
        'existing_clients' => $existing,
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
foreach (array_slice($files, 12) as $old) {
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
    'clients' => $incoming,
], JSON_UNESCAPED_UNICODE);
