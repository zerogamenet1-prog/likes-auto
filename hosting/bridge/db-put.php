<?php
/**
 * Accept a SQLite backup upload from the Render app and store it as the
 * official restore file for the next Free-plan redeploy.
 *
 * Also keeps a short rolling history under .la-db-history/ so a bad overwrite
 * does not destroy the only copy.
 *
 * Auth: header X-LA-DB-TOKEN must match token in la-config.php
 *
 * Safety: rejects "thinner" uploads (fewer clients) unless reason is
 * admin / shutdown / force — stops a Render Free seed DB from wiping customers.
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
 * @return int client count, or -1 if unreadable
 */
function la_sqlite_client_count(string $path): int
{
    if (!is_file($path) || !class_exists('SQLite3')) {
        return -1;
    }
    try {
        $db = new SQLite3($path, SQLITE3_OPEN_READONLY);
        $row = $db->querySingle('SELECT COUNT(*) FROM clients');
        $db->close();
        return is_numeric($row) ? (int) $row : -1;
    } catch (Throwable $e) {
        return -1;
    }
}

$name = (string) ($config['db_restore_name'] ?? '.la-db-restore-d1qyg5az73cs4unx8jl9trbw.db');
$path = __DIR__ . '/' . $name;
$tmp = $path . '.tmp';
if (file_put_contents($tmp, $raw) === false) {
    http_response_code(500);
    header('Content-Type: application/json; charset=utf-8');
    echo json_encode(['ok' => false, 'error' => 'write_failed']);
    exit;
}

$reason = strtolower(trim((string) ($_SERVER['HTTP_X_LA_DB_REASON'] ?? '')));
$force = in_array($reason, ['admin', 'shutdown', 'force', 'flush', 'live_eax999_restored', 'restore_eax999_guard'], true)
    || (string) ($_SERVER['HTTP_X_LA_DB_FORCE'] ?? '') === '1';

$incoming = la_sqlite_client_count($tmp);
$existing = is_file($path) ? la_sqlite_client_count($path) : -1;
if (!$force && $incoming >= 0 && $existing >= 0 && $incoming < $existing) {
    @unlink($tmp);
    http_response_code(409);
    header('Content-Type: application/json; charset=utf-8');
    echo json_encode([
        'ok' => false,
        'error' => 'thinner_than_existing',
        'incoming_clients' => $incoming,
        'existing_clients' => $existing,
        'reason' => $reason,
    ], JSON_UNESCAPED_UNICODE);
    exit;
}

rename($tmp, $path);
@chmod($path, 0644);

// Keep a second alias so boot restore has a fallback URL.
$alias = __DIR__ . '/.la-db-restore-latest.db';
@copy($path, $alias);
@chmod($alias, 0644);

// Rolling history (keep last 12 snapshots).
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
    'bytes' => strlen($raw),
    'file' => $name,
    'alias' => '.la-db-restore-latest.db',
    'history' => basename($hist),
    'reason' => $reason,
    'clients' => $incoming,
], JSON_UNESCAPED_UNICODE);
