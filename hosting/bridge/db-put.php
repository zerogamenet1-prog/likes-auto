<?php
/**
 * Accept a SQLite backup upload from the Render app and store it as the
 * official restore file for the next Free-plan redeploy.
 *
 * Also keeps a short rolling history under .la-db-history/ so a bad overwrite
 * does not destroy the only copy.
 *
 * Auth: header X-LA-DB-TOKEN must match token in la-config.php
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

$name = (string) ($config['db_restore_name'] ?? '.la-db-restore-d1qyg5az73cs4unx8jl9trbw.db');
$path = __DIR__ . '/' . $name;
$tmp = $path . '.tmp';
if (file_put_contents($tmp, $raw) === false) {
    http_response_code(500);
    header('Content-Type: application/json; charset=utf-8');
    echo json_encode(['ok' => false, 'error' => 'write_failed']);
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

$reason = (string) ($_SERVER['HTTP_X_LA_DB_REASON'] ?? '');
http_response_code(200);
header('Content-Type: application/json; charset=utf-8');
echo json_encode([
    'ok' => true,
    'bytes' => strlen($raw),
    'file' => $name,
    'alias' => '.la-db-restore-latest.db',
    'history' => basename($hist),
    'reason' => $reason,
], JSON_UNESCAPED_UNICODE);
